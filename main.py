import pickle
from time import sleep
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from lib.config_file_actions import set_apikey, refresh_apikey
import requests

with open('database/config.pickle', 'rb') as f:
    config_info = pickle.load(f)
bot = Bot(token=config_info['token'])
api_key = config_info['api_key']

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    user_SummonerName = State()
    user_Server = State()
    user_apikey = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
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
            """
            Process user name
            """
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

            async with state.proxy() as data:
                response = requests.get(
                    f"https://ru.api.riotgames.com/lol/summoner/v4/summoners/by-name/{data['user_SummonerName']}",
                    params={"api_key": api_key})
                users_info[message.from_user.id] = {"id": response.json()['id'],
                                                    "accountId": response.json()['accountId'],
                                                    'name': response.json()['name'],
                                                    "summonerLevel": response.json()['summonerLevel'],
                                                    'Server': f'{data["user_Server"]}',
                                                    'puuid': response.json()['accountId'],
                                                    "profileIconId": response.json()['profileIconId']}
                with open('database/users_info.pickle', 'wb') as f:
                    pickle.dump(users_info, f)
                await bot.send_message(message.chat.id,
                                       'Теперь вы в нашей Базе Данных, введите /start ,\nчтобы убедиться',
                                       reply_markup=markup)

                await state.finish()
    else:
        if requests.get(f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{users_info[message.from_user.id]["id"]}', params=api_key).status_code == 200:
            is_online= True
        else:
            is_online= False
        await bot.send_message(message.chat.id,
                               f'Добро пожаловать призыватель, Мы Вас помним!\nВаше Имя призывателя: {users_info[message.from_user.id]["name"]}\nСейчас в игре: {"Да" if is_online else "Нет"}\nСервер: {users_info[message.from_user.id]["Server"]}\nУровень призывателя: {users_info[message.from_user.id]["summonerLevel"]}\nВаш ID призывателя: {users_info[message.from_user.id]["id"]}'
                               f'<a href="http://ddragon.leagueoflegends.com/cdn/12.22.1/img/profileicon/{users_info[message.from_user.id]["profileIconId"]}.png">&#8205</a>',
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
    api_key = refresh_apikey()
    await message.reply(f'Ваш APIKEY обновлен')


    # while True:
    #     sleep(900)
    #     response1 = requests.get(f"https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/pSUEMC0Samkn_nZIiO1BD9xIsLEcHFLTrsDBevLnfG6XaD4",params={"api_key":api_key})
    #     if response1.status_code == 200:
    #         await bot.send_message(message.chat.id, "ALARM!! СЕРЕЖА В ИГРЕ")

    # with open('database/phrase_dict.pickle', 'rb') as f:
    #     phrase_dict = pickle.load(f)
    # with open('database/phrase_dict.pickle', 'wb') as f:
    #     pickle.dump(phrase_dict, f)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
