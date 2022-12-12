import asyncio
import pickle
from datetime import datetime

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from pip._internal import commands

from lib.config_file_actions import set_apikey, get_apikey
from sqlite import db_start, db_create_user, db_user_edit, db_user_exist, db_user_get_info, db_user_edit_info,db_get_all_info

with open('database/config.pickle', 'rb') as f:
    config_info = pickle.load(f)
bot = Bot(token=config_info['token'])
global api_key
api_key = config_info['api_key']

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def on_startup(_):
    await db_start()


class ProfileStatesGroup(StatesGroup):
    user_SummonerName = State()
    user_Server = State()
    user_approve = State()


class ApiStatesGroup(StatesGroup):
    input_api = State()
class WatcherStatesGroup(StatesGroup):
    input_watcher = State()

def get_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton('/create'))
    return kb


def get_cancel_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton('/cancel'))
    return kb


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await message.delete()
    await message.answer(f'Чтобы создать профиль отправьте /create', reply_markup=get_kb())
    await db_create_user(message.from_user.id)


@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return
    await state.finish()
    await message.delete()
    await message.answer('Вы прервали создание профиля, чтобы начать заново введите /create', reply_markup=get_kb())


@dp.message_handler(commands=['create'])
async def cmd_create(message: types.Message):
    await message.delete()
    if await db_user_exist(message.from_user.id):
        await db_create_user(message.from_user.id)
        await message.answer(f'Отправь мне твое имя призывателя!', reply_markup=get_cancel_kb())
        await ProfileStatesGroup.user_SummonerName.set()
    else:
        await message.answer(f'Мы помним Вас, введите /profile', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.user_SummonerName)
async def input_summonername(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        data['summoner_name'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("RU", "EU", "NA", "/cancel")
    await message.answer('Теперь выбери сервер на котором играешь!', reply_markup=markup)
    await ProfileStatesGroup.next()


@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.user_Server)
async def input_summonername(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['user_server'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Да", "Нет", "/cancel")
    try:
        user_lol_info = requests.get(
            f"https://{str(data['user_server']).lower()}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{data['summoner_name']}",
            params={"api_key": get_apikey()}).json()
        await message.answer(
            f'<b>Это вы?</b>\n<b>Имя призывателя:</b> {user_lol_info["name"]}\n<b>Уровень:</b> {user_lol_info["summonerLevel"]} <a href="http://ddragon.leagueoflegends.com/cdn/12.22.1/img/profileicon/{user_lol_info["profileIconId"]}.png">&#8205</a>',
            parse_mode='HTML', disable_web_page_preview=False, reply_markup=markup)
        await message.delete()
        await ProfileStatesGroup.next()
    except:
        await message.reply(f'Oooops!! Что-то пошло не так, снова отправьте /create \nПеред этим проверьте правильность выбора сервера и имя призывателя', reply_markup=get_kb())
        await state.finish()


@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.user_approve)
async def input_summonername(message: types.Message, state: FSMContext):
    await message.delete()
    if message.text == 'Да':
        await message.answer(f'Спасибо, профиль успешно создан', reply_markup=types.ReplyKeyboardRemove())
        await db_user_edit(state, message.from_user.id)
        await state.finish()
    if message.text == 'Нет':
        await message.answer(f'Отправьте /create и попробуйте снова. Еще раз проверьте имя призывателя и сервер',
                             reply_markup=get_kb())
        await state.finish()


@dp.message_handler(commands='setapi')
async def set_api_case(message: types.Message):
    await message.delete()
    await message.answer(f'Отправь мне новый API', reply_markup=get_cancel_kb())
    await ApiStatesGroup.input_api.set()

    @dp.message_handler(state=ApiStatesGroup.input_api)
    async def set_api(message: types.Message, state: FSMContext):
        set_apikey(message.text)
        await bot.send_message(message.chat.id,
                               f'Ваш новый APIKEY: {message.text}\n сделайте /refreshapi , чтобы обновить',
                               reply_markup=types.ReplyKeyboardRemove())
        await state.finish()


@dp.message_handler(commands='printapi')
async def print_api(message: types.Message):
    await bot.send_message(message.chat.id, api_key)


@dp.message_handler(commands='refreshapi')
async def refresh_api(message: types.Message):
    global api_key
    api_key = get_apikey()
    await message.reply(f'Ваш APIKEY обновлен')


@dp.message_handler(commands='profile')
async def show_profile(message: types.Message):
    await message.delete()
    await message.answer(f'Приветствую тебя, <b>@{message.from_user.username}</b> !!\n'
                         f'Имя призывателя: <b>{await db_user_get_info(message.from_user.id, "summoner_name")}</b>\n'
                         f'Сервер: <b>{await db_user_get_info(message.from_user.id, "summoner_server")}</b>\n'
                         f'Уровень: <b>{await db_user_get_info(message.from_user.id, "summoner_level")}</b>\n'
                         f'Наблюдаете за: <b>{await db_user_get_info(message.from_user.id, "watching_for_summonername")}</b>\n'
                         f'Состояние уведомлений: <b>{"Включены" if await db_user_get_info(message.from_user.id, "is_watching")=="True" else "Отключены"}</b>\n'
                         f'<a href="http://ddragon.leagueoflegends.com/cdn/12.22.1/img/profileicon/{await db_user_get_info(message.from_user.id, "profileiconid")}.png">&#8205</a>',
                         parse_mode='HTML', disable_web_page_preview=False
                         )


@dp.message_handler(commands='watch')
async def start_watching(message: types.Message):
    if await db_user_exist(message.from_user.id):
        await message.answer(f'Перед тем как начать получать уведомления, пройдите регистрацию /create ')
    else:
        if await db_user_get_info(message.from_user.id,'is_watching')=='1':
            await message.answer(f'Уведомления уже подключены. Проявите терпения, <b>{await db_user_get_info(message.from_user.id,"watching_for_summonername")}</b> еще не был онлайн', parse_mode="HTML")
        else:
            await db_user_edit_info(message.from_user.id, 'is_watching', True)
            await message.answer(f'Уведомления включены. Вы получите уведомление, когда пользователь <b>{await db_user_get_info(message.from_user.id,"watching_for_summonername")}</b> будет в сети', parse_mode='HTML')
        print(requests.get(
            f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{await db_user_get_info(message.from_user.id, "watching_for")}',
            params={
                "api_key": api_key}).status_code)
        while await db_user_get_info(message.from_user.id,'is_watching')=='True':
            if requests.get(
                            f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{await db_user_get_info(message.from_user.id,"watching_for")}',
                            params={
                                "api_key": api_key}).status_code == 200:
                await message.reply(f'Пользователь с ником <b>{await db_user_get_info(message.from_user.id,"watching_for_summonername")}</b> ОН-ЛА-ЙН!\nВремя: <b>{datetime.now().strftime("%D-%H:%M")}</b>\n'
                                    f'Уведомления отключены до следующей команды /watch', parse_mode='HTML')
                await db_user_edit_info(message.from_user.id, 'is_watching', False)
            else:
                await asyncio.sleep(120)

@dp.message_handler(commands='stopwatch')
async def stop_watching(message: types.Message):
    await db_user_edit_info(message.from_user.id, 'is_watching', False)
    await message.reply(f'Уведомления отключены. Отправьте /watch ,  чтобы начать снова получать уведомления')

@dp.message_handler(commands='set')
async def set_watcher(message: types.Message):
    await message.reply(f'Пришлите мне имя призывателя, за которым хотите следить', reply_markup=get_cancel_kb())
    await WatcherStatesGroup.input_watcher.set()
    @dp.message_handler(state=WatcherStatesGroup.input_watcher)
    async def input_watcher(message: types.Message, state: FSMContext):
        await db_user_edit_info(message.from_user.id,"watching_for_summonername",message.text)
        await message.reply(f'Теперь вы следите за пользователем {message.text}\nОтправьте /profile, чтобы убедиться', reply_markup=types.ReplyKeyboardRemove())
        await state.finish()

@dp.message_handler(commands='getdb')
async def get_db(message: types.Message):
    await message.reply(await db_get_all_info())



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
