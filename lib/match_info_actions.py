from sqlite import db_user_get_info
from lib.config_file_actions import get_apikey
import datetime
import requests
import json


class UserMatch:
    def __init__(self, tg_id):
        self.tg_id = tg_id
        self.match_info= None
        self.championId=None
        self.champion=None
        self.champions_json={}
    async def get_info(self):
        self.match_info = requests.get(
            f'https://ru.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{await db_user_get_info(self.tg_id, "watching_for")}',
            params={"api_key":get_apikey()}).json()
        self.game_mode = self.match_info["gameMode"]
        self.gameStartTime = datetime.datetime.fromtimestamp(self.match_info["gameStartTime"]/1000).strftime("%Y-%m-%d %H:%M:%S")
        self.gameLength= f'{int(self.match_info["gameLength"])//60}m{self.match_info["gameLength"]-60*(self.match_info["gameLength"]//60)}sec'
        for i in self.match_info["participants"]:
            if str(await db_user_get_info(self.tg_id,"watching_for_summonername")) in i.values():
                self.championId=i["championId"]
    async def get_champ(self):
        self.champions_json= requests.get("http://ddragon.leagueoflegends.com/cdn/12.23.1/data/en_US/champion.json").json()
        for i in self.champions_json['data'].keys():
            if self.champions_json['data'][i]['key'] == str(self.championId):
                self.champion=self.champions_json['data'][i]['id']







