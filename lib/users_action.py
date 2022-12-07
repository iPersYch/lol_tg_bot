import pickle

import requests
from lib.config_file_actions import get_apikey


class User:
    def __init__(self, summoner_name, summoner_server: str, tg_id):
        self.summoner_name = summoner_name
        self.summoner_server = summoner_server
        self.tg_ID = tg_id
        self.lol_id = None
        self.accountid = None
        self.puuid = None
        self.summoner_level = None
        self.profileiconid = None
        self.approved = None
        self.watching_for = "pSUEMC0Samkn_nZIiO1BD9xIsLEcHFLTrsDBevLnfG6XaD4"
        self.is_watching = None

    async def lolinfo(self):
        get_userinfo = requests.get(
            f"https://{self.summoner_server.lower()}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{self.summoner_name}",
            params={"api_key": get_apikey()})
        self.lol_id = get_userinfo.json()['id']
        self.accountid = get_userinfo.json()['accountId']
        self.puuid = get_userinfo.json()['puuid']
        self.summoner_level = get_userinfo.json()['summonerLevel']
        self.profileiconid = get_userinfo.json()['profileIconId']

    async def add_user(self):
        if self.approved:
            try:
                with open('database/users_info.pickle', 'rb') as f:
                    users_info = pickle.load(f)
            except:
                users_info ={}
            users_info[self.tg_ID] = {'summoner_name': self.summoner_name,
                                      'summoner_server': self.summoner_server,
                                      'lol_id': self.lol_id,
                                      'accountid': self.accountid,
                                      'puuid': self.puuid,
                                      'summoner_level': self.summoner_level,
                                      'profileiconid': self.profileiconid,
                                      'watching_for': self.watching_for,
                                      'is_watching': self.is_watching}
            with open('database/users_info.pickle', 'wb') as f:
                pickle.dump(users_info, f)
            return f'Вы были успешно добавлены в нашу БД, чтобы посмотреть информацию о своем профиле введите /profile'
        else:
            return "Введите /start и попробуйте снова. Проверьте имя призывателя и сервер"


if __name__ == "__main__":
    vex1k = User("vex1k", "ru", "1488")
    vex1k.lolinfo()
    print(vex1k.add_user())
