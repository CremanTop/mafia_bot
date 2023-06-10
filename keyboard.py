from enum import Enum
from functools import reduce

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from Role import Role
from lex import lex
from main import Bot_db


class Cdata(Enum):
    iag = 'index_active_game'
    ag = 'active_game'
    iwg = 'index_wait_game'
    wg = 'wait_game'
    spubg = 'set_public_game'
    sprig = 'set_private_game'
    spg = 'subtract_player_game'
    apg = 'add_player_game'
    ceg = 'close_editor_game'
    sr = 'subtract_role'
    ar = 'add_role'
    g = '_game'


def button_builder(name):
    return KeyboardButton(text=lex[name])


def keyboard_rules():
    buttons_text = [['button_main_menu'],
                    ['button_rules_common', 'button_rules_ghost', 'button_rules_killer'],
                    ['button_rules_doctor', 'button_rules_sheriff', 'button_rules_beauty'],
                    ['button_rules_godfather', 'button_rules_immortal', 'button_rules_medium'],
                    ['button_rules_barman']]
    return keyboard_builder(buttons_text)


def keyboard_main():
    buttons_text = [['button_game_start'],
                    ['button_game_wait', 'button_game_list'],
                    ['button_private_game', 'button_create_game']]
    return keyboard_builder(buttons_text)


def keyboard_cancel():
    buttons_text = [['button_cancel']]
    return keyboard_builder(buttons_text)


def keyboard_observer():
    buttons_text = [['button_leave_game']]
    return keyboard_builder(buttons_text)


def keyboard_builder(buttons_text):
    buttons = []
    for array in buttons_text:
        line = []
        for text in array:
            line.append(button_builder(text))
        buttons.append(line)
    keyboard_main = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard_main


def _inline_ingame_keyboard_builder(players, predicate, size: int = 3, skipped: bool = False):
    buttons = []
    lines = []
    if skipped:
        buttons.append(InlineKeyboardButton(text=lex['skip'], callback_data='skip'))
    for player in players:
        if predicate(player):
            buttons.append(InlineKeyboardButton(text=f'{Bot_db.get_username(player.id)} ({str(player.role)})'
            , callback_data=player.id))
            if len(buttons) == size:
                lines.append(buttons)
                buttons = []
    if len(buttons) != 0:
        lines.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=lines)


def kb_without_role(players, role):
    predicate = lambda player: player.role is not role and player.role is not Role.observer
    return _inline_ingame_keyboard_builder(players, predicate)


def kb_role(players, role):
    predicate = lambda player: player.role is role
    return _inline_ingame_keyboard_builder(players, predicate)


def kb_without_team(players, team):
    predicate = lambda player: player.role.get_team() is not team and player.role is not Role.observer
    return _inline_ingame_keyboard_builder(players, predicate)


def kb_all_players(players, skipped: bool = False):
    predicate = lambda player: player.role is not Role.observer
    return _inline_ingame_keyboard_builder(players, predicate, skipped=skipped)


def kb_without_player(players, target):
    predicate = lambda player: player != target and player.role is not Role.observer
    return _inline_ingame_keyboard_builder(players, predicate)


def _kb_games(games: list, index: int, data_game: str, data_index: str):
    size = 8
    buttons = []
    two_line = []
    i = 1
    for game in games:
        if not game.private:
            if index * size < i <= (index + 1) * size:
                buttons.append(InlineKeyboardButton(text=str(i), callback_data=f'{data_game}{str(game.id)}'))
            i += 1
    if index > 0:
        two_line.append(InlineKeyboardButton(text=lex['back'], callback_data=f'{data_index}{index - 1}'))
    if i - 1 > (index + 1) * size:
        two_line.append(InlineKeyboardButton(text=lex['forward'], callback_data=f'{data_index}{index + 1}'))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, two_line])


def kb_active_games(games, index):
    return _kb_games(games, index, Cdata.ag.value, Cdata.iag.value)


def kb_wait_games(lists, index):
    return _kb_games(lists, index, Cdata.wg.value, Cdata.iwg.value)


def kb_game_setting(wait_list):
    roles = wait_list.game_roles
    size = wait_list.size_game
    id = wait_list.id
    private = wait_list.private

    dict_roles = {}
    [dict_roles.update({role: roles.count(role)}) for role in roles]
    num_all_roles = reduce(lambda a, b: a + b, tuple(dict_roles.values()))

    lines = []

    def add_button(text: str, data: str):
        return InlineKeyboardButton(text=text, callback_data=data)

    def add_line(line: list):
        lines.append(line)

    add_line([add_button(lex['made_public'] if private else lex['made_private'], f'{Cdata.spubg.value}{id}' if private else f'{Cdata.sprig.value}{id}')])

    def buttons_size():
        buttons = []
        if size > 3 and size > num_all_roles:
            buttons.append(add_button('➖', f'{Cdata.spg.value}{id}'))
        buttons.append(add_button(lex['player_num'], 'none'))
        if size < 50:
            buttons.append(add_button('➕', f'{Cdata.apg.value}{id}'))
        return buttons

    add_line(buttons_size())

    all_roles = Role.__members__
    all_roles = dict((k, v) for v, k in all_roles.items())  # Это мы переставляем местами ключи и значения
    del all_roles[Role.observer]
    del all_roles[Role.common]
    all_roles = sorted(all_roles.keys(), reverse=True, key=lambda x: dict_roles.get(x) if dict_roles.get(x) is not None else 0)  # Сортировка по убыванию количества

    for role in all_roles:
        buttons = []
        if dict_roles.keys().__contains__(role):
            buttons.append(add_button('➖', f'{Cdata.sr.value}{role.value}{Cdata.g.value}{id}'))
        buttons.append(add_button(str(role)[0].upper() + str(role)[1:], 'none'))
        if num_all_roles < size:
            buttons.append(add_button('➕', f'{Cdata.ar.value}{role.value}{Cdata.g.value}{id}'))
        if len(buttons) > 1:
            add_line(buttons)

    add_line([add_button(lex['close_editor'], f'{Cdata.ceg.value}{id}')])

    return InlineKeyboardMarkup(inline_keyboard=lines)
