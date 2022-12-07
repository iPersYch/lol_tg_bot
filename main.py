import asyncio
import pickle
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from lib.config_file_actions import set_apikey, get_apikey
from lib.users_action import User
import requests

with open('database/config.pickle', 'rb') as f:
    config_info = pickle.load(f)
bot = Bot(token=config_info['token'])
api_key = config_info['api_key']

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    user_SummonerName = State()
    user_Server = State()
    user_approved = State()
    user_apikey = State()




@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    try:
        with open('database/users_info.pickle', 'rb') as f:
            users_info = pickle.load(f)
    except:
        users_info = {}
    if message.from_user.id not in users_info.keys():  # Проверяем есть ли ИД в БД
        await message.reply("Привет, отправь мне свой ник в League of Legends")
        await Form.user_SummonerName.set()

        @dp.message_handler(state='*', commands='cancel')
        @dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
        async def cancel_handler(message: types.Message, state: FSMContext):
            current_state = await state.get_state()
            if current_state is None:
                return
            await state.finish()
            # And remove keyboard (just in case)
            await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())

        @dp.message_handler(state=Form.user_SummonerName)
        async def process_name(message: types.Message, state: FSMContext):

            async with state.proxy() as data:
                data['user_SummonerName'] = message.text

            await Form.next()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add("RU", "EU", "NA")
            await message.reply("What is your server", reply_markup=markup)

        @dp.message_handler(state=Form.user_Server)
        async def process_age(message: types.Message, state: FSMContext):
            # Update state and data
            await state.update_data(user_Server=message.text)
            markup = types.ReplyKeyboardRemove()
            await Form.next()
            async with state.proxy() as data:
                new_user = User(data['user_SummonerName'], data['user_Server'], message.from_user.id)
                await new_user.lolinfo()
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                markup.add("Да", "Нет")
                await message.reply(f"Это вы?\n\n<b>Имя призывателя:</b> {new_user.summoner_name}\n<b>Уровень призывателя:</b> {new_user.summoner_level}\n<a href='http://ddragon.leagueoflegends.com/cdn/12.22.1/img/profileicon/{new_user.profileiconid}.png'>&#8205</a>",
                               parse_mode='HTML', disable_web_page_preview=False, reply_markup=markup)

        @dp.message_handler(state=Form.user_approved)
        async def process_approved(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                new_user = User(data['user_SummonerName'], data['user_Server'], message.from_user.id)
            await new_user.lolinfo()
            if message.text=="Да":
                new_user.approved = True
            if message.text=="Нет":
                new_user.approved = False
            text_from_add=await new_user.add_user()
            await bot.send_message(message.chat.id,text_from_add, reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
    else:
        await bot.send_message(message.chat.id,
                               f'Добро пожаловать призыватель, Мы Вас помним!\nВаше Имя призывателя: {users_info[message.from_user.id]["summoner_name"]}\nСервер: {users_info[message.from_user.id]["summoner_server"]}\nУровень призывателя: {users_info[message.from_user.id]["summoner_level"]}\nВаш ID призывателя: {users_info[message.from_user.id]["lol_id"]}'
                               f'<a href="http://ddragon.leagueoflegends.com/cdn/12.22.1/img/profileicon/{users_info[message.from_user.id]["profileiconid"]}.png">&#8205</a>',
                               parse_mode='HTML', disable_web_page_preview=False)


@dp.message_handler(commands='setapi')
async def set_api_case(message: types.Message):
    await message.reply(f'Отправь мне новый API')
    await Form.user_apikey.set()

    @dp.message_handler(state=Form.user_apikey, )
    async def set_api(message: types.Message, state: FSMContext):
        set_apikey(message.text)
        await bot.send_message(message.chat.id,
                               f'Ваш новый APIKEY: {message.text}\n сделайте /refreshapi , чтобы обновить')
        await state.finish()


@dp.message_handler(commands='printapi')
async def print_api(message: types.Message):
    await bot.send_message(message.chat.id, api_key)


@dp.message_handler(commands='refreshapi')
async def refresh(message: types.Message):
    global api_key
    api_key = get_apikey()
    await message.reply(f'Ваш APIKEY обновлен')


@dp.message_handler(commands='startwatching')
async def start_watching(message: types.Message):
    with open('database/users_info.pickle', 'rb') as f:
        users_info = pickle.load(f)
        users_info[message.from_user.id]["is_watching"] = True
    with open('database/users_info.pickle', 'wb') as f:
        pickle.dump(users_info, f)

    if message.chat.id not in users_info.keys():
        await message.reply(f'Вас нет в нашей базе данных, пройдите регистрацию через /start')
    else:
        if requests.get(
                f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{users_info[message.from_user.id]["watching_for"]}',
                params={
                    "api_key": api_key}).status_code == 200:
            await bot.send_message(message.chat.id,
                                   f'Игрок vex1k сейчас в сети,\n(сюда воткнуть инфу по матчу).')
        else:
            await bot.send_message(message.chat.id,
                                   f'Игрок vex1k сейчас не сети, но не переживайте мы сообщим вам, как только он будет онлайн.')
            while users_info[message.from_user.id]["is_watching"] == True:
                if requests.get(
                        f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{users_info[message.from_user.id]["watching_for"]}',
                        params={
                            "api_key": api_key}).status_code == 200:
                    await bot.send_message(message.from_user.id,
                                           f'Сережа онлайн! Повторяю Сережа ОН-ЛА-ЙН\n(сюда добавить информацию по игре)')
                    users_info[message.from_user.id]["is_watching"] = False
                    await bot.send_message(message.from_user.id,
                                           f'Чтобы получить еще одно уведомление напишите /startwatching')
                else:
                    await asyncio.sleep(120)

@dp.message_handler(commands='profile')
async def profile(message: types.Message):
    with open('database/users_info.pickle', 'rb') as f:
        users_info = pickle.load(f)
    await message.reply(f'{users_info}')




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
