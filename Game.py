import asyncio
from enum import Enum, auto
from random import random
from typing import Final, Self, Callable

from aiogram.types import ReplyKeyboardRemove, MediaGroup
from aiogram.types.base import TelegramObject

from Client import UserStatus as Us
from modules_import import *
from libs.api import FuncEnum, send_message
from keyboard import kb_without_player, kb_role, kb_without_team, kb_all_players, keyboard_observer, keyboard_main, \
    keyboard_manager, keyboard_lobby, keyboard_cancel
from lex import m_start_game, m_team_killers, m_player_role, lex, m_time_alert, m_result_night, m_result_voting, \
    m_players_in_lobby

config: Final[Config] = Config.get()
Bot_db = config.Bot_db

games: list = []
waiting_lists: list = []


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
        self.time_evening: Final[int] = 20  # 20
        self.time_night: Final[int] = 30  # 30
        self.time_speak: Final[int] = 15  # 90
        self.time_voting: Final[int] = 20  # 20
        self.time_alert: Final[int] = 5  # 5 должно быть меньше всех остальных

    def get_player(self, user_id: int) -> Player:
        for player in self.players:
            if player.id == user_id:
                return player

    @staticmethod
    def get_game(game_id: int) -> Self | None:
        if game_id == -1:
            return
        for game in games:
            if game.id == game_id:
                return game

    async def run(self) -> None:
        self.assign_roles(self.players_id, self.roles.copy())
        await self.send_to_all_players(FuncEnum.keyboard, text=m_start_game(self.players),
                                       keyboard=ReplyKeyboardRemove())

        async with asyncio.TaskGroup() as tg:
            for player in self.players:
                stage: int = Us.ingame.value if Bot_db.get_user_stage(player.id) == Us.lobby.value else Us.ingame_ghost.value
                Bot_db.set_stage(player.id, stage)

                tg.create_task(send_message(player.id, FuncEnum.text, text=m_player_role(player)))
                if player.role.get_team() is Team.mafia:
                    tg.create_task(send_message(player.id, FuncEnum.text, text=m_team_killers(player, self.players)))

        await asyncio.sleep(2)
        await self.evening()

    def assign_roles(self, players: list[int], role_list: list[Role]):
        def assign(chat_id: int, role: Role):
            if 0 <= chat_id <= 100:
                new_player = Player(chat_id, role, virtual=True)
            else:
                new_player = Player(chat_id, role)
            self.players.append(new_player)

        active_players: list[int] = list(filter(lambda x: Bot_db.get_user_stage(x) != Us.lobby_ghost.value, players))
        ghosts: tuple[int] = tuple(filter(lambda x: Bot_db.get_user_stage(x) == Us.lobby_ghost.value, players))

        for role in role_list:
            selected = random.choice(active_players)
            active_players.remove(selected)
            assign(selected, role)

        for chat_id in active_players:
            assign(chat_id, Role.common)

        for chat_id in ghosts:
            assign(chat_id, Role.observer)

    async def send_to_all_players(self,
                                  func,
                                  predicate=lambda x: True,
                                  text: str = None,
                                  keyboard: TelegramObject = None,
                                  media: MediaGroup = None,
                                  sticker: str = None,
                                  voice: str = None) -> None:
        async with asyncio.TaskGroup() as tg:
            for player in self.players:
                if predicate(player) and not player.virtual:
                    tg.create_task(send_message(player.id, func, text=text, keyboard=keyboard, media=media,
                                                sticker=sticker, voice=voice))

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
        if config.TEST_MODE:
            print('Начинается вечер')
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
                        text: str = lex['evening_beauty']
                        keyboard = kb_without_player(self.players, player)
                    case Role.medium:
                        text: str = lex['evening_medium']
                        keyboard = kb_role(self.players, Role.observer)
                    case Role.barman:
                        text: str = lex['evening_barman']
                        keyboard = kb_without_player(self.players, player)
                    case Role.snitch:
                        text: str = lex['evening_snitch']
                        keyboard = kb_without_player(self.players, player)
                    case _:
                        text: str = lex['evening_common']
                        keyboard = None

                asyncio.create_task(send_message(player.id, FuncEnum.keyboard, text=text, keyboard=keyboard))

            await asyncio.sleep(self.time_evening - self.time_alert)
            if self.phase is GamePhase.evening:
                predicate: Callable[[Player], bool] = lambda player: player.role in (
                    Role.beauty, Role.medium, Role.barman, Role.snitch) and not player.choosed
                await self.send_to_all_players(func=FuncEnum.text, predicate=predicate,
                                               text=m_time_alert(self.time_alert, 0))
                await asyncio.sleep(self.time_alert)
                await self.night()

    async def night(self):
        if config.TEST_MODE:
            print('Начинается ночь')
        if self.phase is GamePhase.evening:

            self.voting_count = 0
            self.phase = GamePhase.night
            self.revaluation_evening()
            for player in self.players:
                match player.role:
                    case Role.killer:
                        text: str = lex['night_killer']
                        keyboard = kb_without_team(self.players, Team.mafia)

                        for tg in self.players:
                            if player.id < 100:
                                if tg.id == 3:
                                    tg.choosen_kill += 1
                                    player.target = tg

                    case Role.doctor:
                        text: str = lex['night_doctor']
                        keyboard = kb_all_players(self.players)
                    case Role.bodyguard:
                        text: str = lex['night_bodyguard']
                        keyboard = kb_all_players(self.players)
                    case Role.sheriff:
                        text: str = lex['night_sheriff']
                        keyboard = kb_without_player(self.players, player)
                    case Role.godfather:
                        text: str = lex['night_godfather']
                        keyboard = kb_without_player(self.players, player)
                    case Role.don:
                        text: str = lex['night_don']
                        keyboard = kb_without_player(self.players, player)
                    case _:
                        text: str = lex['night_common']
                        keyboard = None

                asyncio.create_task(send_message(player.id, FuncEnum.keyboard, text=text, keyboard=keyboard))

            await asyncio.sleep(self.time_night - self.time_alert)
            if self.phase is GamePhase.night:
                predicate = lambda player: player.role in (
                    Role.doctor, Role.sheriff, Role.killer, Role.godfather, Role.don,
                    Role.bodyguard) and not player.choosed
                await self.send_to_all_players(func=FuncEnum.text, predicate=predicate,
                                               text=m_time_alert(self.time_alert, 1))
                await asyncio.sleep(self.time_alert)
                await self.setup_day()

    async def setup_day(self):
        if config.TEST_MODE:
            print('Начинается день')
        if self.phase is GamePhase.night:

            if config.TEST_MODE:
                print('Выборы ночи:')
                for player in self.players:
                    print(
                        f'{Bot_db.get_username(player.id)} - {player.choosen_kill}(k), {player.choosen_beauty}(b), {player.choosen_doctor}(d), {player.choosen_godfather}(g), {player.choosen_barman}(bar), {player.choosen_bodyguard}(bg)',
                        end='\n\n')

            self.phase = GamePhase.day_discuss
            self.revaluation_night()
            await self.send_to_all_players(FuncEnum.text, text=m_result_night(self.players))  # логика тут

            if config.TEST_MODE:
                print('Итоги ночи:')
                for player in self.players:
                    print(
                        f'{Bot_db.get_username(player.id)} - {player.choosen_kill}(k), {player.choosen_beauty}(b), {player.choosen_doctor}(d), {player.choosen_godfather}(g), {player.choosen_barman}(bar), {player.choosen_bodyguard}(bg)',
                        end='\n\n')

            for player in self.players:
                if player.choosen_kill > 0:
                    player.role = Role.observer
                    Bot_db.set_stage(player.id, Us.ingame_ghost.value)
                    asyncio.create_task(send_message(player.id, FuncEnum.keyboard, text=lex['kill_player'],
                                                     keyboard=keyboard_observer()))
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

        asyncio.create_task(self.send_to_all_players(FuncEnum.keyboard, predicate_not_mute, text=lex['start_voting'],
                                                     keyboard=kb_all_players(self.players, skipped=True)))
        asyncio.create_task(self.send_to_all_players(FuncEnum.text, predicate_mute, text=lex['start_voting']))
        asyncio.create_task(
            self.send_to_all_players_to_roles((Role.observer,), FuncEnum.text, text=lex['start_voting']))

        await asyncio.sleep(self.time_voting - self.time_alert)
        if self.phase is GamePhase.day_voting:
            predicate = lambda player: not player.voted and predicate_not_mute(player)
            await self.send_to_all_players(func=FuncEnum.text, predicate=predicate,
                                           text=m_time_alert(self.time_alert, 3))
            await asyncio.sleep(self.time_alert)
            await self.exclusion()

    async def exclusion(self):
        if config.TEST_MODE:
            print('Начинается изгнание')
        if self.phase is GamePhase.day_voting:

            self.phase = GamePhase.day_exclusion
            max_voices = self.skip_count
            target = []

            if config.TEST_MODE:
                print('Итоги голосования:')
                for player in self.players:
                    print(f'{Bot_db.get_username(player.id)} - {player.voices}')
                print(f'skip - {self.skip_count}', end='\n\n')

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
                Bot_db.set_stage(target[0].id, Us.ingame_ghost.value)
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

            if (player.role.get_team() is Team.citizen and city_win) or (player.role.get_team() is Team.mafia and not city_win):
                Bot_db.set_wins(player.id, Bot_db.get_wins(player.id) + 1)
                roles += f'{Bot_db.get_username(player.id)} - {str(player.role)}\n'

        await self.send_to_all_players(FuncEnum.text, text=text + roles)
        games.remove(self)
        w_list = WaitingList(self.size, self.manager, self.private, self.roles)
        waiting_lists.append(w_list)
        for player in self.players:
            stage: int = Us.lobby.value if Bot_db.get_user_stage(player.id) == Us.ingame.value or player.id == self.manager else Us.lobby_ghost.value
            Bot_db.set_stage(player.id, stage)
            await w_list.add_player(player.id, False, False, False)


class GamePhase(Enum):
    day_discuss = auto()
    day_voting = auto()
    day_exclusion = auto()
    night = auto()
    evening = auto()


class WaitingList:
    counter = 0

    def __init__(self, size: int, manager: int, private: bool = False, roles: list[Role] = None,
                 wait_for_confirm: bool = False, pause: bool = False):
        self.players_id: dict[int, bool] = {}
        self.manager: int = manager
        self.size_game: int = size
        self.game_roles: list[Role] = self.get_roles(size) if roles is None else roles
        self.id: int = WaitingList.counter
        self.private: bool = private
        self.wait_for_confirm: bool = wait_for_confirm
        self.pause: bool = pause
        WaitingList.counter += 1

        asyncio.create_task(self.add_player(self.manager, True, False))

    def is_full(self) -> bool:  # хватает ли людей
        return len(self.players_id) >= self.size_game

    def is_ready(self) -> bool:  # все ли готовы
        tuple_not_ghost = tuple(filter(lambda p_id: Bot_db.get_user_stage(p_id) == Us.lobby.value, self.players_id))
        ready: list[bool] = [self.players_id[x] for x in tuple_not_ghost]
        return all(ready)

    async def add_player(self, player_id: int, confirm: bool = True, message: bool = True, redistribute_stages: bool = True):
        if redistribute_stages:
            if not self.is_full():
                Bot_db.set_stage(player_id, Us.lobby.value)
            else:
                Bot_db.set_stage(player_id, Us.lobby_ghost.value)

        Bot_db.set_game(player_id, self.id)
        if tuple(self.players_id.keys()).count(player_id) == 0:
            self.players_id[player_id] = confirm
            if message:
                await self.send_all(
                    f'({len(self.players_id)}/{self.size_game}) Игрок {Bot_db.get_username(player_id)} подключился.',
                    lambda x: x != player_id)

            k_board = keyboard_cancel() if player_id != self.manager else keyboard_manager()
            await send_message(player_id, FuncEnum.text, m_players_in_lobby(self), keyboard=k_board)

            if not self.pause:
                await self.preparedness(player_id, True)

    async def remove_player(self, player_id: int):
        Bot_db.set_stage(player_id, Us.default.value)
        Bot_db.set_game(player_id, -1)
        self.players_id.pop(player_id)
        await send_message(player_id, FuncEnum.keyboard, text='Вы отключились от игры.', keyboard=keyboard_main())

        if not config.TEST_MODE:
            if len(tuple(filter(lambda id: id > 100, self.players_id))) == 0 and self in waiting_lists:
                waiting_lists.remove(self)
                return

        await self.send_all(
            f'({len(self.players_id)}/{self.size_game}) Игрок {Bot_db.get_username(player_id)} отключился или был исключён.')
        if self.manager == player_id and len(self.players_id) > 0:
            self.manager = list(self.players_id.keys())[0]
            await send_message(self.manager, FuncEnum.keyboard,
                               text='Теперь вы являетесь модератором этой игры и можете менять настройки.',
                               keyboard=keyboard_manager())
        if self.wait_for_confirm and not self.is_full():
            self.wait_for_confirm = False

    async def kick_unready(self):
        await asyncio.sleep(25)
        if not self.wait_for_confirm:
            return

        kick_count: int = 0
        players = tuple(filter(lambda p_id: Bot_db.get_user_stage(p_id) == Us.lobby.value, self.players_id.keys()))
        for player in players:
            if player in players:
                if not self.players_id[player]:
                    asyncio.create_task(self.remove_player(player))
                    kick_count += 1

        async def ghosts_return(ghosts: tuple[int]) -> None:
            await self.send_all(lex['you_not_ghost'], lambda x: x in ghosts)

            def set_lobby(ghost):
                Bot_db.set_stage(ghost, Us.lobby.value)

            map(set_lobby, ghosts)

        ghosts = tuple(filter(lambda p_id: Bot_db.get_user_stage(p_id) == Us.lobby_ghost.value, self.players_id.keys()))
        if len(ghosts) <= kick_count:
            await ghosts_return(ghosts)
            await self.preparedness()
        else:
            choosen_ghosts = ghosts[:kick_count]
            await ghosts_return(choosen_ghosts)

    async def preparedness(self, player_id: int = None, show_mes: bool = False):
        if self.is_full():
            if player_id is not None:
                await send_message(player_id, FuncEnum.keyboard, text=lex['you_ghost'], keyboard=keyboard_cancel())
            if self.is_ready():
                await self.start_game()
            else:
                if show_mes:
                    await self.send_all('Подтвердите начало игры.',
                                        predicate=lambda player: not self.players_id[player], keyboard=keyboard_lobby())
                    await self.send_all('Ожидаем подтверждение от всех игроков.')
                    self.wait_for_confirm = True
                    await self.kick_unready()
        elif player_id is not None:
            k_board = keyboard_cancel() if player_id != self.manager else keyboard_manager()
            await send_message(player_id, FuncEnum.keyboard, text=lex['waiting'], keyboard=k_board)

    async def start_game(self):
        game = Game(self, private=self.private, manager=self.manager)
        games.append(game)
        waiting_lists.remove(self)
        await game.run()

    async def send_all(self, text: str, predicate=lambda x: True, keyboard=None):
        async with asyncio.TaskGroup() as tg:
            for player in list(self.players_id.keys()):
                if predicate(player):
                    tg.create_task(send_message(player, FuncEnum.keyboard, text=text, keyboard=keyboard))

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
    def get_w_list(list_id: int, uid: int = None) -> Self | None:
        """Возвращает лист по id, если указанный игрок - его менеджер"""
        if list_id == -1:
            return
        for wlist in waiting_lists:
            if wlist.id == list_id:
                if uid is not None:
                    if wlist.manager == uid:
                        return wlist
                else:
                    return wlist

    # @staticmethod
    # def serialize(obj, uid: int) -> None:
    #     data: dict = WaitingList._load_file('edit_games.json')
    #
    #     obj: WaitingList = copy.deepcopy(obj)
    #     obj.__dict__['game_roles'] = list(map(lambda role: role.value, obj.__dict__['game_roles']))
    #     data[str(uid)] = obj.__dict__
    #
    #     with open('edit_games.json', 'w') as file:
    #         json.dump(data, file, indent=4)
    #
    # @staticmethod
    # async def deserialize(uid: int):
    #     data: dict = WaitingList._load_file('edit_games.json')
    #     try:
    #         data: dict = data[str(uid)]
    #     except KeyError:
    #         return WaitingList(6, uid)
    #
    #     data['game_roles'] = list(map(lambda idr: Role(idr), data['game_roles']))
    #
    #     w_list: WaitingList = WaitingList(data['size_game'], data['manager'], data['private'], data['game_roles'],
    #                                       data['wait_for_confirm'], data['pause'])
    #     w_list.players_id = {int(player): data['players_id'][player] for player in data['players_id']}
    #     return w_list
    #
    # @staticmethod
    # def _load_file(file_name: str) -> dict:
    #     with open(file_name, 'r') as file:
    #         return json.load(file)
