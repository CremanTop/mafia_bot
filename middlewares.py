import asyncio

from aiogram import types, Dispatcher
from aiogram.dispatcher.handler import current_handler, CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled


def rate_limit(limit: int = 0):
    def decorator(func):
        setattr(func, 'limit', limit)
        return func

    return decorator


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 3):
        super().__init__()
        self.rate_limit = limit

    async def on_process_message(self, msg: types.Message, data: dict):
        # print('Миддлваря', msg)
        handler = current_handler.get()
        if handler:
            key = getattr(handler, 'limit', self.rate_limit)
            self.rate_limit = key

        # print(handler)
        dp = Dispatcher.get_current()

        try:
            await dp.throttle(key='antiflood_message', rate=self.rate_limit)
        except Throttled as _t:
            # print('throttle')
            raise CancelHandler()

    async def antiflood_message(self, msg: types.Message, throttled: Throttled):
        delta = throttled.rate - throttled.delta
        print('msg')
        if throttled.exceeded_count <= 2:
            await msg.reply('Не спамьте сообщениями! Иначе другие игроки не будут их видеть.')
        await asyncio.sleep(delta)
