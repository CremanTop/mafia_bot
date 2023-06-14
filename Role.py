from enum import Enum, auto


class Team(Enum):
    citizen = auto()
    mafia = auto()
    ghost = auto()

    def __str__(self):
        match self:
            case Team.citizen:
                return 'горожане 🟢'
            case Team.mafia:
                return 'мафия 🔴'
            case Team.ghost:
                return 'нет команды'
            case _:
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
    barman = auto()
    don = auto()

    def __str__(self):
        match self:
            case Role.common:
                return 'мирный житель 👔'
            case Role.killer:
                return 'убийца 🔪'
            case Role.doctor:
                return 'доктор 💊'
            case Role.sheriff:
                return 'шериф 🚨'
            case Role.beauty:
                return 'красотка 💋'
            case Role.godfather:
                return 'крёстный отец 🌹'
            case Role.immortal:
                return 'бессмертный ♾'
            case Role.medium:
                return 'медиум 🪬'
            case Role.barman:
                return 'бармен 🍺'
            case Role.observer:
                return 'призрак 👻'
            case Role.don:
                return 'дон 💵'
            case _:
                return '[ошибка]'

    def get_team(self):
        match self:
            case Role.common | Role.doctor | Role.sheriff | Role.beauty | Role.immortal | Role.medium:
                return Team.citizen
            case Role.killer | Role.godfather | Role.barman | Role.don:
                return Team.mafia
            case Role.observer:
                return Team.ghost
            case _:
                return None
