from sqlite import db_user_get_info
from lib.config_file_actions import get_apikey
import datetime
import requests


class UserMatch:
    def __init__(self, tg_id):
        self.tg_id = tg_id
        self.match_info= None
    async def get_info(self):
        self.match_info = requests.get(
            f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{await db_user_get_info(self.tg_id, "watching_for")}',
            params={"api_key":get_apikey()}).json()
        print(self.match_info)
        print(type(await db_user_get_info(self.tg_id, "lol_id")))

        self.game_mode = self.match_info["gameMode"]
        print(self.game_mode)
        print(self.match_info["gameStartTime"])
        self.gameStartTime = datetime.datetime.fromtimestamp(self.match_info["gameStartTime"]/1000).strftime("%Y-%m-%d %H:%M:%S")
        self.gameLength= f'{int(self.match_info["gameLength"])//60}m{self.match_info["gameLength"]-60*(self.match_info["gameLength"]//60)}sec'
