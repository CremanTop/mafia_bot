import random

from Role import Role, Team
from main import Bot_db

lex: dict[str, str] = {
    'help_nick': 'Сейчас тебе нужно придумать и написать мне свой никнейм.',
    'help_main': 'Чтобы начать игру, нажми "Найти игру". Что узнать правила, используй /rules.',
    'command_start': 'Добро пожаловать в мафию! Пожалуйста, отправь мне свой никнейм, который будет отображаться в играх.',
    'command_rename': 'Твой никнейм сброшен. Теперь отправь мне новый.',
    'command_rules': 'Итак, в этой игре все игроки делятся на две команды: мирные жители 👔 и мафия 🔪.\nЦель мирных '
                     'жителей: вычислить и изгнать мафию.\nЦель мафии: захватить власть над городом. Для этого '
                     'достаточно, чтобы членов мафии осталось не меньше, чем мирных жителей.\n\nИгра циклично идёт '
                     'через 2 фазы: 🌅 день и 🌃 ночь.\n\nНочью обычные жители спят, а мафия выбирает, '
                     'на кого совершить нападение. Но горожане не так уж беззащитны - у них есть разные роли, '
                     'которые тоже просыпаются ночью и совершают действия: лечат, проводят обыск и тд.\n\nДнём все '
                     'живые игроки просыпаются, видят итоги ночи и в течение 1,5 минут обсуждают, кто может быть '
                     'мафией. Вы можете отправлять текстовые, голосовые сообщения; видеосообщения; стикеры; и их '
                     'увидят остальные игроки (Не спамьте! Сообщения, отправляемые чаще, чем раз в 5 секунд, '
                     'приходить не будут!). По окончанию обсуждения даётся 20 секунд на голосование. Игрок, '
                     'получивший больше всего голосов, изгоняется из игры.\n\nДля получения помощи по отдельным '
                     'ролям, используйте кнопки.',
    'rename_expection': 'Вы не можете установить никнейм, совпадающий с названием одной из ролей! Введите другое имя.',
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
    'button_rules_common': 'Мирный житель',
    'button_rules_ghost': 'Призрак',
    'button_rules_killer': 'Убийца',
    'button_rules_doctor': 'Доктор',
    'button_rules_sheriff': 'Шериф',
    'button_rules_beauty': 'Красотка',
    'button_rules_godfather': 'Крёстный отец',
    'button_rules_immortal': 'Бессмертный',
    'button_rules_medium': 'Медиум',
    'general_rules': 'День: все роли обсуждают, кто может быть мафией и выгоняют голосованием подозрительных игроков.\n\n',
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
    'rules_beauty': 'Ночь: выбирает, чьё действие этой ночью будет отменено (на шерифа не распространяется). '
                    'Примеры: если был выбран доктор, то его лечение не засчитывается (убирает одно очко лечения); '
                    'если был выбран убийца, то убийство не происходит (убирает одно очко смерти).\nПримечание: если '
                    'убийц несколько, то красотка отвлекает только одного, другие всё равно совершают убийство.',
    'rules_godfather': 'Ночь: просыпается вместе с убийцами, может с ними обсуждать покушение, но не голосует за '
                       'жертву. Вместо этого выбирает игрока, который днём будет молчать и не примет участия в '
                       'голосовании.',
    'rules_immortal': 'Не может быть убит. Только игнан дневным голосованием.',
    'rules_medium': 'Ночь: выбирает одного призрака, с которым может общаться до наступления дня. Медиум может отправлять любые сообщения, призрак - только текстовые.',
    'team': 'Команда:',
    'waiting': 'Ищем для вас соперников. Как только наберётся достаточно игроков, мы начнём.',
    'evening_common': '🌄 Наступает вечер. На улицу выходят разные сомнительные личности.',
    'evening_beauty': '🌄 Наступает вечер. Пришло время выбрать, чьё действие этой ночью будет отменено.',
    'evening_medium': '🌄 Наступает вечер. Пришло время выбрать, с каким призраком связаться.',
    'night_common': '🌃 Наступает ночь. Мирные жители засыпают, просыпается мафия...',
    'night_killer': '🌃 Наступает ночь. Теперь, когда мирные жители уснули, пришло время выбрать, кто из них не увидит завтрашний день...',
    'night_doctor': '🌃 Наступает ночь. Бригада скорой помощи выезжает, но приехать ко всем вы не успеете. Пришло время выбрать, кто сегодня будет спасён.',
    'night_sheriff': '🌃 Наступает ночь. Убийца прячется под личиной мирного жителя. Пришло время проверить кого-то из них, чтобы вычислить его.',
    'night_godfather': '🌃 Наступает ночь. Пришло время выбрать, кто днём не сможет участвовать в обсуждении и голосовать.',
    'start_voting': 'Обсуждение закончено. Пришло время выбрать, кто должен быть изгнан.',
    'vote': 'Вы проголосовали за ',
    'already_voted': 'Вы уже проголосовали!',
    'choose': 'Вы выбрали ',
    'wait': '. Ожидание выборов других игроков.',
    'his_role': 'Его/её роль - ',
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
    'eq_old_tg': 'Вы не можете выбирать одного и того же игрока несколько раз подряд!'
}


def m_setup_nick(nick: str):
    return f'Прекрасно, {nick}, теперь мы можем приступить к игре. Если ты не знаешь правила, то сейчас я всё ' \
           f'объясню.\n\n{lex["command_rules"]}\n\nНажми на кнопку "Найти игру", когда захочешь поиграть. '


def m_start_game(players: list):
    roles = []
    player_names = []
    for player in players:
        player_names.append(Bot_db.get_username(player.id))
        roles.append(str(player.role))
    random.shuffle(roles)
    return f'Игра началась! Добро пожаловать {", ".join(player_names)}. \n\nВ последнее время в маленьком городе неспокойно. Страшные вещи происходят по ночам.\n\nРоли: {", ".join(roles)}.'


def m_player_role(player):
    role = player.role
    task = ''
    if role is Role.killer:
        task = 'убивать мирных жителей по ночам и не вызывать подозрений днём.'
    elif role is Role.common:
        task = 'найти убийцу и изгнать его, чтобы прекратить эти преступления.'
    elif role is Role.doctor:
        task = 'догадаться, кого выбрала сегодня мафия, и вылечить его.'
    elif role is Role.sheriff:
        task = 'найти убийцу. Вы можете провести обыск у любого игрока и узнать, является ли он мафией.'
    elif role is Role.beauty:
        task = 'выбирать игрока, чьё действие этой ночью будет отменено.'
    elif role is Role.godfather:
        task = 'выбирать игрока, который днём будет молчать и не примет участие в голосовании.'
    elif role is Role.immortal:
        task = 'найти убийцу и изгнать его. Вы не можете быть убиты ночью.'
    elif role is Role.medium:
        task = 'общаться с призраками, чтобы больше узнать о потаённой стороне игры.'
    return f'Вы - {str(role)}. Ваша задача {task}'


def m_team_killers(this, players):
    team = []
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


def m_result_night(players: list):
    victims = []
    cancelled = []
    mute = []
    alives = []
    mes = []
    for player in players:
        if player.choosen_beauty > 0:
            cancelled.append(player)
        if player.choosen_kill > 0:
            victims.append(player)
        if player.choosen_godfather > 0:
            mute.append(player)

    final_victim = None
    if len(victims) > 0:
        max_point = 0
        prior_victim = []
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

    mes_start = ''
    if final_victim is not None:
        final_victim.choosen_kill -= final_victim.choosen_doctor
        if final_victim.choosen_kill == 0:
            mes.append(
                f'было совершено покушение на {Bot_db.get_username(final_victim.id)}, но доктору удалось его/её спасти')
        elif final_victim.role is Role.immortal and final_victim not in cancelled:
            pass
        else:
            mes_start = 'среди них нет:\n'
    else:
        mes.append('все остались живы')

    for player in players:
        if player.role is Role.immortal and player not in cancelled:
            player.choosen_kill = 0
        if player.choosen_kill > 0:
            mes.append(f'{mes_start}{Bot_db.get_username(player.id)}, роль - {str(player.role)}')
            mes_start = ''
        elif player.role is not Role.observer:
            alives.append(player)

    if len(mes) == 0:
        mes.append('все остались живы')

    for cancel in cancelled:
        mes.append(f'Красотка провела ночь с {str(cancel.role.get_team())}')
    for m in mute:
        mes.append(f'Будет молчать сегодня {Bot_db.get_username(m.id)}')
    mes = ';\n'.join(mes)
    alives = [Bot_db.get_username(i.id) for i in alives]
    return f'🌅 Наступает день. Мирные жители просыпаются и обнаруживают, что сегодня {mes}.' \
           f'\n\nЖители собираются, чтобы обсудить главные вопросы на повестке дня.\n\nВ игре остались: {", ".join(alives)}.'


def m_result_voting(target: list):
    if len(target) == 1:
        return f'{Bot_db.get_username(target[0].id)} изгнан(а) по результатам голосования. Он(а) был(а) {str(target[0].role)}.'
    elif len(target) == 0:
        return 'Было принято решение пропустить голосование.'
    else:
        return 'Голоса разделились и никто не был изгнан.'


def m_leaders(leaders: dict):
    i = 1
    board = 'Доска лидеров:\n'
    for player in leaders:
        if i > 10:
            break
        board += f'{str(i)}) {player}. Побед: {leaders[player]}.\n'
        i += 1
    return board


def m_list_game(index, games):
    mes = ''
    i = 1
    size = 8
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


def m_list_wait(index, lists):
    mes = ''
    i = 1
    size = 8
    for list in lists:
        if not list.private:
            if index * size < i <= (index + 1) * size:
                players = [Bot_db.get_username(p) for p in list.players_id]
                roles = [str(role) for role in list.game_roles]
                random.shuffle(players)
                mes += f'{i}) Игра ({len(players)}/{str(list.size_game)}). Игроки: {", ".join(players)}. Роли: {", ".join(roles)}.\n'
            i += 1
    mes += '\nИспользуйте кнопки ниже, чтобы подключиться к игре.'
    return mes


def m_game_setting(wait_list):
    roles = wait_list.game_roles
    size = wait_list.size_game
    private = 'приватная' if wait_list.private else 'публичная'

    dict_roles = {}
    [dict_roles.update({role: roles.count(role)}) for role in roles]

    mes = f'Игра на {size} игроков.\n' \
          f'Тип: {private}.\n\n' \
          f'Роли:\n'

    for key, value in dict_roles.items():
        key = str(key)
        mes += f'-{value}- ' + key[0].upper() + key[1:] + '\n'

    return mes
