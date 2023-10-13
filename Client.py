from enum import Enum


class UserStatus(Enum):
    start = 0  # Начальное состояние, когда пользователю предлагается ввести никнейм
    default = 1  # Стандартное состояние пользователя вне игры
    ingame = 2  # Состояние пользователя в игре
    waiting_code = 3  # Состояние, в котором от пользователя ожидается введение кода приватной игры
    lobby = 4  # Состояние игрока в лобби игры

    @property
    def value(self) -> int:
        """The value of the Enum member."""
        return self._value_
