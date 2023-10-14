from enum import Enum
from functools import reduce
from typing import Final, Callable, Union

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from lex import lex
from modules_import import *

config: Final[Config] = Config.get()
Bot_db = config.Bot_db

SetButton = tuple[tuple[str, ...], ...]
SetPlayer = list[Player]
Predicate = Callable[[Player], bool]


class Cdata(Enum):
    iag = 'index_active_game'
    ag = 'active_game'
    iwg = 'index_wait_game'
    wg = 'wait_game'
    spubg = 'set_public_game'
    sprig = 'set_private_game'
    spg = 'subtract_player_game'
    png = 'player_num_game'
    apg = 'add_player_game'
    ceg = 'close_editor_game'
    sr = 'subtract_role'
    ar = 'add_role'
    g = '_game'

    @property
    def value(self) -> str:
        """The value of the Enum member."""
        return self._value_


def keyboard_rules() -> ReplyKeyboardMarkup:
    buttons_text: SetButton = (('button_main_menu',),
                               ('button_rules_common', 'button_rules_ghost', 'button_rules_killer'),
                               ('button_rules_doctor', 'button_rules_sheriff', 'button_rules_beauty'),
                               ('button_rules_godfather', 'button_rules_immortal', 'button_rules_medium'),
                               ('button_rules_barman', 'button_rules_don', 'button_rules_bodyguard'),
                               ('button_rules_snitch',))
    return keyboard_builder(buttons_text)


def keyboard_main() -> ReplyKeyboardMarkup:
    buttons_text: SetButton = (('button_game_start',),
                               ('button_game_wait', 'button_game_list'),
                               ('button_private_game', 'button_create_game'))
    return keyboard_builder(buttons_text)


def keyboard_lobby() -> ReplyKeyboardMarkup:
    buttons_text: SetButton = (('button_ready',),
                               ('button_cancel',))
    return keyboard_builder(buttons_text)


def keyboard_cancel() -> ReplyKeyboardMarkup:
    buttons_text: SetButton = (('button_cancel',),)
    return keyboard_builder(buttons_text)


def keyboard_manager() -> ReplyKeyboardMarkup:
    buttons_text: SetButton = (('button_edit',),
                               ('button_cancel',))
    return keyboard_builder(buttons_text)


def keyboard_observer() -> ReplyKeyboardMarkup:
    buttons_text: SetButton = (('button_leave_game',),)
    return keyboard_builder(buttons_text)


def button_builder(name: str) -> KeyboardButton:
    return KeyboardButton(text=lex[name])


def keyboard_builder(buttons_text: SetButton) -> ReplyKeyboardMarkup:
    buttons: list[list[KeyboardButton]] = []
    for array in buttons_text:
        line: list[KeyboardButton] = []
        for text in array:
            line.append(button_builder(text))
        buttons.append(line)
    keyboard: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def _inline_ingame_keyboard_builder(players: SetPlayer, predicate: Predicate, size: int = 3, skipped: bool = False) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    lines: list[list[InlineKeyboardButton]] = []
    if skipped:
        buttons.append(InlineKeyboardButton(text=lex['skip'], callback_data='skip'))
    for player in players:
        if predicate(player):
            buttons.append(InlineKeyboardButton(text=f'{Bot_db.get_username(player.id)}'  # ({str(player.role)})'
                                                , callback_data=str(player.id)))
            if len(buttons) == size:
                lines.append(buttons)
                buttons = []
    if len(buttons) != 0:
        lines.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=lines)


def kb_without_role(players: SetPlayer, role: Role) -> InlineKeyboardMarkup:
    predicate: Predicate = lambda player: player.role is not role and player.role is not Role.observer
    return _inline_ingame_keyboard_builder(players, predicate)


def kb_role(players: SetPlayer, role: Role) -> InlineKeyboardMarkup:
    predicate: Predicate = lambda player: player.role is role
    return _inline_ingame_keyboard_builder(players, predicate)


def kb_without_team(players: SetPlayer, team: Team) -> InlineKeyboardMarkup:
    predicate: Predicate = lambda player: player.role.get_team() is not team and player.role is not Role.observer
    return _inline_ingame_keyboard_builder(players, predicate)


def kb_all_players(players: SetPlayer, skipped: bool = False) -> InlineKeyboardMarkup:
    predicate: Predicate = lambda player: player.role is not Role.observer
    return _inline_ingame_keyboard_builder(players, predicate, skipped=skipped)


def kb_without_player(players: SetPlayer, target: Player) -> InlineKeyboardMarkup:
    predicate: Predicate = lambda player: player != target and player.role is not Role.observer
    return _inline_ingame_keyboard_builder(players, predicate)


def __kb_games(games: list, index: int, data_game: str, data_index: str) -> InlineKeyboardMarkup:
    size: int = 8
    buttons: list[InlineKeyboardButton] = []
    two_line: list[InlineKeyboardButton] = []
    i: int = 1
    for game in games:
        if not game.private and not game.pause:
            if index * size < i <= (index + 1) * size:
                buttons.append(InlineKeyboardButton(text=str(i), callback_data=f'{data_game}{str(game.id)}'))
            i += 1
    if index > 0:
        two_line.append(InlineKeyboardButton(text=lex['back'], callback_data=f'{data_index}{index - 1}'))
    if i - 1 > (index + 1) * size:
        two_line.append(InlineKeyboardButton(text=lex['forward'], callback_data=f'{data_index}{index + 1}'))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, two_line])


def kb_active_games(games: list, index: int) -> InlineKeyboardMarkup:
    return __kb_games(games, index, Cdata.ag.value, Cdata.iag.value)


def kb_wait_games(lists: list, index: int) -> InlineKeyboardMarkup:
    return __kb_games(lists, index, Cdata.wg.value, Cdata.iwg.value)


def kb_game_setting(wait_list) -> InlineKeyboardMarkup:
    roles: list[Role] = wait_list.game_roles
    size: int = wait_list.size_game
    id: int = wait_list.id
    private: bool = wait_list.private

    dict_roles: dict[Role, int] = {}
    [dict_roles.update({role: roles.count(role)}) for role in roles]
    num_all_roles: int = reduce(lambda a, b: a + b, tuple(dict_roles.values()))

    lines: list[list[InlineKeyboardButton]] = []

    def add_button(text: str, data: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=data)

    def add_line(line: list[InlineKeyboardButton]) -> None:
        lines.append(line)

    add_line([add_button(lex['made_public'] if private else lex['made_private'],
                         f'{Cdata.spubg.value}{id}' if private else f'{Cdata.sprig.value}{id}')])

    def buttons_size() -> list[InlineKeyboardButton]:
        buttons: list[InlineKeyboardButton] = []
        if size > 3 and size > num_all_roles:
            buttons.append(add_button('➖', f'{Cdata.spg.value}{id}'))
        buttons.append(add_button(lex['player_num'], f'{Cdata.png.value}{id}'))
        if size < 50:
            buttons.append(add_button('➕', f'{Cdata.apg.value}{id}'))
        return buttons

    add_line(buttons_size())

    all_roles = Role.__members__
    all_roles = dict((k, v) for v, k in all_roles.items())  # Это мы переставляем местами ключи и значения
    del all_roles[Role.observer]
    del all_roles[Role.common]
    all_roles = sorted(all_roles.keys(), reverse=True, key=lambda x: dict_roles.get(x) if dict_roles.get(
        x) is not None else 0)  # Сортировка по убыванию количества

    for role in all_roles:
        buttons: list[InlineKeyboardButton] = []
        if dict_roles.keys().__contains__(role):
            buttons.append(add_button('➖', f'{Cdata.sr.value}{role.value}{Cdata.g.value}{id}'))
        buttons.append(add_button(str(role)[0].upper() + str(role)[1:], 'none'))
        if num_all_roles < size:
            buttons.append(add_button('➕', f'{Cdata.ar.value}{role.value}{Cdata.g.value}{id}'))
        if len(buttons) > 1:
            add_line(buttons)

    add_line([add_button(lex['close_editor'], f'{Cdata.ceg.value}{id}')])

    return InlineKeyboardMarkup(inline_keyboard=lines)
