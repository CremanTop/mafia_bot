# import keep_alive
import random

from aiogram import Bot, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command
from aiogram.types import Message, ContentType, CallbackQuery
from environs import Env
from magic_filter import F

from middlewares import *
from db import BotDB
from Game import *


#
# BOT_TOKEN = os.environ['BOT_TOKEN']  # Сохраняем значение переменной окружения в переменную bot_token
# password = os.environ['DEFAULT_PASSWORD']

env = Env()  # Создаем экземплят класса Env
env.read_env()  # Методом read_env() читаем файл .env и загружаем из него переменные в окружение

BOT_TOKEN = env('BOT_TOKEN')  # Сохраняем значение переменной окружения в переменную bot_token
password = env('DEFAULT_PASSWORD')

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
storage: MemoryStorage = MemoryStorage()
dp: Dispatcher = Dispatcher(bot, storage=storage)
Bot_db = BotDB('database')


@dp.message_handler(Command(commands=['start']))
async def start_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)
    if Bot_db.get_user_stage(uid) == 0:
        await message.answer(lex['command_start'])


@dp.message_handler(Command(commands=['help']))
@rate_limit(limit=2)
async def help_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)
    stage = Bot_db.get_user_stage(uid)
    if stage == 3:
        Bot_db.set_stage(uid, 1)

    if Bot_db.is_admin(uid):
        pass
    elif Bot_db.get_username(uid) == 'default' and stage == 0:
        await message.answer(lex['help_nick'], reply_markup=ReplyKeyboardRemove())
    elif stage == 1:
        await message.answer(lex['help_main'], reply_markup=keyboard_main())


@dp.message_handler(Command(commands=['rename']))
async def rename_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)
    stage = Bot_db.get_user_stage(uid)
    if stage in (1, 3):
        Bot_db.set_stage(uid, 0)
        await message.answer(lex['command_rename'], reply_markup=ReplyKeyboardRemove())


@dp.message_handler(Command(commands=['leaderboard']))
async def leader_command(message: Message):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)
    stage = Bot_db.get_user_stage(uid)
    if stage == 3:
        Bot_db.set_stage(uid, 1)
    champions = {}
    for user in Bot_db.get_users():
        champions[user[2]] = user[3]
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
    if stage == 3:
        Bot_db.set_stage(uid, 1)
    await message.answer(lex['command_rules'], reply_markup=keyboard_rules())


@dp.message_handler(content_types=['photo'])
async def photo_handler(message: Message):
    if message.from_user.id == 2130716911:
        print(message.photo[0].file_id)


@dp.message_handler(content_types=['voice'])
@rate_limit(limit=5)
async def voice_handler(message: Message):
    await player_chat(message, func=FuncEnum.voice, voice=message.voice.file_id, text=f'{Bot_db.get_username(message.from_user.id)} говорит.')


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
    buttons_text = (lex['button_rules_common'], lex['button_rules_ghost'], lex['button_rules_killer'], lex['button_rules_doctor'], lex['button_rules_sheriff'], lex['button_rules_beauty'], lex['button_rules_godfather'], lex['button_rules_immortal'], lex['button_rules_medium'])

    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)
    stage = Bot_db.get_user_stage(uid)

    if stage == 0:
        if text not in buttons_text and text not in (lex['button_main_menu'], lex['button_game_start'], lex['button_game_wait'], lex['button_game_list']):
            Bot_db.set_name(uid, text.strip())
            Bot_db.set_stage(uid, 1)
            await message.answer(m_setup_nick(text.strip()), reply_markup=keyboard_main())
        else:
            await message.answer(lex['rename_expection'], reply_markup=ReplyKeyboardRemove())

    elif stage == 1 and text == lex['button_main_menu']:
        await message.answer(lex['main_menu'], reply_markup=keyboard_main())

    elif stage == 1 and text == lex['button_game_list']:
        if len(list(filter(lambda game: not game.private, games))) > 0:
            mes = m_list_game(0, games)
        else:
            mes = lex['no_active_games']
        await message.answer(mes, reply_markup=kb_active_games(games, 0))

    elif stage == 1 and text == lex['button_game_wait']:
        if len(list(filter(lambda game: not game.private, waiting_lists))) > 0:
            mes = m_list_wait(0, waiting_lists)
        else:
            mes = lex['no_wait_games']
        await message.answer(mes, reply_markup=kb_wait_games(waiting_lists, 0))

    elif stage == 1 and text == lex['button_private_game']:
        Bot_db.set_stage(uid, 3)
        await message.answer(lex['req_private_game'], reply_markup=keyboard_cancel())

    elif stage == 1 and text == lex['button_create_game']:
        waiting_list = WaitingList(8)
        games_in_setup.append(waiting_list)
        await message.answer(m_game_setting(waiting_list), reply_markup=kb_game_setting(waiting_list))



    elif stage == 1 and text == lex['button_game_start']:



        if uid == 2130716911:
            # w_list = WaitingList(9, False)
            # waiting_lists.append(w_list)
            # #await w_list.add_player(uid)
            # for i in range(w_list.size_game - 1):
            #     await w_list.add_player(i)

            await new_virtual_game(random.randint(3, 8))
            #await new_virtual_game(4)



        else:
            min_slots = 100
            target_list = None
            for w_list in waiting_lists:
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

    elif stage == 1 and text in buttons_text:
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
            role = Role.doctor
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
        await message.answer(f'{lex["team"]} {str(role.get_team())}.\n\n{mes}{adv}')

    elif stage == 3:
        if text == lex['button_cancel']:
            Bot_db.set_stage(uid, 1)
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

    elif stage == 4:
        if text == lex['button_cancel']:
            Bot_db.set_stage(uid, 1)
            game_id = Bot_db.get_game(uid)
            for w_list in waiting_lists:
                if w_list.id == game_id:
                    w_list.players_id.remove(uid)
                    await w_list.send_all(
                        f'({len(w_list.players_id)}/{w_list.size_game}) Игрок {Bot_db.get_username(uid)} отключился.')
                    if len(w_list.players_id) == 0:
                        waiting_lists.remove(w_list)
            await message.answer(lex['main_menu'], reply_markup=keyboard_main())

    elif stage == 2:
        await player_chat(message, func=FuncEnum.text, text=f'{Bot_db.get_username(uid)} говорит:\n{text.strip()}')


async def new_virtual_game(num):
    wait_list = WaitingList(num)
    waiting_lists.append(wait_list)
    for i in range(wait_list.size_game):
        await wait_list.add_player(i)


async def player_chat(message: Message,
                      func,
                      text: str = None,
                      sticker: str = None,
                      voice: str = None):
    uid = message.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)
    game = Game.get_game(Bot_db.get_game(uid))
    if game is not None:
        player = game.get_player(uid)
        if player.role is Role.observer and message.text == lex['button_leave_game']:
            game.players.pop(game.players.index(player))
            Bot_db.set_stage(player.id, 1)
            Bot_db.set_game(player.id, -1)
            await message.answer(lex['player_leave'], reply_markup=keyboard_main())
        elif game.phase is GamePhase.day_discuss:
            if player.role is Role.observer:
                await message.answer(lex['ghost_message'])
            elif player.mute:
                await message.answer(lex['this_mute'])
            else:
                await game.send_to_all_players_without(uid, func=func, text=text, sticker=sticker, voice=voice)
        elif game.phase in (GamePhase.night, GamePhase.evening):
            if player.role.get_team() is Team.mafia:
                predicate = lambda player: player.id != uid and player.role.get_team() is Team.mafia
                await game.send_to_all_players(func=func, predicate=predicate, text=text, sticker=sticker, voice=voice)
            elif player.role is Role.observer and player.medium_who_contact is not None and text is not None:
                if text not in (f'{Bot_db.get_username(uid)} говорит.', f'{Bot_db.get_username(uid)} отправил(а):'):
                    await send_message(player.medium_who_contact.id, func=FuncEnum.text, text=text)
            elif player.role is Role.medium and player.target is not None:
                await send_message(player.target.id, func=func, text=text, sticker=sticker, voice=voice)


@dp.callback_query_handler()#(F.func(lambda c: c.data == 'button1'))
async def process_button_press(callback: CallbackQuery):
    uid = callback.from_user.id
    if not Bot_db.user_exists(uid):
        Bot_db.add_user(uid)
    stage = Bot_db.get_user_stage(uid)
    game = Game.get_game(Bot_db.get_game(uid))
    data = callback.data

    await callback.answer()

    def get_game(id: int, games: list):
        correct_games = tuple(filter(lambda fgame: fgame.id == id, games))
        if len(correct_games) > 0:
            return correct_games[0]

    def get_role(id: int):
        correct_role = tuple(filter(lambda x: x.value == id, Role.__members__.values()))
        if len(correct_role) > 0:
            return correct_role[0]

    async def game_list(index, l_games, m_list, kb):
        if len(l_games) > index * 8:
            await callback.message.edit_text(text=m_list(index, l_games), reply_markup=kb(l_games, index))
        else:
            await callback.message.edit_text(text=m_list(index - 1, l_games), reply_markup=kb(l_games, index - 1))

    async def set_private(game):
        game.private = not game.private
        await callback.message.edit_text(m_game_setting(game), reply_markup=kb_game_setting(game))

    async def subtract_player(game):
        game.size_game -= 1
        await callback.message.edit_text(m_game_setting(game), reply_markup=kb_game_setting(game))

    async def add_player(game):
        game.size_game += 1
        await callback.message.edit_text(m_game_setting(game), reply_markup=kb_game_setting(game))

    async def close_editor(game):
        games_in_setup.remove(game)
        waiting_lists.append(game)
        if game.private:
            code = random.randint(100000, 999999)
            while tuple(filter(lambda x: x.id == code, waiting_lists)):
                code = random.randint(100000, 999999)
            game.id = code
            await callback.message.edit_text(lex['your_code'] + str(code))
        await game.add_player(uid)

        for i in range(game.size_game - 1):
            await game.add_player(i)

    if stage == 1:
        keys = tuple(Cdata.__members__.values())
        tuple_matches = tuple(values in data for values in [key.value for key in keys])
        if any(tuple_matches):
            type_data = keys[tuple_matches.index(True)]
            len_data = len(type_data.value)

            if data[len_data:].isdigit():
                id = int(data[len_data:])

                if type_data is Cdata.iag:
                    await game_list(id, games, m_list_game, kb_active_games)

                elif type_data is Cdata.iwg:
                    await game_list(id, waiting_lists, m_list_wait, kb_wait_games)

                elif type_data is Cdata.ag:
                    game = get_game(id, games)
                    if game is not None:
                        game.players.append(Player(uid, Role.observer))
                        Bot_db.set_stage(uid, 2)
                        Bot_db.set_game(uid, id)
                        await callback.message.answer(text=lex['observer_add'], reply_markup=keyboard_observer())
                    else:
                        await callback.message.answer(text=lex['game_already_end'])

                elif type_data is Cdata.wg:
                    game = get_game(id, waiting_lists)
                    if game is not None:
                        if not game.is_full():
                            await game.add_player(uid)
                        else:
                            await callback.message.answer(text=lex['full_game'])
                    else:
                        await callback.message.answer(text=lex['full_game'])

                elif type_data in (Cdata.spubg, Cdata.sprig, Cdata.spg, Cdata.apg, Cdata.ceg):
                    game = get_game(id, games_in_setup)
                    if game is not None:
                        if type_data in (Cdata.spubg, Cdata.sprig):
                            await set_private(game)
                        elif type_data is Cdata.spg:
                            await subtract_player(game)
                        elif type_data is Cdata.apg:
                            await add_player(game)
                        elif type_data is Cdata.ceg:
                            await close_editor(game)
                    else:
                        await callback.answer(lex['bug'])

            elif Cdata.g.value in data[len_data:]:
                role_id = data[len_data:data.find(Cdata.g.value)]
                game_id = data[data.find(Cdata.g.value) + len(Cdata.g.value):]
                if role_id.isdigit() and game_id.isdigit():
                    role_id = int(role_id)
                    game_id = int(game_id)
                    role = get_role(role_id)

                    game = get_game(game_id, games_in_setup)
                    if game is not None and role is not None:
                        if type_data is Cdata.sr:
                            game.game_roles.remove(role)
                            await callback.message.edit_text(m_game_setting(game), reply_markup=kb_game_setting(game))
                        elif type_data is Cdata.ar:
                            game.game_roles.append(role)
                            await callback.message.edit_text(m_game_setting(game), reply_markup=kb_game_setting(game))
                    else:
                        await callback.answer(lex['bug'])

    elif game is not None and stage == 2:
        player = game.get_player(uid)
        if data.isdigit():
            target = game.get_player(int(data))
            t_name = Bot_db.get_username(target.id)
        else:
            target = None
            t_name = None

        if game.phase is GamePhase.evening:
            if target is not None and not player.choosed:
                if target == player.old_target:
                    await callback.message.answer(lex['eq_old_tg'])
                else:
                    if player.role is Role.beauty:
                        target.choosen_beauty += 1
                        await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                    elif player.role is Role.medium:
                        target.medium_who_contact = player
                        await send_message(target.id, FuncEnum.text, text=lex['medium_connect_to'])
                        await callback.message.answer(lex['medium_connect_from'])

                    if player.role in (Role.medium, Role.beauty):
                        player.choosed = True
                        player.target = target

                    await callback.message.delete()

        elif game.phase is GamePhase.night:
            if target is not None and not player.choosed:
                if target == player.old_target:
                    await callback.message.answer(lex['eq_old_tg'])
                else:
                    if player.role is Role.killer:
                        target.choosen_kill += 1
                        await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                    elif player.role is Role.godfather:
                        target.choosen_godfather += 1
                        await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                    elif player.role is Role.doctor:
                        target.choosen_doctor += 1
                        await callback.message.answer(lex['choose'] + t_name + lex['wait'])
                    elif player.role is Role.sheriff:
                        if player.choosen_beauty > 0:
                            await callback.message.answer(
                                lex['choose'] + t_name + '. ' + lex['no_find_role'] + lex['wait'])
                        else:
                            await callback.message.answer(lex['choose'] + t_name + '. ' + lex['his_role'] + str(target.role) + lex['wait'])
                    player.choosed = True
                    player.target = target

                    await callback.message.delete()

        elif game.phase is GamePhase.day_voting:
            await callback.message.delete()
            if player.mute:
                await callback.answer(text=lex['no_voted'])
            elif not player.voted:
                if target is not None:
                    if player.role != Role.observer:
                        target.voices += 1
                        await callback.message.answer(lex['vote'] + t_name + '.')
                    player.voted = True
                elif data == 'skip':
                    game.skip_count += 1
                    await callback.message.answer(lex['skip_m'])
                    player.voted = True
            else:
                await callback.answer(text=lex['already_voted'])


#
#
# keep_alive.keep_alive()

if __name__ == '__main__':
    for user in Bot_db.get_users():
        uid = user[1]
        Bot_db.set_game(uid, -1)
        Bot_db.set_stage(uid, 1)
        #Bot_db.set_wins(uid, 0)
    dp.middleware.setup(ThrottlingMiddleware(1))
    executor.start_polling(dp, skip_updates=False)
