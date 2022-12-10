import pickle

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

from lib.config_file_actions import set_apikey, get_apikey
from sqlite import db_start, db_create_user, db_user_edit, db_users_exist

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
    await message.answer(f'Чтобы создать профиль отправьте /create', reply_markup=get_kb())
    await db_create_user(message.from_user.id)


@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return
    await state.finish()
    await message.reply('Вы прервали создание профиля, чтобы начать заново введите /create', reply_markup=get_kb())


@dp.message_handler(commands=['create'])
async def cmd_create(message: types.Message):
    if await db_users_exist(message.from_user.id):
        await db_create_user(message.from_user.id)
        await message.reply(f'Отправь мне твое имя призывателя!', reply_markup=get_cancel_kb())
        await ProfileStatesGroup.user_SummonerName.set()
    else:
        await message.reply(f'Мы помним Вас, введите /profile', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.user_SummonerName)
async def input_summonername(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['summoner_name'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("RU", "EU", "NA", "/cancel")
    await message.reply('Теперь выбери сервер на котором играешь!', reply_markup=markup)
    await ProfileStatesGroup.next()


@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.user_Server)
async def input_summonername(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_server'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Да", "Нет", "/cancel")
    user_lol_info = requests.get(
        f"https://{str(data['user_server']).lower()}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{data['summoner_name']}",
        params={"api_key": get_apikey()}).json()
    await message.reply(
        f'<b>Это вы?</b>\n<b>Имя призывателя:</b> {user_lol_info["name"]}\n<b>Уровень:</b> {user_lol_info["summonerLevel"]} <a href="http://ddragon.leagueoflegends.com/cdn/12.22.1/img/profileicon/{user_lol_info["profileIconId"]}.png">&#8205</a>',
        parse_mode='HTML', disable_web_page_preview=False, reply_markup=markup)
    await ProfileStatesGroup.next()


@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.user_approve)
async def input_summonername(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await message.reply(f'Спасибо, профиль успешно создан', reply_markup=types.ReplyKeyboardRemove())
        await db_user_edit(state, message.from_user.id)
        await state.finish()
    if message.text == 'Нет':
        await message.reply(f'Отправьте /create и попробуйте снова. Еще раз проверьте имя призывателя и сервер',
                            reply_markup=get_kb())
        await state.finish()


@dp.message_handler(commands='setapi')
async def set_api_case(message: types.Message):
    await message.reply(f'Отправь мне новый API', reply_markup=get_cancel_kb())
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
async def refresh(message: types.Message):
    global api_key
    api_key = get_apikey()
    await message.reply(f'Ваш APIKEY обновлен')


#
#
# @dp.message_handler(commands='startwatching')
# async def start_watching(message: types.Message):
#     with open('database/users_info.pickle', 'rb') as f:
#         users_info = pickle.load(f)
#         users_info[message.from_user.id]["is_watching"] = True
#     with open('database/users_info.pickle', 'wb') as f:
#         pickle.dump(users_info, f)
#
#     if message.chat.id not in users_info.keys():
#         await message.reply(f'Вас нет в нашей базе данных, пройдите регистрацию через /start')
#     else:
#         if requests.get(
#                 f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{users_info[message.from_user.id]["watching_for"]}',
#                 params={
#                     "api_key": api_key}).status_code == 200:
#             await bot.send_message(message.chat.id,
#                                    f'Игрок {users_info[message.from_user.id]["watching_for_summonername"]} сейчас в сети,\n(сюда воткнуть инфу по матчу).')
#         else:
#             await bot.send_message(message.chat.id,
#                                    f'Игрок {users_info[message.from_user.id]["watching_for_summonername"]} сейчас не сети, но не переживайте мы сообщим вам, как только он будет онлайн.')
#             while users_info[message.from_user.id]["is_watching"] == True:
#                 if requests.get(
#                         f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{users_info[message.from_user.id]["watching_for"]}',
#                         params={
#                             "api_key": api_key}).status_code == 200:
#                     await bot.send_message(message.from_user.id,
#                                            f'{users_info[message.from_user.id]["watching_for_summonername"]} онлайн! Повторяю {users_info[message.from_user.id]["watching_for_summonername"]} ОН-ЛА-ЙН\n(сюда добавить информацию по игре)')
#                     users_info[message.from_user.id]["is_watching"] = False
#                     with open('database/users_info.pickle', 'wb') as f:
#                         pickle.dump(users_info, f)
#
#                     await bot.send_message(message.from_user.id,
#                                            f'Чтобы получить еще одно уведомление напишите /startwatching')
#                 else:
#                     await asyncio.sleep(120)
#
#
# @dp.message_handler(commands='profile')
# async def profile(message: types.Message):
#     profile = Profile(message)
#     await profile.profile_reply(message)
#
#
# @dp.message_handler(commands='setwatcher')
# async def setwatcher(message: types.Message):
#     try:
#         with open('database/users_info.pickle', 'rb') as f:
#             users_info = pickle.load(f)
#     except:
#         users_info = {}
#     users_info[message.from_user.id]["watching_for_summonername"] = message.text.split(' ')[1]
#     new_watcher_ID = requests.get(
#         f"https://{users_info[message.from_user.id]['summoner_server']}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{message.text.split(' ')[1]}",
#         params={"api_key": get_apikey()}).json()["id"]
#     users_info[message.from_user.id]["watching_for"] = new_watcher_ID
#     with open('database/users_info.pickle', 'wb') as f:
#         pickle.dump(users_info, f)
#     await message.reply(f'Теперь вы следите за игроком {users_info[message.from_user.id]["watching_for_summonername"]}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
