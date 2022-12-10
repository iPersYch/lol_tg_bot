import sqlite3 as sq

import requests

from lib.config_file_actions import get_apikey


async def db_start():
    global db, cur
    db = sq.connect('database/users_info.db')
    cur = db.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users_info(id INTEGER PRIMARY KEY AUTOINCREMENT,tg_ID TEXT,summoner_name '
                'TEXT,summoner_server TEXT,lol_id TEXT,accountid TEXT,puuid TEXT, '
                'summoner_level TEXT,profileiconid TEXT,watching_for TEXT,watching_for_summonername TEXT,is_watching '
                'TEXT)')

    db.commit()

async def db_create_user(tg_ID):
    print(tg_ID)
    user = cur.execute(f'SELECT 1 FROM users_info WHERE "tg_ID"=="{tg_ID}"').fetchone()
    print(f'{user=}')
    if not user:
        cur.execute(f'INSERT INTO users_info("tg_ID") VALUES ({tg_ID})')
        db.commit()

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


async def db_users_exist(tg_ID):
    user_exist= cur.execute(f'SELECT summoner_name FROM users_info WHERE "tg_ID"="{tg_ID}"').fetchone()
    print(f"{user_exist=}")
    print(f'{None in user_exist=}')

    if None in user_exist:
        return True
    else:
        return False

if __name__ == '__main__':
    db_start()
    print(db_users_exist('5766429577'))





