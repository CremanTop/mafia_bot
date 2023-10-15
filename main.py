# import keep_alive
import asyncio
import random
from typing import Final, Callable

from aiogram import executor
from aiogram.dispatcher.filters import Command
from aiogram.types import Message, ContentType, CallbackQuery, ReplyKeyboardRemove
from magic_filter import F

from Client import UserStatus as Us
from Game import games, waiting_lists, WaitingList, Game, GamePhase
from keyboard import keyboard_main, keyboard_rules, kb_active_games, kb_wait_games, keyboard_cancel, kb_game_setting, \
    Cdata, keyboard_observer
from lex import lex, m_leaders, m_setup_nick, m_list_game, m_list_wait, m_game_setting, m_players_in_lobby
from libs.api import FuncEnum, send_message
from middlewares import ThrottlingMiddleware, rate_limit
from modules_import import *

config: Final[Config] = Config.get()

bot = config.bot
dp = config.dp
Bot_db = config.Bot_db


@dp.message_handler(Command(commands=['start']))
async def start_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)

    if Bot_db.get_user_stage(uid) == Us.start.value:
        await message.answer(lex['command_start'])
    else:
        await message.answer(lex['help_main'], reply_markup=keyboard_main())


@dp.message_handler(Command(commands=['help']))
@rate_limit(limit=2)
async def help_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)

    stage = Bot_db.get_user_stage(uid)

    if stage == Us.waiting_code.value:
        Bot_db.set_stage(uid, Us.default.value)

    match stage:
        case Us.start.value:
            if Bot_db.get_username(uid) == 'default':
                await message.answer(lex['help_nick'], reply_markup=ReplyKeyboardRemove())
            else:
                pass
        case Us.default.value:
            await message.answer(lex['help_main'], reply_markup=keyboard_main())
        case Us.lobby.value | Us.lobby_ghost.value:
            await message.answer(lex['help_lobby'], reply_markup=keyboard_cancel())
        case Us.ingame.value | Us.ingame_ghost.value:
            pass


@dp.message_handler(Command(commands=['rename']))
async def rename_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)

    stage = Bot_db.get_user_stage(uid)

    match stage:
        case Us.default.value | Us.waiting_code.value:
            Bot_db.set_stage(uid, Us.start.value)
            await message.answer(lex['command_rename'], reply_markup=ReplyKeyboardRemove())
        case Us.start.value:
            await message.answer(lex['help_nick'], reply_markup=ReplyKeyboardRemove())
        case _:
            await message.answer(lex['rename_error'])


@dp.message_handler(Command(commands=['leaderboard']))
async def leader_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)

    stage = Bot_db.get_user_stage(uid)

    if stage == Us.waiting_code.value:
        Bot_db.set_stage(uid, Us.default.value)

    champions = {}
    for user_tuple in Bot_db.get_users():
        champions[user_tuple[2]] = user_tuple[3]
    sorted_dict = {}
    for key in sorted(champions, key=champions.get, reverse=True):
        sorted_dict[key] = champions[key]
    await message.answer(m_leaders(sorted_dict), reply_markup=keyboard_main())


@dp.message_handler(Command(commands=['rules']))
async def rules_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)

    stage = Bot_db.get_user_stage(uid)
    if stage == Us.waiting_code.value:
        Bot_db.set_stage(uid, Us.default.value)

    await message.answer(lex['command_rules'], reply_markup=keyboard_rules())


@dp.message_handler(content_types=['voice'])
@rate_limit(limit=5)
async def voice_handler(message: Message):
    await player_chat(message, func=FuncEnum.voice, voice=message.voice.file_id,
                      text=f'{Bot_db.get_username(message.from_user.id)} говорит.')


@dp.message_handler(content_types=['video_note'])
@rate_limit(limit=5)
async def video_handler(message: Message):
    await player_chat(message, func=FuncEnum.text, text=f'{Bot_db.get_username(message.from_user.id)} отправил(а):')
    await player_chat(message, func=FuncEnum.video, voice=message.video_note.file_id)


@dp.message_handler(content_types=['sticker'])
@rate_limit(limit=5)
async def sticker_handler(message: Message):
    await player_chat(message, func=FuncEnum.text, text=f'{Bot_db.get_username(message.from_user.id)} отправил(а):')
    await player_chat(message, func=FuncEnum.sticker, sticker=message.sticker.file_id)


@dp.message_handler(F.content_type == ContentType.TEXT)
@rate_limit(limit=0)
async def text_message(message: Message):
    uid = message.from_user.id
    text = message.text
    buttons_rules_text = (
        lex['button_rules_common'], lex['button_rules_ghost'], lex['button_rules_killer'], lex['button_rules_doctor'],
        lex['button_rules_sheriff'], lex['button_rules_beauty'], lex['button_rules_godfather'],
        lex['button_rules_immortal'], lex['button_rules_medium'], lex['button_rules_barman'], lex['button_rules_don'],
        lex['button_rules_bodyguard'], lex['button_rules_snitch'])

    if Bot_db.is_admin(uid):
        match text:
            case 'gamesp':
                print_games()
            case 'addvgame':
                await new_virtual_game(random.randint(3, 8), uid)

    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)

    stage = Bot_db.get_user_stage(uid)

    match stage:
        case Us.start.value:
            if text not in buttons_rules_text and text not in (
                    lex['button_main_menu'], lex['button_game_start'], lex['button_game_wait'],
                    lex['button_game_list']):
                Bot_db.set_name(uid, text.strip())
                Bot_db.set_stage(uid, Us.default.value)
                await message.answer(m_setup_nick(text.strip()), reply_markup=keyboard_main())
            else:
                await message.answer(lex['rename_expection'], reply_markup=ReplyKeyboardRemove())

        case Us.default.value:
            if text == lex['button_main_menu']:
                await message.answer(lex['main_menu'], reply_markup=keyboard_main())

            elif text == lex['button_game_list']:
                if len(list(filter(lambda game: not game.private, games))) > 0:
                    mes = m_list_game(0, games)
                else:
                    mes = lex['no_active_games']
                await message.answer(mes, reply_markup=kb_active_games(games, 0))

            elif text == lex['button_game_wait']:
                if len(list(filter(lambda game: not game.private, waiting_lists))) > 0:
                    mes = m_list_wait(0, waiting_lists)
                else:
                    mes = lex['no_wait_games']
                await message.answer(mes, reply_markup=kb_wait_games(waiting_lists, 0))

            elif text == lex['button_private_game']:
                Bot_db.set_stage(uid, Us.waiting_code.value)
                await message.answer(lex['req_private_game'], reply_markup=keyboard_cancel())

            elif text == lex['button_create_game']:
                waiting_list = WaitingList(6, uid, pause=True)
                waiting_lists.append(waiting_list)
                await message.answer(m_game_setting(waiting_list), reply_markup=kb_game_setting(waiting_list))

            elif text == lex['button_game_start']:
                min_slots = 100
                target_list = None
                for w_list in waiting_lists:
                    if w_list.pause or w_list.private:
                        continue
                    slots = w_list.size_game - len(w_list.players_id)
                    if slots == 1:
                        await w_list.add_player(uid)
                        return
                    else:
                        if slots < min_slots:
                            min_slots = slots
                            target_list = w_list
                if target_list is not None:
                    await target_list.add_player(uid)
                else:
                    await message.answer(lex['no_games'])

            elif text in buttons_rules_text:
                mes = lex["general_rules"]
                adv = ''
                role = None
                if text == lex['button_rules_common']:
                    adv = lex['rules_common']
                    role = Role.common
                elif text == lex['button_rules_ghost']:
                    mes = ''
                    adv = lex['rules_ghost']
                    role = Role.observer
                elif text == lex['button_rules_killer']:
                    adv = lex['rules_killer']
                    role = Role.killer
                elif text == lex['button_rules_doctor']:
                    adv = lex['rules_doctor']
                    role = Role.doctor
                elif text == lex['button_rules_sheriff']:
                    adv = lex['rules_sheriff']
                    role = Role.sheriff
                elif text == lex['button_rules_beauty']:
                    adv = lex['rules_beauty']
                    role = Role.beauty
                elif text == lex['button_rules_godfather']:
                    adv = lex['rules_godfather']
                    role = Role.godfather
                elif text == lex['button_rules_medium']:
                    adv = lex['rules_medium']
                    role = Role.medium
                elif text == lex['button_rules_immortal']:
                    adv = lex['rules_common'] + ' ' + lex['rules_immortal']
                    role = Role.immortal
                elif text == lex['button_rules_barman']:
                    adv = lex['rules_barman']
                    role = Role.barman
                elif text == lex['button_rules_don']:
                    adv = lex['rules_don']
                    role = Role.don
                elif text == lex['button_rules_bodyguard']:
                    adv = lex['rules_bodyguard']
                    role = Role.bodyguard
                elif text == lex['button_rules_snitch']:
                    adv = lex['rules_snitch']
                    role = Role.snitch
                await message.answer(
                    f'{str(role)[0].upper()}{str(role)[1:]}\n\n{lex["team"]} {str(role.get_team())}.\n\n{mes}{adv}')

        case Us.waiting_code.value:
            if text == lex['button_cancel']:
                Bot_db.set_stage(uid, Us.default.value)
                await message.answer(lex['main_menu'], reply_markup=keyboard_main())

            elif text.isdigit():
                private_game_tuple = tuple(filter(lambda game: game.id == int(text) and game.private, waiting_lists))
                if len(private_game_tuple) > 0:
                    private_game = private_game_tuple[0]
                    await private_game.add_player(uid)
                else:
                    await message.answer(lex['req_correct_code'])
            else:
                await message.answer(lex['req_correct_code'])

        case Us.lobby.value | Us.lobby_ghost.value:
            game_id = Bot_db.get_game(uid)
            if game_id == -1:
                return

            for w_list in waiting_lists:
                if w_list.id == game_id:
                    if text == lex['button_edit'] and w_list.manager == uid and not w_list.pause:
                        w_list.pause = True
                        w_list.wait_for_confirm = False
                        await w_list.send_all(lex['start_editing'], lambda x: x != w_list.manager)
                        await message.answer(m_game_setting(w_list), reply_markup=kb_game_setting(w_list))

                    elif text == lex['button_cancel']:
                        await w_list.remove_player(uid)
                        Bot_db.set_stage(uid, Us.default.value)

                    elif text == lex['button_ready']:
                        w_list.players_id[uid] = True
                        if not w_list.pause:
                            await w_list.preparedness(uid)
                        await message.answer('Вы подтвердили своё участие', reply_markup=ReplyKeyboardRemove())

                    else:
                        await w_list.send_all(f'{Bot_db.get_username(uid)} говорит:\n{text.strip()}',
                                              predicate=lambda player: player != uid)
        case Us.ingame.value | Us.ingame_ghost.value:
            await player_chat(message, func=FuncEnum.text, text=f'{Bot_db.get_username(uid)} говорит:\n{text.strip()}')


async def new_virtual_game(num: int, man: int):
    wait_list: WaitingList = WaitingList(num, man)
    waiting_lists.append(wait_list)
    for i in range(wait_list.size_game - 1):
        await wait_list.add_player(i)
    #wait_list.serialize(wait_list, man)


async def player_chat(message: Message,
                      func,
                      text: str = None,
                      sticker: str = None,
                      voice: str = None):
    uid = message.from_user.id
    uname = Bot_db.get_username(uid)

    def drunk_message(text):
        list_text = list(text)
        random.shuffle(list_text)
        return ''.join(list_text).strip()

    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)
        return

    game: Game = Game.get_game(Bot_db.get_game(uid))

    if game is not None:
        player = game.get_player(uid)

        if player.role is Role.observer and message.text == lex['button_leave_game']:
            game.players.pop(game.players.index(player))
            Bot_db.set_stage(player.id, Us.default.value)
            Bot_db.set_game(player.id, -1)
            await message.answer(lex['player_leave'], reply_markup=keyboard_main())

        elif game.phase is GamePhase.day_discuss:
            if player.role is Role.observer:
                await message.answer(lex['ghost_message'])

            elif player.mute:
                await message.answer(lex['this_mute'])

            else:
                if player.drunk:
                    # Если игрок отправляет текстовое сообщение (отправлять голосовые и видео он не может)
                    if text not in (f'{uname} говорит.', f'{uname} отправил(а):', None):
                        index = len(uname) + 11
                        text = text[:index] + drunk_message(text[index:])
                        await game.send_to_all_players_without(uid, func=FuncEnum.text, text=text)
                else:
                    await game.send_to_all_players_without(uid, func=func, text=text, sticker=sticker, voice=voice)

        elif game.phase in (GamePhase.night, GamePhase.evening):
            if player.role.get_team() is Team.mafia:
                predicate = lambda player: player.id != uid and player.role.get_team() is Team.mafia
                await game.send_to_all_players(func=func, predicate=predicate, text=text, sticker=sticker, voice=voice)

            elif player.role is Role.observer and player.medium_who_contact is not None and text is not None:
                if text not in (f'{uname} говорит.', f'{uname} отправил(а):'):
                    await send_message(player.medium_who_contact.id, func=FuncEnum.text, text=text)

            elif player.role is Role.medium and player.target is not None:
                await send_message(player.target.id, func=func, text=text, sticker=sticker, voice=voice)


@dp.callback_query_handler()  # (F.func(lambda c: c.data == 'button1'))
async def process_button_press(callback: CallbackQuery):
    uid = callback.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)

    stage = Bot_db.get_user_stage(uid)
    data = callback.data

    if config.TEST_MODE:
        print(data)

    await callback.answer()

    def get_game(game_id: int, g_games: list):
        all_correct_games = tuple(filter(lambda fgame: fgame.id == game_id, g_games))
        if len(all_correct_games) > 0:
            return all_correct_games[0]

    def get_role(enum_id: int):
        return Role(enum_id)

    async def game_list(index: int, l_games: list, m_list: Callable, kb: Callable):
        if len(l_games) > index * 8:
            await callback.message.edit_text(text=m_list(index, l_games), reply_markup=kb(l_games, index))
        else:
            await callback.message.edit_text(text=m_list(index - 1, l_games), reply_markup=kb(l_games, index - 1))

    async def callback_update(c_game):
        await callback.message.edit_text(m_game_setting(c_game), reply_markup=kb_game_setting(c_game))

    async def handler_voting(game: Game, player: Player, text: str):
        asyncio.create_task(callback.message.answer(text))
        player.voted = True
        count_must_votes: int = len(tuple(filter(
            lambda player: player.role is not Role.observer and not player.mute and not player.virtual, game.players)))
        
        game.voting_count += 1
        print(game.voting_count, count_must_votes)
        
        if game.voting_count >= count_must_votes:
            await game.exclusion()

    async def close_editor(wait_list):
        wait_list.pause = False
        if wait_list.private:
            code = random.randint(100000, 999999)
            while tuple(filter(lambda x: x.id == code, waiting_lists)):
                code = random.randint(100000, 999999)
            wait_list.id = code
            await callback.message.edit_text(lex['your_code'] + str(code))
        else:
            await callback.message.edit_text(m_game_setting(wait_list))

        await wait_list.send_all(lex['config_edit'] + m_game_setting(wait_list) + '\n\n' + m_players_in_lobby(wait_list),
                                 lambda x: x != wait_list.manager)
        await wait_list.preparedness()

        # for i in range(game.size_game - 2):
        #     await game.add_player(i)

    def data_handler() -> tuple[str, int] | None:
        keys = tuple(Cdata.__members__.values())
        tuple_matches = tuple(values in data for values in [key.value for key in keys])
        if any(tuple_matches):
            r_type_data = keys[tuple_matches.index(True)]
            r_len_data = len(r_type_data.value)
            return r_type_data, r_len_data

    async def editor_handler() -> None:
        if data[len_data:].isdigit():
            id: int = int(data[len_data:])
            w_list: WaitingList = WaitingList.get_w_list(id, uid)
            if w_list is None:
                return

            match type_data:
                case Cdata.spubg | Cdata.sprig:
                    w_list.private = not w_list.private
                case Cdata.spg:
                    w_list.size_game -= 1
                case Cdata.apg:
                    w_list.size_game += 1
                case Cdata.ceg:
                    await close_editor(w_list)
                case Cdata.png:
                    w_list.game_roles = WaitingList.get_roles(w_list.size_game)
            if type_data is not Cdata.ceg:
                await callback_update(w_list)

        elif Cdata.g.value in data[len_data:]:
            id: int = int(data[data.find(Cdata.g.value)+ len(Cdata.g.value):])
            w_list: WaitingList = WaitingList.get_w_list(id, uid)
            if w_list is None:
                return

            role_id = data[len_data:data.find(Cdata.g.value)]
            if role_id.isdigit():
                role = get_role(int(role_id))

                if role is not None:
                    if type_data is Cdata.sr:
                        w_list.game_roles.remove(role)
                        await callback_update(w_list)
                    elif type_data is Cdata.ar:
                        w_list.game_roles.append(role)
                        await callback_update(w_list)
                else:
                    await callback.answer(lex['bug'])

    if stage == Us.default.value:
        handler: tuple[str, int] | None = data_handler()
        if handler is None:
            return

        type_data, len_data = handler

        if data[len_data:].isdigit():
            id = int(data[len_data:])

            match type_data:
                case Cdata.iag:
                    await game_list(id, games, m_list_game, kb_active_games)

                case Cdata.iwg:
                    await game_list(id, waiting_lists, m_list_wait, kb_wait_games)

                case Cdata.ag:
                    game = get_game(id, games)
                    if game is not None:
                        game.players.append(Player(uid, Role.observer))
                        Bot_db.set_stage(uid, Us.ingame_ghost.value)
                        Bot_db.set_game(uid, id)
                        await callback.message.answer(text=lex['observer_add'], reply_markup=keyboard_observer())
                    else:
                        await callback.message.answer(text=lex['game_already_end'])

                case Cdata.wg:
                    game = get_game(id, waiting_lists)
                    if game is not None:
                        await game.add_player(uid)
                    else:
                        await callback.message.answer(text=lex['full_game'])

    elif stage == Us.lobby.value:
        handler: tuple[str, int] | None = data_handler()
        if handler is None:
            return

        type_data, len_data = handler
        await editor_handler()

    elif stage == Us.ingame.value:
        game = Game.get_game(Bot_db.get_game(uid))
        if game is None:
            return

        player = game.get_player(uid)
        target = None
        t_name = None
        if data.isdigit():
            target = game.get_player(int(data))
            if target is not None:
                t_name = Bot_db.get_username(target.id)

        if game.phase is GamePhase.evening:
            if target is not None and not player.choosed:
                print(target, player.old_target)
                if target is player.old_target:
                    await callback.message.answer(lex['eq_old_tg'])
                else:
                    match player.role:
                        case Role.beauty:
                            target.choosen_beauty += 1
                            await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                        case Role.medium:
                            target.medium_who_contact = player
                            await send_message(target.id, FuncEnum.text, text=lex['medium_connect_to'])
                            await callback.message.answer(lex['medium_connect_from'])
                        case Role.barman:
                            target.choosen_barman += 1
                            await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                        case Role.snitch:
                            target.choosen_snitch += 1
                            await callback.message.answer(lex['choose'] + t_name + lex['wait'])

                    evening_role: tuple[Role, ...] = (Role.medium, Role.beauty, Role.barman, Role.snitch)

                    if player.role in evening_role:
                        player.choosed = True
                        player.target = target

                        count_must_vote = len(tuple(
                            filter(lambda player: player.role in evening_role and not player.virtual, game.players)))
                        game.voting_count += 1
                        print(game.voting_count, count_must_vote)
                        if game.voting_count >= count_must_vote:
                            await game.night()

                    await callback.message.delete()

        elif game.phase is GamePhase.night:
            if target is not None and not player.choosed:
                print(target, player.old_target)
                if target is player.old_target:
                    await callback.message.answer(lex['eq_old_tg'])
                else:
                    match player.role:
                        case Role.killer:
                            target.choosen_kill += 1
                            await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                        case Role.godfather:
                            target.choosen_godfather += 1
                            await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                        case Role.doctor:
                            target.choosen_doctor += 1
                            await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                        case Role.bodyguard:
                            target.choosen_bodyguard += 1
                            await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                        case Role.sheriff:
                            if player.choosen_beauty > 0:
                                await callback.message.answer(
                                    lex['choose'] + t_name + '. ' + lex['no_find_role'] + lex['wait'])
                            else:
                                if target.choosen_snitch > 0:
                                    display_role: Role = game.get_fake_role()
                                else:
                                    display_role: Role = target.role
                                await callback.message.answer(
                                    lex['choose'] + t_name + '. ' + lex['his_role'] + str(display_role) + lex['wait'])
                        case Role.don:
                            if player.choosen_beauty > 0:
                                await callback.message.answer(
                                    lex['choose'] + t_name + '. ' + lex['no_find_role'] + lex['wait'])
                            else:
                                if target.choosen_snitch > 0 or target.role is not Role.sheriff:
                                    await callback.message.answer(
                                        lex['choose'] + t_name + '. ' + lex['not_sheriff'] + lex['wait'])
                                else:
                                    await callback.message.answer(
                                        lex['choose'] + t_name + '. ' + lex['his'] + str(target.role) + lex['wait'])
                    player.choosed = True
                    player.target = target
                    await callback.message.delete()

                    night_role: tuple[Role, ...] = (
                        Role.doctor, Role.sheriff, Role.killer, Role.godfather, Role.bodyguard, Role.don)

                    count_must_vote = len(
                        tuple(filter(lambda player: player.role in night_role and not player.virtual, game.players)))
                    if player.role in night_role:
                        game.voting_count += 1
                    print(game.voting_count, count_must_vote)
                    if game.voting_count >= count_must_vote:
                        await game.setup_day()

        elif game.phase is GamePhase.day_voting:
            await callback.message.delete()
            if player.mute:
                await callback.answer(text=lex['no_voted'])
            elif not player.voted:
                if player.drunk:
                    target = random.choices([target, player, random.choice(
                        tuple(filter(lambda player: player.role is not Role.observer, game.players)))],
                                            weights=[2, 1, 1], k=1)[0]
                if target is not None:
                    if player.role != Role.observer:
                        target.voices += 1
                        await handler_voting(game, player, lex['vote'] + t_name + '.')

                elif data == 'skip':
                    game.skip_count += 1
                    await handler_voting(game, player, lex['skip_m'])

            else:
                await callback.answer(text=lex['already_voted'])


#
#
# keep_alive.keep_alive()
def print_games():
    for game in waiting_lists:
        print(
            f'Игра {game.id}. Создатель - {game.manager}.\nПриватная - {game.private}, на паузе - {game.pause}. На {game.size_game} игроков. В лобби {len(game.players_id)} игроков.\n')


if __name__ == '__main__':
    for user in Bot_db.get_users():
        u_id = user[1]
        Bot_db.set_game(u_id, -1)
        Bot_db.set_stage(u_id, Us.default.value)
    #Bot_db.set_admin(2130716911)
    # Bot_db.set_wins(802878496, 12)
    # names = ('Mr. Green💤', 'Лампочка💤', 'Товарищ💤', 'Доцент💤', 'Предатель💤', 'Аристократ💤', 'Тракторист💤', 'Кузьма💤', 'Биба💤', 'Боба💤', 'Фаренгейт💤', 'Тирекс💤', 'Убийца💤', 'Мирный💤', 'Прокурор💤')
    # for i in range(15):
    #     Bot_db.set_name(i, names[i])
    dp.middleware.setup(ThrottlingMiddleware(1))
    executor.start_polling(dp, skip_updates=False)
