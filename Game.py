import asyncio
import copy
import json
from enum import Enum, auto
from random import random
from typing import Optional

from aiogram.types import ReplyKeyboardRemove, MediaGroup
from aiogram.types.base import TelegramObject

from Role import Team
from api import FuncEnum, send_message, media_generate, media_collector, mailing
from lex import *
from keyboard import *

games = []
waiting_lists = []


class Game:
    def __init__(self, waiting_list, manager: int, private: bool = False):
        self.id: int = waiting_list.id
        self.size: int = waiting_list.size_game
        self.manager: int = manager
        self.private: bool = private
        self.roles: list[Role] = waiting_list.game_roles
        self.players_id: list[int] = list(waiting_list.players_id.keys())
        self.players: list[Player] = []
        self.phase: GamePhase = GamePhase.day_exclusion
        self.skip_count: int = 0
        self.voting_count: int = 0
        self.time_evening: int = 20  # 20
        self.time_night: int = 30  # 30
        self.time_speak: int = 15  # 90
        self.time_voting: int = 20  # 20
        self.time_alert: int = 5  # 5 должно быть меньше всех остальных

    def get_player(self, user_id):
        for player in self.players:
            if player.id == user_id:
                return player

    @staticmethod
    def get_game(game_id):
        for game in games:
            if game.id == game_id:
                return game

    async def run(self):
        self.assign_roles(self.players_id, self.roles.copy())
        await self.send_to_all_players(FuncEnum.keyboard, text=m_start_game(self.players),
                                       keyboard=ReplyKeyboardRemove())
        for player in self.players:
            Bot_db.set_stage(player.id, 2)
            await send_message(player.id, FuncEnum.text, text=m_player_role(player))
            if player.role.get_team() is Team.mafia:
                await send_message(player.id, FuncEnum.text, text=m_team_killers(player, self.players))
        await asyncio.sleep(2)
        await self.evening()

    def assign_roles(self, players: list[int], role_list):
        def assign(chat_id, role):
            if 0 <= chat_id <= 100:
                new_player = Player(chat_id, role, virtual=True)
            else:
                new_player = Player(chat_id, role)
            self.players.append(new_player)

        for role in role_list:
            selected = random.choice(players)
            players.remove(selected)
            assign(selected, role)

        for chat_id in players:
            # if chat_id == 1662143212:
            #     assign(chat_id, Role.barman)
            # if chat_id == 2130716911:
            #     assign(chat_id, Role.don)
            # else:
            assign(chat_id, Role.common)

    async def send_to_all_players(self,
                                  func,
                                  predicate=lambda x: True,
                                  text: str = None,
                                  keyboard: TelegramObject = None,
                                  media: MediaGroup = None,
                                  sticker: str = None,
                                  voice: str = None) -> None:
        for player in self.players:
            if predicate(player) and not player.virtual:
                await send_message(player.id, func, text=text, keyboard=keyboard, media=media, sticker=sticker,
                                   voice=voice)

    async def send_to_all_players_without(self,
                                          user_id,
                                          func,
                                          text: str = None,
                                          keyboard: TelegramObject = None,
                                          media: MediaGroup = None,
                                          sticker: str = None,
                                          voice: str = None) -> None:
        predicate = lambda player: player.id != user_id
        await self.send_to_all_players(func, predicate, text=text, keyboard=keyboard, media=media, sticker=sticker,
                                       voice=voice)

    async def send_to_all_players_without_roles(self,
                                                roles: tuple,
                                                func,
                                                text: str = None,
                                                keyboard: TelegramObject = None,
                                                media: MediaGroup = None,
                                                sticker: str = None,
                                                voice: str = None) -> None:
        predicate = lambda player: player.role not in roles
        await self.send_to_all_players(func, predicate, text=text, keyboard=keyboard, media=media, sticker=sticker,
                                       voice=voice)

    async def send_to_all_players_to_roles(self,
                                           roles: tuple,
                                           func,
                                           text: str = None,
                                           keyboard: TelegramObject = None,
                                           media: MediaGroup = None,
                                           sticker: str = None,
                                           voice: str = None) -> None:
        predicate = lambda player: player.role in roles
        await self.send_to_all_players(func, predicate, text=text, keyboard=keyboard, media=media, sticker=sticker,
                                       voice=voice)

    async def send_to_all_players_to_role_without(self,
                                                  roles: tuple,
                                                  uid: int,
                                                  func,
                                                  text: str = None,
                                                  keyboard: TelegramObject = None,
                                                  media: MediaGroup = None,
                                                  sticker: str = None,
                                                  voice: str = None) -> None:
        predicate = lambda player: player.role in roles and player.id != uid
        await self.send_to_all_players(func, predicate, text=text, keyboard=keyboard, media=media, sticker=sticker,
                                       voice=voice)

    async def evening(self):
        print('Должен быть вечер')
        if self.phase is GamePhase.day_exclusion:

            self.phase = GamePhase.evening
            self.voting_count = 0

            for player in self.players:
                player.choosed = False
                player.mute = False
                player.drunk = False
                player.old_target = player.target
                player.target = None

                match player.role:
                    case Role.beauty:
                        await send_message(player.id, FuncEnum.text, text=lex['evening_beauty'],
                                           keyboard=kb_without_player(self.players, player))
                    case Role.medium:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['evening_medium'],
                                           keyboard=kb_role(self.players, Role.observer))
                    case Role.barman:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['evening_barman'],
                                           keyboard=kb_without_player(self.players, player))
                    case Role.snitch:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['evening_snitch'],
                                           keyboard=kb_without_player(self.players, player))
                    case _:
                        await send_message(player.id, func=FuncEnum.text, text=lex['evening_common'])

            await asyncio.sleep(self.time_evening - self.time_alert)
            if self.phase is GamePhase.evening:
                predicate = lambda player: player.role in (Role.beauty, Role.medium, Role.barman, Role.snitch) and not player.choosed
                await self.send_to_all_players(func=FuncEnum.text, predicate=predicate,
                                               text=m_time_alert(self.time_alert, 0))
                await asyncio.sleep(self.time_alert)
                await self.night()

    async def night(self):
        print('Должна быть ночь')
        if self.phase is GamePhase.evening:

            self.voting_count = 0
            self.phase = GamePhase.night
            self.revaluation_evening()
            for player in self.players:
                match player.role:
                    case Role.killer:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['night_killer'],
                                           keyboard=kb_without_team(self.players, Team.mafia))


                        for tg in self.players:
                            if player.id < 100:
                                if tg.id == 3:
                                    tg.choosen_kill += 1
                                    player.target = tg


                    case Role.doctor:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['night_doctor'],
                                           keyboard=kb_all_players(self.players))
                    case Role.bodyguard:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['night_bodyguard'],
                                           keyboard=kb_all_players(self.players))
                    case Role.sheriff:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['night_sheriff'],
                                           keyboard=kb_without_player(self.players, player))
                    case Role.godfather:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['night_godfather'],
                                           keyboard=kb_without_player(self.players, player))
                    case Role.don:
                        await send_message(player.id, FuncEnum.keyboard, text=lex['night_don'],
                                           keyboard=kb_without_player(self.players, player))
                    case _:
                        await send_message(player.id, FuncEnum.text, text=lex['night_common'])

            await asyncio.sleep(self.time_night - self.time_alert)
            if self.phase is GamePhase.night:
                predicate = lambda player: player.role in (
                Role.doctor, Role.sheriff, Role.killer, Role.godfather, Role.don, Role.bodyguard) and not player.choosed
                await self.send_to_all_players(func=FuncEnum.text, predicate=predicate,
                                               text=m_time_alert(self.time_alert, 1))
                await asyncio.sleep(self.time_alert)
                await self.setup_day()

    async def setup_day(self):
        print('Должен быть день')
        if self.phase is GamePhase.night:

            print('Выборы ночи:')
            for player in self.players:
                print(
                    f'{Bot_db.get_username(player.id)} - {player.choosen_kill}(k), {player.choosen_beauty}(b), {player.choosen_doctor}(d), {player.choosen_godfather}(g), {player.choosen_barman}(bar), {player.choosen_bodyguard}(bg)')
            print()

            self.phase = GamePhase.day_discuss
            self.revaluation_night()
            await self.send_to_all_players(FuncEnum.text, text=m_result_night(self.players))  # логика тут

            print('Итоги ночи:')
            for player in self.players:
                print(
                    f'{Bot_db.get_username(player.id)} - {player.choosen_kill}(k), {player.choosen_beauty}(b), {player.choosen_doctor}(d), {player.choosen_godfather}(g), {player.choosen_barman}(bar), {player.choosen_bodyguard}(bg)')
            print()

            for player in self.players:
                if player.choosen_kill > 0:
                    player.role = Role.observer
                    await send_message(player.id, FuncEnum.keyboard, text=lex['kill_player'],
                                       keyboard=keyboard_observer())
                elif player.choosen_godfather > 0:
                    player.mute = True
                elif player.choosen_barman > 0:
                    player.drunk = True
                player.voted = False
                player.medium_who_contact = None
                player.choosen_barman = 0
                player.choosen_kill = 0
                player.choosen_doctor = 0
                player.choosen_beauty = 0
                player.choosen_godfather = 0
                player.choosen_bodyguard = 0
                player.choosen_snitch = 0
            if not await self.check_end():
                await asyncio.sleep(self.time_speak - self.time_alert * 2)
                if self.phase is GamePhase.day_discuss:
                    await self.send_to_all_players(func=FuncEnum.text, text=m_time_alert(self.time_alert * 2, 2))
                    await asyncio.sleep(self.time_alert * 2)
                    await self.start_voting()

    def revaluation_evening(self):
        for player in self.players:
            if player.target is None:
                continue
            if player.choosen_beauty:
                match player.role:
                    case Role.beauty:
                        player.target.choosen_beauty -= 1
                    case Role.snitch:
                        player.target.choosen_snitch -= 1

    def revaluation_night(self):
        # roles = [player.role for player in self.players]
        for player in self.players:
            target = player.target
            if target is None:
                continue
            if player.choosen_beauty:
                match player.role:
                    case Role.killer:
                        target.choosen_kill -= 1
                    case Role.doctor:
                        target.choosen_doctor -= 1
                    case Role.godfather:
                        target.choosen_godfather -= 1
                    case Role.barman:
                        target.choosen_barman -= 1
                    case Role.bodyguard:
                        target.choosen_bodyguard -= 1

    async def start_voting(self):
        self.phase = GamePhase.day_voting
        self.voting_count = 0

        predicate_not_ghost = lambda player: player.role is not Role.observer
        predicate_not_mute = lambda player: not player.mute and predicate_not_ghost(player)
        predicate_mute = lambda player: player.mute and predicate_not_ghost(player)

        await self.send_to_all_players(FuncEnum.keyboard, predicate_not_mute, text=lex['start_voting'],
                                       keyboard=kb_all_players(self.players, skipped=True))
        await self.send_to_all_players(FuncEnum.text, predicate_mute, text=lex['start_voting'])
        await self.send_to_all_players_to_roles((Role.observer,), FuncEnum.text, text=lex['start_voting'])

        await asyncio.sleep(self.time_voting - self.time_alert)
        if self.phase is GamePhase.day_voting:
            predicate = lambda player: not player.voted and predicate_not_mute(player)
            await self.send_to_all_players(func=FuncEnum.text, predicate=predicate,
                                           text=m_time_alert(self.time_alert, 3))
            await asyncio.sleep(self.time_alert)
            await self.exclusion()

    async def exclusion(self):
        print('Должно быть изгнание')
        if self.phase is GamePhase.day_voting:

            self.phase = GamePhase.day_exclusion
            max_voices = self.skip_count
            target = []

            print('Итоги голосования:')
            for player in self.players:
                print(f'{Bot_db.get_username(player.id)} - {player.voices}')
            print(f'skip - {self.skip_count}')
            print()

            self.skip_count = 0
            for player in self.players:
                if player.voices > max_voices:
                    target = [player]
                    max_voices = player.voices
                elif player.voices == max_voices:
                    target.append(player)
                player.voices = 0
            await self.send_to_all_players(FuncEnum.text, text=m_result_voting(target))
            if len(target) == 1:
                target[0].role = Role.observer
                await send_message(target[0].id, FuncEnum.keyboard, text=lex['kill_player'],
                                   keyboard=keyboard_observer())
            await asyncio.sleep(2)
            if not await self.check_end():
                await self.evening()

    def get_fake_role(self) -> Role:
        players_with_relevant_role = tuple(filter(lambda player: player.role.get_team() is Team.mafia, self.players))
        return players_with_relevant_role[0].role

    async def check_end(self):
        mafia = 0
        citizen = 0
        for player in self.players:
            if player.role.get_team() is Team.mafia:
                mafia += 1
            elif player.role.get_team() is Team.citizen:
                citizen += 1
        if citizen <= mafia:
            await self.end(False)
            return True
        elif mafia == 0:
            await self.end(True)
            return True
        else:
            return False

    async def end(self, city_win: bool):
        text = lex['end_win'] if city_win else lex['end_defeat']
        roles = '\n'
        for player in self.players:
            if player.virtual:
                continue
            Bot_db.set_stage(player.id, 4)
            if (player.role.get_team() is Team.citizen and city_win) or (
                    player.role.get_team() is Team.mafia and not city_win):
                Bot_db.set_wins(player.id, Bot_db.get_wins(player.id) + 1)
                roles += f'{Bot_db.get_username(player.id)} - {str(player.role)}\n'
        await self.send_to_all_players(FuncEnum.text, text=text + roles)
        games.pop(games.index(self))
        w_list = WaitingList(self.size, self.manager, self.private, self.roles)
        waiting_lists.append(w_list)
        for player in self.players:
            await w_list.add_player(player.id, False, False)


class Player:
    def __init__(self, chat_id, role: Role, virtual: bool = False):
        self.virtual: bool = virtual
        self.id: int = chat_id
        self.role: Role = role
        self.choosen_kill: int = 0
        self.choosen_doctor: int = 0
        self.choosen_beauty: int = 0
        self.choosen_godfather: int = 0
        self.choosen_barman: int = 0
        self.choosen_bodyguard: int = 0
        self.choosen_snitch: int = 0
        self.target: Optional[Player] = None
        self.old_target: Optional[Player] = None
        self.medium_who_contact: Optional[Player] = None
        self.choosed: bool = False
        self.mute: bool = False
        self.drunk: bool = False
        self.voted: bool = False
        self.voices: int = 0

    def __eq__(self, other):
        if not isinstance(other, Player):
            raise TypeError("Операнд справа должен иметь тип Player")
        return self.id == other.id

    def __ne__(self, other):
        if not isinstance(other, Player):
            raise TypeError("Операнд справа должен иметь тип Player")
        return self.id != other.id


class GamePhase(Enum):
    day_discuss = auto()
    day_voting = auto()
    day_exclusion = auto()
    night = auto()
    evening = auto()


class WaitingList:
    counter = 0

    def __init__(self, size: int, manager: int, private: bool = False, roles: list[Role] = None, wait_for_confirm: bool = False, pause: bool = False):
        self.players_id: dict[int, bool] = {}
        self.manager: int = manager
        self.size_game: int = size
        self.game_roles: list[Role] = self.get_roles(size) if roles is None else roles
        self.id: int = WaitingList.counter
        self.private: bool = private
        self.wait_for_confirm: bool = wait_for_confirm
        self.pause: bool = pause
        WaitingList.counter += 1

    def is_full(self):  # хватает ли людей
        return len(self.players_id) >= self.size_game

    def is_ready(self):  # все ли готовы
        return all(self.players_id.values())

    async def add_player(self, player_id: int, confirm: bool = True, message: bool = True):
        if len(self.players_id) < self.size_game:
            Bot_db.set_stage(player_id, 4)
            Bot_db.set_game(player_id, self.id)
            if tuple(self.players_id.keys()).count(player_id) == 0:
                self.players_id[player_id] = confirm
                if message:
                    await self.send_all(
                        f'({len(self.players_id)}/{self.size_game}) Игрок {Bot_db.get_username(player_id)} подключился.')
                await self.preparedness(player_id, True)
        else:
            Bot_db.set_stage(player_id, 1)
            Bot_db.set_game(player_id, -1)
            pass
            # НУ ТУТ СООБЩЕНИЕ КАКОЕ-ТО КИКНУТЫМ (может лучше их сделать призраками)

    async def remove_player(self, player_id: int):
        Bot_db.set_stage(player_id, 1)
        Bot_db.set_game(player_id, -1)
        self.players_id.pop(player_id)
        await send_message(player_id, FuncEnum.keyboard, text='Вы отключились от игры.', keyboard=keyboard_main())
        # if len(tuple(filter(lambda id: id > 100, self.players_id))) == 0 and self in waiting_lists:
        #     waiting_lists.remove(self)
        #     return
        if self.pause:
            temp_obj = WaitingList.deserialize(self.manager)
            temp_obj.remove_player(player_id)
            WaitingList.serialize(temp_obj, self.manager)
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Тестить

        await self.send_all(
            f'({len(self.players_id)}/{self.size_game}) Игрок {Bot_db.get_username(player_id)} отключился или был исключён.')
        if self.manager == player_id and len(self.players_id) > 0:
            self.manager = list(self.players_id.keys())[0]
            await send_message(self.manager, FuncEnum.keyboard, text='Теперь вы являетесь менеджером этой игры и можете менять настройки.', keyboard=keyboard_manager())
        self.wait_for_confirm = False

    async def kick_unready(self):
        await asyncio.sleep(25)
        if self.wait_for_confirm:
            players = tuple(self.players_id.keys())
            for player in players:
                if player in players:
                    if not self.players_id[player]:
                        await self.remove_player(player)

    async def preparedness(self, player_id, show_mes: bool = False):
        if self.is_full():
            if self.is_ready():
                await self.start_game()
            else:
                if show_mes:
                    await self.send_all('Подтвердите начало игры.',
                                        predicate=lambda player: not self.players_id[player], keyboard=keyboard_lobby())
                    await self.send_all('Ожидаем подтверждение от всех игроков.')
                    self.wait_for_confirm = True
                    await self.kick_unready()
        else:
            if self.manager == player_id:
                await send_message(player_id, FuncEnum.keyboard, text=lex['waiting'], keyboard=keyboard_manager())
            else:
                await send_message(player_id, FuncEnum.keyboard, text=lex['waiting'], keyboard=keyboard_cancel())

    async def start_game(self):
        game = Game(self, private=self.private, manager=self.manager)
        games.append(game)
        waiting_lists.remove(self)
        await game.run()

    async def send_all(self, text: str, predicate=lambda x: True, keyboard=None):
        for player in list(self.players_id.keys()):
            if predicate(player):
                await send_message(player, FuncEnum.keyboard, text=text, keyboard=keyboard)

    @staticmethod
    def get_roles(size: int) -> list[Role]:
        match size:
            case 2:
                roles = [Role.killer]
            case 3:
                roles = [Role.killer, Role.doctor, Role.sheriff]
            case 4 | 5:
                roles = [Role.killer, Role.doctor, Role.sheriff, Role.beauty]
            case 6 | 7:
                roles = [Role.killer, Role.killer, Role.doctor, Role.godfather]
            case 8:
                roles = [Role.killer, Role.killer, Role.doctor, Role.godfather, Role.beauty, Role.beauty, Role.sheriff,
                         Role.sheriff]
            case 9:
                roles = [Role.killer, Role.killer, Role.doctor, Role.godfather, Role.beauty, Role.beauty, Role.sheriff,
                         Role.doctor]
            case _:
                roles = [Role.killer]

        return roles

    @staticmethod
    def serialize(obj, uid: int) -> None:
        data: dict = WaitingList._load_file('edit_games.json')

        obj: WaitingList = copy.deepcopy(obj)
        obj.__dict__['game_roles'] = list(map(lambda role: role.value, obj.__dict__['game_roles']))
        data[str(uid)] = obj.__dict__

        with open('edit_games.json', 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    async def deserialize(uid: int):
        data: dict = WaitingList._load_file('edit_games.json')
        try:
            data: dict = data[str(uid)]
        except KeyError:
            return WaitingList(6, uid)

        data['game_roles'] = list(map(lambda idr: Role(idr), data['game_roles']))

        w_list: WaitingList = WaitingList(data['size_game'], data['manager'], data['private'], data['game_roles'], data['wait_for_confirm'], data['pause'])
        w_list.players_id = {int(player): data['players_id'][player] for player in data['players_id']}
        return w_list

    @staticmethod
    def _load_file(file_name: str) -> dict:
        with open(file_name, 'r') as file:
            return json.load(file)
