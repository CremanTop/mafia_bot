import datetime
import functools
import time
from enum import Enum, auto
from typing import Final, Self, Callable
from colorama import Fore, Style

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from environs import Env

from libs.db import BotDB


class Config:
    __instance: Self = None

    def __init__(self):
        env: Final[Env] = Env()
        env.read_env()  # Методом read_env() читаем файл .env и загружаем из него переменные в окружение

        self.BOT_TOKEN: Final[str] = env('BOT_TOKEN')
        self.password: Final[str] = env('DEFAULT_PASSWORD')

        self.bot: Final[Bot] = Bot(self.BOT_TOKEN)
        self.storage: MemoryStorage = MemoryStorage()
        self.dp: Final[Dispatcher] = Dispatcher(self.bot, storage=self.storage)
        self.Bot_db: Final[BotDB] = BotDB('database')
        self.logger: Logger = Logger(True)

        self.TEST_MODE: bool = True

    @staticmethod
    def get() -> Self:
        if Config.__instance is None:
            Config.__instance = Config()
        return Config.__instance


class Filter:
    only_error: Final[Callable[[str], bool]] = lambda string: str(Logger.Mode.error) in string
    only_info: Final[Callable[[str], bool]] = lambda string: str(Logger.Mode.info) in string
    game: Final[Callable[[str, int], bool]] = lambda string, gid: f'game={gid}' in string

    l_concret_pos: Final[Callable[[str, int, int, int], bool]] = lambda string, pos1, pos2, value: string[pos1:pos2] == str(value)
    day: Final[Callable[[str, int], bool]] = lambda string, day: Filter.l_concret_pos(string, 1, 3, day)
    month: Final[Callable[[str, int], bool]] = lambda string, month: Filter.l_concret_pos(string, 4, 6, month)
    year: Final[Callable[[str, int], bool]] = lambda string, year: Filter.l_concret_pos(string, 7, 11, year)
    hour: Final[Callable[[str, int], bool]] = lambda string, hour: Filter.l_concret_pos(string, 12, 14, hour)
    min: Final[Callable[[str, int], bool]] = lambda string, min: Filter.l_concret_pos(string, 15, 17, min)
    sec: Final[Callable[[str, int], bool]] = lambda string, sec: Filter.l_concret_pos(string, 18, 20, sec)

    @staticmethod
    def frange(s: str, one: str, two: str) -> bool:
        s = tuple(map(int, (s[7:11], s[4:6], s[1:3], s[12:14], s[15:17], s[18:20])))
        o = tuple(map(int, (one[7:11], one[4:6], one[1:3], one[12:14], one[15:17], one[18:20])))
        t = tuple(map(int, (two[7:11], two[4:6], two[1:3], two[12:14], two[15:17], two[18:20])))
        s_time = datetime.datetime(s[0], s[1], s[2], s[3], s[4], s[5])
        o_time = datetime.datetime(o[0], o[1], o[2], o[3], o[4], o[5])
        t_time = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])

        if o_time <= s_time <= t_time:
            return True
        return False

    def __init__(self, original: list[str] = None, sort: bool = False) -> None:
        if original is not None:
            self.list: list[str] = original
            if sort:
                self.sort()
            return

        with open('files/logs.txt', mode='r', encoding='utf8') as file:
            self.list: list[str] = [string.strip() for string in file]

    def sort(self) -> None:

        def compare(one, two):
            if one[7:11] != two[7:11]:
                return int(one[7:11]) - int(two[7:11])
            if one[4:6] != two[4:6]:
                return int(one[4:6]) - int(two[4:6])
            if one[1:3] != two[1:3]:
                return int(one[1:3]) - int(two[1:3])
            if one[12:14] != two[12:14]:
                return int(one[12:14]) - int(two[12:14])
            if one[15:17] != two[15:17]:
                return int(one[15:17]) - int(two[15:17])
            if one[18:20] != two[18:20]:
                return int(one[18:20]) - int(two[18:20])
            return 1

        self.list.sort(key=functools.cmp_to_key(compare))

    def filter(self, comp: Callable, *args) -> Self:
        match len(args):
            case 0:
                self.list = [string for string in self.list if comp(string)]
            case 1:
                self.list = [string for string in self.list if comp(string, args[0])]
            case 2:
                self.list = [string for string in self.list if comp(string, args[0], args[1])]
        return self

    def __handler_double_filter(self, comp1: Callable, comp2: Callable, *args) -> tuple[Self, Self]:
        match len(args):
            case 1:
                filt1 = Filter(self.list).filter(comp1, args[0])
                filt2 = Filter(self.list).filter(comp2)
            case 2:
                filt1 = Filter(self.list).filter(comp1, args[0])
                filt2 = Filter(self.list).filter(comp2, args[1])
            case _:
                filt1 = Filter(self.list).filter(comp1)
                filt2 = Filter(self.list).filter(comp2)
        return filt1, filt2

    def excluded_filter(self, comp1: Callable, comp2: Callable, *args) -> Self:
        filt1, filt2 = self.__handler_double_filter(comp1, comp2, *args)
        return Filter([item for item in filt1 if item not in filt2])

    def addition_filter(self, comp1: Callable, comp2: Callable, *args) -> Self:
        filt1, filt2 = self.__handler_double_filter(comp1, comp2, *args)
        return Filter(self.excluded_filter(comp1, comp2, *args).list + filt2.list, True)

    def __iter__(self) -> Self:
        self.__iter_index = 0
        return self

    def __next__(self) -> str:
        if self.__iter_index >= len(self.list):
            raise StopIteration
        result = self.list[self.__iter_index]
        self.__iter_index += 1
        return result


class Logger:

    class Mode(Enum):
        info = auto()
        error = auto()

        def __str__(self) -> str:
            match self:
                case Logger.Mode.info:
                    return 'INFO'
                case Logger.Mode.error:
                    return 'ERROR'

    def __init__(self, writing: bool, game: int = -1) -> None:
        self.writing: bool = writing
        self.game_id: Final[int] = game

    @staticmethod
    def get_time() -> str:
        clock = time.localtime(time.time())
        return f'{f"{clock.tm_mday}".rjust(2, "0")}.{f"{clock.tm_mon}".rjust(2, "0")}.{clock.tm_year}|{clock.tm_hour}:{f"{clock.tm_min}".rjust(2, "0")}:{f"{clock.tm_sec}".rjust(2, "0")}'

    @staticmethod
    def get_dated_message(message: str) -> str:
        return f'[{Logger.get_time()}] {message}'

    def __print(self, text: str, mode: Mode, form: str = Style.RESET_ALL) -> None:
        gid: str = f'(game={self.game_id})' if self.game_id != -1 else ''

        message: str = f'[{Logger.get_time()}] {mode}: {text} {gid}'
        print(f'{form}{message}')

        if self.writing:
            with open('files/logs.txt', mode='a', encoding='utf8') as file:
                file.write(message + '\n')

    def info(self, text: str) -> None:
        self.__print(text, Logger.Mode.info)

    def error(self, text: str) -> None:
        self.__print(text, Logger.Mode.error, Fore.RED)

    @staticmethod
    def print_with_filter(filt: Filter):
        for i in filt:
            if 'ERROR' in i:
                print(f'{Fore.RED}{i}')
            else:
                print(f'{Style.RESET_ALL}{i}')


#Logger.print_with_filter(Filter().filter(Filter.only_info).filter(Filter.day, 19).filter(Filter.hour, 21))


#Logger.print_with_filter(Filter().excluded_filter(Filter.day, Filter.game, 19, 0))
#Logger.print_with_filter(Filter().filter(Filter.frange, '[19.10.2023|22:40:43]', '[20.10.2023|14:49:18]'))
