from enum import Enum, auto


class Team(Enum):
    citizen = auto()
    mafia = auto()
    ghost = auto()

    def __str__(self):
        if self is Team.citizen:
            return 'горожане'
        elif self is Team.mafia:
            return 'мафия'
        elif self is Team.ghost:
            return 'нет команды'
        else:
            return '[ошибка]'


class Role(Enum):
    observer = auto()
    common = auto()
    killer = auto()
    doctor = auto()
    sheriff = auto()
    beauty = auto()
    godfather = auto()
    immortal = auto()
    medium = auto()

    def __str__(self):
        if self is Role.common:
            return 'мирный житель 👔'
        elif self is Role.killer:
            return 'убийца 🔪'
        elif self is Role.doctor:
            return 'доктор 💊'
        elif self is Role.sheriff:
            return 'шериф 🚨'
        elif self is Role.beauty:
            return 'красотка 💋'
        elif self is Role.godfather:
            return 'крёстный отец 🌹'
        elif self is Role.immortal:
            return 'бессмертный ♾'
        elif self is Role.medium:
            return 'медиум 🪬'
        else:
            return '[ошибка]'

    def get_team(self):
        if self in (Role.common, Role.doctor, Role.sheriff, Role.beauty, Role.immortal, Role.medium):
            return Team.citizen
        elif self in (Role.killer, Role.godfather):
            return Team.mafia
        elif self is Role.observer:
            return Team.ghost
        else:
            return None

# s = 'Я строка, новая строкаааа'
# l_s = list(s)
# random.shuffle(l_s)
# s = ''.join(l_s).strip()
#
# print(s)
