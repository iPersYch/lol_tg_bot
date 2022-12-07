import pickle
from aiogram import Bot, Dispatcher, types

class Profile:

    def __init__(self, message: types.Message):
        self.tg_id = message.from_user.id
        with open('database/users_info.pickle', 'rb') as f:
            self.users_info = pickle.load(f)
        self.user = self.users_info[self.tg_id]

    async def profile_reply(self, message: types.Message):
        await message.reply(f'<i>Имя призывателя:</i>   <b>{self.user["summoner_name"]}</b>\n'
                      f'<i>Сервер:</i>                          <b>{self.user["summoner_server"]}</b>\n'
                      f'<i>Уровень:</i>                       <b>{self.user["summoner_level"]}</b>\n'
                      f'<i>Следите за игроком:</i>    <b>{self.user["watching_for_summonername"]}</b>\n'
                      f'<i>Статус уведомлений:</i> <b>{"Включены" if self.user["is_watching"] else "Отключены"}</b>\n'
                      f'<a href="http://ddragon.leagueoflegends.com/cdn/12.22.1/img/profileicon/{self.user["profileiconid"]}.png">&#8205</a>',
                      parse_mode='HTML', disable_web_page_preview=False)
