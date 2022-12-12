import sqlite3 as sq
from time import strftime

import requests

from lib.config_file_actions import get_apikey


async def db_start():
    global db, cur
    try:
        db = sq.connect('database/users_info.db')
        cur = db.cursor()

        cur.execute('CREATE TABLE IF NOT EXISTS users_info(id INTEGER PRIMARY KEY AUTOINCREMENT,tg_ID TEXT,summoner_name '
                    'TEXT,summoner_server TEXT,lol_id TEXT,accountid TEXT,puuid TEXT, '
                    'summoner_level TEXT,profileiconid TEXT,watching_for TEXT,watching_for_summonername TEXT,is_watching '
                    'TEXT)')
        db.commit()
        print(f'Соединение с базой данных успешно установлено\n')
    except Exception as e:
        print(f'Не удалось установить соединение с базой данных\n'
              f'Причина: {e}')


async def db_create_user(tg_ID):
    print(f'Попытка создания пользователя с TelegramID: {tg_ID}')
    user = cur.execute(f'SELECT 1 FROM users_info WHERE "tg_ID"=="{tg_ID}"').fetchone()
    if not user:
        print(f'Пользователя не было в БД. Создана первичная запись для TelegramID: {tg_ID}')
        cur.execute(f'INSERT INTO users_info("tg_ID") VALUES ({tg_ID})')
        db.commit()
    else:
        print(f'TelegramID уже есть в БД. Нет необходимости создания новой записи')

async def db_user_edit(state, tg_ID):
    async with state.proxy() as data:
        response = requests.get(
            f"https://{str(data['user_server']).lower()}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{data['summoner_name']}",
            params={"api_key": get_apikey()}).json()
        summoner_name=response['name']
        summoner_server=data["user_server"]
        lol_id=response["id"]
        print(f"{lol_id=}")
        accountid=response["accountId"]
        puuid=response["puuid"]
        summoner_level=response["summonerLevel"]
        profileiconid=response["profileIconId"]

        cur.execute(f'UPDATE users_info SET "summoner_name"="{summoner_name}","summoner_server"="{summoner_server}",'
                    f'"lol_id"="{lol_id}","accountid"="{accountid}","puuid"="{puuid}",'
                    f'"summoner_level"="{summoner_level}","profileiconid"="{profileiconid}","watching_for"="OltZbV6ovRsgRu1T0wXxQWVtsDQC7oD72BoaSeLWEIkWQg","watching_for_summonername"="попся","is_watching"=False WHERE "tg_ID"=="{tg_ID}"')
        db.commit()


async def db_user_exist(tg_ID):
    print(f'Начало проверки заполнености профиля пользователя с TelegramID : {tg_ID}')
    user_exist= cur.execute(f'SELECT summoner_name FROM users_info WHERE tg_ID={tg_ID}').fetchone()
    print(f'Профиль пользователя {"не заполнен" if None in user_exist else "заполнен"}')
    if None==user_exist[0]:
        return True
    else:
        return False

async def db_user_get_info(tg_ID, column_name)->str:
    print(f'Начинаем получать данные {column_name} для пользователя {tg_ID} из БД')
    user_info = cur.execute(f'SELECT {column_name} FROM users_info WHERE tg_ID={tg_ID}').fetchone()
    print(f'Данные {column_name} для пользователя {tg_ID} : {user_info[0]}')
    print(f'Возвращаем {user_info[0]}\n {"#"*20}')
    return user_info[0]

async def db_user_edit_info(tg_ID, column_name, new_info):
    print(f'Попытка изменения информации {column_name} пользователя {tg_ID}')
    if type(new_info)==str:
        new_info.replace(' ','')
    cur.execute(f'UPDATE users_info SET "{column_name}" = "{new_info}" WHERE tg_ID={tg_ID}')
    if column_name=="watching_for_summonername":
        response = requests.get(f'https://ru.api.riotgames.com/lol/summoner/v4/summoners/by-name/{new_info}', params={"api_key": get_apikey()})
        print(response.json())
        cur.execute(
            f'UPDATE users_info SET watching_for="{response.json()["id"]}" WHERE tg_ID={tg_ID}').fetchone()
    print(f'Данные пользователя {tg_ID} успешно изменены\n {"#"*20}')
    db.commit()

async def db_get_all_info():
    all_info = cur.execute(f'SELECT * FROM users_info').fetchall()
    return all_info







