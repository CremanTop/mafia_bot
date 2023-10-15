import time
from typing import Final, Self

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from environs import Env

from libs.db import BotDB


class Config:
    __instance: Self = None

    def __init__(self):
        env: Final[Env] = Env()  # Создаем экземплят класса Env
        env.read_env()  # Методом read_env() читаем файл .env и загружаем из него переменные в окружение

        self.BOT_TOKEN: Final[str] = env('BOT_TOKEN')
        self.password: Final[str] = env('DEFAULT_PASSWORD')

        self.bot: Final[Bot] = Bot(self.BOT_TOKEN)
        self.storage: MemoryStorage = MemoryStorage()
        self.dp: Final[Dispatcher] = Dispatcher(self.bot, storage=self.storage)
        self.Bot_db: Final[BotDB] = BotDB('database')

        self.TEST_MODE: bool = True

    @staticmethod
    def get() -> Self:
        if Config.__instance is None:
            Config.__instance = Config()
        return Config.__instance

    @staticmethod
    def get_time() -> str:
        clock = time.localtime(time.time())
        return f'{clock.tm_hour}:{f"{clock.tm_min}".rjust(2, "0")}:{f"{clock.tm_sec}".rjust(2, "0")}'

    @staticmethod
    def get_dated_message(message: str) -> str:
        return f'[{Config.get_time()}] {message}'
