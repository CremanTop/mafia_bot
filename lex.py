import random
from typing import Final, Optional, Union

from modules_import import *

config: Final[Config] = Config.get()
Bot_db = config.Bot_db

PlayerS = list[Player]

lex: dict[str, str] = {
    'help_nick': 'Сейчас тебе нужно придумать и написать мне свой никнейм.',
    'help_main': 'Чтобы начать игру, нажми "Найти игру". Что узнать правила, используй /rules.',
    'help_lobby': 'Вы находитесь в лобби. Здесь вы можете общаться с другими игроками в ожидании начала игры.',
    'command_start': 'Добро пожаловать в мафию! Пожалуйста, отправь мне свой никнейм, который будет отображаться в играх.',
    'command_rename': 'Твой никнейм сброшен. Теперь отправь мне новый.',
    'command_rules': 'Итак, в этой игре все игроки делятся на две команды: мирные жители 👔 и мафия 🔪.\nЦель мирных '
                     'жителей: вычислить и изгнать мафию.\nЦель мафии: захватить власть над городом. Для этого '
                     'достаточно, чтобы членов мафии осталось не меньше, чем мирных жителей.\n\nИгра циклично идёт '
                     'через несколько фаз: 🌅 день, 🌄 вечер, 🌃 ночь.\n\nНочью обычные жители спят, а мафия выбирает, '
                     'на кого совершить нападение (представители мафии могут общаться друг с другом). Но горожане не '
                     'так уж беззащитны - у них есть разные роли, '
                     'которые тоже просыпаются ночью и совершают действия: лечат, проводят обыск и тд.\n\nДнём все '
                     'живые игроки просыпаются, видят итоги ночи и в течение 1,5 минут обсуждают, кто может быть '
                     'мафией. Вы можете отправлять текстовые, голосовые сообщения; видеосообщения; стикеры; и их '
                     'увидят остальные игроки (Не спамьте! Сообщения, отправляемые чаще, чем раз в 5 секунд, '
                     'приходить не будут!). По окончанию обсуждения даётся 20 секунд на голосование. Игрок, '
                     'получивший больше всего голосов, изгоняется из игры.\n\nДля получения помощи по отдельным '
                     'ролям, используйте кнопки.',
    'rename_expection': 'Вы не можете установить никнейм, совпадающий с названием одной из ролей! Введите другое имя.',
    'rename_error': 'Сейчас вы не можете изменить никнейм! 🚫',
    'main_menu': 'Быстрая игра подключит вас к ближайшей к заполнению очереди.\n\nНажав "Игры с ожиданием игроков", '
                 'вы увидите список игр и сможете выбрать, к какой из них подключиться.\n\nВ активных играх '
                 'отображаются игры, идущие в данный момент. К ним можно подключиться в качестве наблюдателя.',
    'back': 'Назад',
    'forward': 'Вперёд',
    'button_cancel': 'Отмена',
    'no_active_games': 'Сейчас нет активных игр.',
    'no_wait_games': 'Сейчас нет ожиданий игр.',
    'req_private_game': 'Введите код приватной игры.',
    'req_correct_code': 'Такой игры нет, введите другой код.',
    'button_main_menu': 'Меню игр',
    'button_game_start': 'Быстрая игра',
    'button_game_list': 'Активные игры',
    'button_game_wait': 'Игры с ожиданием игроков',
    'button_private_game': 'Подключиться к приватной игре',
    'button_create_game': 'Создать игру',
    'button_leave_game': 'Выйти из игры',
    'button_ready': 'Готов ✅',
    'button_edit': 'Редактировать игру',
    'button_rules_common': 'Мирный житель',
    'button_rules_ghost': 'Призрак',
    'button_rules_killer': 'Убийца',
    'button_rules_doctor': 'Доктор',
    'button_rules_sheriff': 'Шериф',
    'button_rules_beauty': 'Красотка',
    'button_rules_godfather': 'Крёстный отец',
    'button_rules_immortal': 'Бессмертный',
    'button_rules_medium': 'Медиум',
    'button_rules_barman': 'Бармен',
    'button_rules_don': 'Дон',
    'button_rules_bodyguard': 'Телохранитель',
    'button_rules_snitch': 'Стукач',
    'general_rules': 'День: все игроки обсуждают, кто может быть мафией и выгоняют голосованием подозрительных игроков.\n\n',
    'rules_common': 'Ночь: спит, нет действий.',
    'rules_ghost': 'Если вас убили или изгнали, вы становитесь призраком. Теперь вы не можете совершать действия, голосовать и участвовать в обсуждении.',
    'rules_killer': 'Ночь: выбирает, на кого из игроков совершить покушение. Если ничего не помешает, то к утру цель '
                    'будет мертва. Если убийц несколько, то ночью они могут обсуждать друг с другом, '
                    'за кого проголосовать. Цель, выбранная большинством, станет общей целью и получит очки смерти от '
                    'всех убийц (Пример: двое убийц выбрали игрока МИРНЫЙ2003, а третий выбрал игрока '
                    'ШЕРИФ_С_ПИСТОЛЕТОМ. Целью убийства станет игрок МИРНЫЙ2003 и получит 3 очка смерти (от всех трёх '
                    'убийц). Значит он может выжить, если, например, его вылечат три доктора). Если несколько целей '
                    'получили равное число голосов, то выбирается случайная из них.',
    'rules_doctor': 'Ночь: выбирает, кого из игроков вылечить. Если на этого игрока было совершено покушение, '
                    'то к утру он выживет.\nПримечание: если убийц несколько, то доктор защищает игрока только от '
                    'одного выстрела (убирает одно очко смерти) и пациент может умереть от остальных.',
    'rules_sheriff': 'Ночь: выбирает, кого из игроков проверить и узнаёт его роль.',
    'rules_beauty': 'Вечер: выбирает, чьё действие этой ночью будет отменено. '
                    'Примеры: если был выбран доктор, то его лечение не засчитывается (убирает одно очко лечения); '
                    'если был выбран убийца, то убийство не происходит (убирает одно очко смерти); если был выбран '
                    'бессмертный, то этой ночью он теряет неуязвимость.\nПримечание: если убийц несколько, '
                    'то красотка отвлекает только одного, другие всё равно совершают убийство.',
    'rules_godfather': 'Ночь: просыпается вместе с убийцами, может с ними обсуждать покушение, но не голосует за '
                       'жертву. Вместо этого выбирает игрока, который днём будет молчать и не примет участия в '
                       'голосовании.',
    'rules_immortal': 'Не может быть убит. Только изгнан дневным голосованием.',
    'rules_medium': 'Вечер: выбирает одного призрака, с которым может общаться до наступления дня. Медиум может '
                    'отправлять любые сообщения, призрак - только текстовые.',
    'rules_barman': 'Вечер: выбирает игрока, чьи сообщения днём будут запутаны. Выбранный игрок не сможет отправлять '
                    'ничего, кроме текстовых сообщений. При голосовании с шансом в 50% он отдаст голос не за того, '
                    'кого выбрал.',
    'rules_don': 'Ночь: выбирает, кого из игроков проверить и узнаёт, является ли он шерифом.',
    'rules_bodyguard': 'Ночь: выбирает, кого из игроков защитить. Если на этого игрока было совершено покушение, '
                       'то он выживает, независимо от того, сколько очков смерти он получил. После одной удачной '
                       'защиты телохранитель теряет способности и становится мирным жителем до конца игры.',
    'rules_snitch': 'Вечер: выбирает, кого из игроков очернить. При проверке этого игрока любой ролью, '
                    'будет отображаться, что он находится в команде мафии, даже если на самом деле это не так.',
    'team': 'Команда:',
    'waiting': 'Ищем для вас соперников. Как только наберётся достаточно игроков, мы начнём.',
    'you_ghost': 'В лобби достаточно игроков. Вы можете остаться и наблюдать за игрой как призрак или выйти (если '
                 'кто-то из других игроков выйдет, вы сможете занять его место).',
    'you_not_ghost': 'Для вас освобдилось место! Теперь вы можете участвовать в игре.',
    'evening_common': '🌄 Наступает вечер. На улицу выходят разные сомнительные личности.',
    'evening_beauty': '🌄 Наступает вечер. Пришло время выбрать, чьё действие этой ночью будет отменено.',
    'evening_medium': '🌄 Наступает вечер. Пришло время выбрать, с каким призраком связаться.',
    'evening_barman': '🌄 Наступает вечер. Пришло время выбрать, кто утром будет мучаться от похмелья.',
    'evening_snitch': '🌄 Наступает вечер. Пришло время выбрать, кто будет оклеветан при проверке роли.',
    'night_common': '🌃 Наступает ночь. Мирные жители засыпают, просыпается мафия...',
    'night_killer': '🌃 Наступает ночь. Теперь, когда мирные жители уснули, пришло время выбрать, кто из них не увидит завтрашний день...',
    'night_doctor': '🌃 Наступает ночь. Бригада скорой помощи выезжает, но приехать ко всем вы не успеете. Пришло время выбрать, кто сегодня будет спасён.',
    'night_sheriff': '🌃 Наступает ночь. Убийца прячется под личиной мирного жителя. Пришло время проверить кого-то из них, чтобы вычислить его.',
    'night_godfather': '🌃 Наступает ночь. Пришло время выбрать, кто днём не сможет участвовать в обсуждении и голосовать.',
    'night_don': '🌃 Наступает ночь. Кто-то из мирных на самом деле шериф. Пришло время проверить кого-то из них, чтобы вычислить его.',
    'night_bodyguard': '🌃 Наступает ночь. Вы можете защитить кого-либо, закрыв своим телом. Пришло время выбрать, кто сегодня будет спасён.',
    'start_voting': 'Обсуждение закончено. Пришло время выбрать, кто должен быть изгнан.',
    'vote': 'Вы проголосовали за ',
    'already_voted': 'Вы уже проголосовали!',
    'choose': 'Вы выбрали ',
    'wait': '. Ожидание выборов других игроков.',
    'his_role': 'Его/её роль - ',
    'his': 'Он/она - ',
    'not_sheriff': 'Это не шериф',
    'end_defeat': 'Город погрузился в полное беззаконие. Это конец игры. Мафия торжествует.',
    'end_win': 'Мирным жителям наконец удалось победить мафию! Теперь город может спать спокойно. Это конец игры.',
    'ghost_message': 'Ваше сообщение не было отправлено другим игрокам, так как вы наблюдатель.',
    'observer_add': 'Вы подключились к игре как наблюдатель.',
    'kill_player': 'Вы стали призраком.',
    'player_leave': 'Вы покинули игру.',
    'full_game': 'Эта игра уже заполнена!',
    'game_already_end': 'Эта игра уже закончилась!',
    'no_games': 'Сейчас нет доступных игр, вы можете создать свою.',
    'this_mute': 'Вы не можете отправлять сообщения в чат.',
    'no_voted': 'Вы не можете голосовать',
    'player_num': 'Количество игроков',
    'made_public': 'Сделать публичной 🔊',
    'made_private': 'Сделать приватной 🔒',
    'close_editor': '✅Завершить редактирование✅',
    'bug': 'Ошибка!',
    'your_code': 'Код игры. Дайте его своим друзьям, чтобы они смогли подключиться к вам:\n\n',
    'medium_connect_to': 'С вами связался медиум. В течение ночи вы можете общаться с ним, но только текстовыми сообщениями.',
    'medium_connect_from': 'Вы связались с призраком. В течение ночи вы можете общаться с ним.',
    'skip': 'Пропуск',
    'skip_m': 'Вы пропустили голосование.',
    'no_find_role': 'Вы не можете узнать роль',
    'eq_old_tg': 'Вы не можете выбирать одного и того же игрока несколько раз подряд!',
    'start_editing': 'Лобби на паузе, модератор вносит изменения в настройки игры.',
    'config_edit': 'Настройки игры изменены модератором.\nНовые настройки:\n\n'
}


def m_setup_nick(nick: str) -> str:
    return f'Прекрасно, {nick}, теперь мы можем приступить к игре. Если ты не знаешь правила, то сейчас я всё ' \
           f'объясню.\n\n{lex["command_rules"]}\n\nНажми на кнопку "Найти игру", когда захочешь поиграть. '


def m_start_game(players: PlayerS) -> str:
    roles: list[str] = []
    player_names: list[str] = []
    for player in players:
        player_names.append(Bot_db.get_username(player.id))
        roles.append(str(player.role))
    random.shuffle(roles)
    return f'Игра началась! Добро пожаловать {", ".join(player_names)}. \n\nВ последнее время в маленьком городе неспокойно. Страшные вещи происходят по ночам.\n\nРоли: {", ".join(roles)}.'


def m_player_role(player: Player) -> str:
    task: str = ''
    match player.role:
        case Role.killer:
            task = 'убивать мирных жителей по ночам и не вызывать подозрений днём.'
        case Role.common:
            task = 'найти убийцу и изгнать его, чтобы прекратить эти преступления.'
        case Role.doctor:
            task = 'догадаться, кого выбрали сегодня убийцы, и вылечить его.'
        case Role.sheriff:
            task = 'найти убийцу. Вы можете провести обыск у любого игрока и узнать, является ли он мафией.'
        case Role.beauty:
            task = 'выбирать игрока, чьё действие этой ночью будет отменено.'
        case Role.godfather:
            task = 'выбирать игрока, который днём будет молчать и не примет участие в голосовании.'
        case Role.immortal:
            task = 'найти убийцу и изгнать его. Вы не можете быть убиты ночью.'
        case Role.medium:
            task = 'общаться с призраками, чтобы больше узнать о потаённой стороне игры.'
        case Role.barman:
            task = 'выбирать игрока, сообщения которого днём будут перепутаны.'
        case Role.don:
            task = 'найти шерифа. Вы можете совершить проверку любого игрока и узнать, является ли он шерифом.'
        case Role.bodyguard:
            task = 'догадаться, кого выбрали убийцы и защитить его.'
        case Role.snitch:
            task = 'выбирать игрока, который при проверке роли будет оклеветан.'
    return f'Вы - {str(player.role)}. Ваша задача {task}'


def m_team_killers(this: Player, players: PlayerS) -> str:
    team: list[str] = []
    for player in players:
        if player.role.get_team() is Team.mafia and player != this:
            team.append(Bot_db.get_username(player.id))
    if len(team) == 0:
        return ''
    elif len(team) == 1:
        text = ''
    else:
        text = 'и'
    return f'Ваш{text} союзник{text}: {", ".join(team)}. С ним{text} вы будете планировать убийства.'


# Плохая реализация, в файле lex не должно быть логики, только сообщения
def m_result_night(players: PlayerS) -> str:
    victims: PlayerS = []
    cancelled: PlayerS = []
    mute: PlayerS = []
    alives: Union[PlayerS, list[str]] = []
    mes: Union[list[str], str] = []
    for player in players:
        if player.choosen_beauty > 0:
            cancelled.append(player)
        if player.choosen_kill > 0:
            victims.append(player)
        if player.choosen_godfather > 0:
            mute.append(player)

    final_victim: Optional[Player] = None
    if len(victims) > 0:
        max_point: int = 0
        prior_victim: PlayerS = []
        for vict in victims:
            if vict.choosen_kill > max_point:
                max_point = vict.choosen_kill
                prior_victim = [vict]
            elif vict.choosen_kill == max_point:
                prior_victim.append(vict)
        final_victim = random.choice(prior_victim)
        for vict in victims:
            if vict != final_victim:
                final_victim.choosen_kill += vict.choosen_kill
                vict.choosen_kill = 0

    mes_start: str = ''
    if final_victim is not None:
        final_victim.choosen_kill -= final_victim.choosen_doctor
        if final_victim.choosen_kill == 0:
            mes.append(
                f'было совершено покушение на {Bot_db.get_username(final_victim.id)}, но доктору удалось его/её спасти')
        elif final_victim.choosen_bodyguard > 0:
            mes.append(f'было совершено покушение на {Bot_db.get_username(final_victim.id)}, но телохранитель закрыл его/её собой')
        elif final_victim.role is Role.immortal and final_victim not in cancelled:
            pass
        else:
            mes_start = 'среди них нет:\n'
    else:
        mes.append('все остались живы')

    for player in players:
        if player.role is Role.immortal and player not in cancelled:
            player.choosen_kill = 0
        elif player.choosen_bodyguard > 0:
            player.choosen_kill = 0
            tuple(filter(lambda guard: guard.role is Role.bodyguard and guard.target is player, players))[0].role = Role.common
        if player.choosen_kill > 0:
            mes.append(f'{mes_start}{Bot_db.get_username(player.id)}, роль - {str(player.role)}')
            mes_start = ''
        elif player.role is not Role.observer:
            alives.append(player)

    if len(mes) == 0:
        mes.append('все остались живы')

    for cancel in cancelled:
        if cancel.choosen_snitch > 0:
            display_team: Team = Team.mafia
        else:
            display_team: Team = cancel.role.get_team()
        mes.append(f'Красотка провела ночь с {str(display_team)}')
    for m in mute:
        mes.append(f'Будет молчать сегодня {Bot_db.get_username(m.id)}')
    mes = ';\n'.join(mes)
    alives = [Bot_db.get_username(i.id) for i in alives]
    return f'🌅 Наступает день. Мирные жители просыпаются и обнаруживают, что сегодня {mes}.' \
           f'\n\nЖители собираются, чтобы обсудить главные вопросы на повестке дня.\n\nВ игре остались: {", ".join(alives)}.'


def m_result_voting(target: PlayerS) -> str:
    if len(target) == 1:
        return f'{Bot_db.get_username(target[0].id)} изгнан(а) по результатам голосования. Он(а) был(а) {str(target[0].role)}.'
    elif len(target) == 0:
        return 'Было принято решение пропустить голосование.'
    else:
        return 'Голоса разделились и никто не был изгнан.'


def m_leaders(leaders: dict) -> str:
    i: int = 1
    board: str = 'Доска лидеров:\n'
    for player in leaders:
        if i > 10:
            break
        board += f'{str(i)}) {player}. Побед: {leaders[player]}.\n'
        i += 1
    return board


def m_list_game(index, games) -> str:
    mes: str = ''
    i: int = 1
    size: int = 8
    for game in games:
        if not game.private:
            if index * size < i <= (index + 1) * size:
                players = [Bot_db.get_username(p.id) for p in game.players if p.role is not Role.observer]
                roles = [str(p.role) for p in game.players if p.role is not Role.observer]
                random.shuffle(roles)
                mes += f'{i}) Игроки: {", ".join(players)}. Роли: {", ".join(roles)}.\n'
            i += 1
    mes += '\nИспользуйте кнопки ниже, чтобы подключиться к игре в качестве наблюдателя.'
    return mes


def m_list_wait(index: int, lists: list) -> str:
    mes: str = ''
    i: int = 1
    size: int = 8
    for w_list in lists:
        if not w_list.private:
            if index * size < i <= (index + 1) * size:
                players = [Bot_db.get_username(p) for p in w_list.players_id]
                roles = [str(role) for role in w_list.game_roles]
                random.shuffle(players)
                mes += f'{i}) Игра ({len(players)}/{str(w_list.size_game)}). Игроки: {", ".join(players)}. Роли: {", ".join(roles)}.\n'
            i += 1
    mes += '\nИспользуйте кнопки ниже, чтобы подключиться к игре.'
    return mes


def m_game_setting(wait_list) -> str:
    roles: list = wait_list.game_roles
    size: int = wait_list.size_game
    private: str = 'приватная' if wait_list.private else 'публичная'

    dict_roles = {}
    [dict_roles.update({role: roles.count(role)}) for role in roles]

    mes = f'Игра на {size} игроков.\n' \
          f'Тип: {private}.\n\n' \
          f'Роли:\n'

    for key, value in dict_roles.items():
        key = str(key)
        mes += f'-{value}- ' + key[0].upper() + key[1:] + '\n'

    return mes


def m_players_in_lobby(wait_list) -> str:
    mes: str = f'В лобби сейчас находятся ({len(wait_list.players_id)}/{wait_list.size_game}):\n'
    players_name: list[str] = []
    for player_id in wait_list.players_id:
        players_name.append(Bot_db.get_username(player_id))
    return mes + '\n'.join(players_name)


def m_time_alert(time_alert: int, phase: int) -> str:
    match phase:
        case 0:
            s_phase = 'вечера'
        case 1:
            s_phase = 'ночи'
        case 2:
            s_phase = 'обсуждения'
        case 3:
            s_phase = 'голосования'
        case _:
            s_phase = '[ошибка]'
    return f'До конца {s_phase} осталось {time_alert}s!'
