from enum import Enum

from aiogram.types import MediaGroup
from aiogram.types.base import TelegramObject
from aiogram.utils.exceptions import WrongFileIdentifier, BotBlocked, BadRequest

from db import BotDB
from main import bot


class FuncEnum(Enum):
    text = bot.send_message
    keyboard = bot.send_message
    media = bot.send_media_group
    voice = bot.send_voice
    video = bot.send_video_note
    sticker = bot.send_sticker


class Predicates:
    all = lambda user: True  # Подходят все
    if_name = lambda user: user[2] != 'default'  # Подходят те, у кого введено имя
    if_not_in_game = lambda user: user[3] != 1  # Подходят те, кто сейчас не в игре


async def send_message(chat_id: int,
                       func,
                       text: str = None,
                       keyboard: TelegramObject = None,
                       media: MediaGroup = None,
                       sticker: str = None,
                       voice: str = None) -> None:
    """Отправляет сообщение указанному пользователю по id"""
    try:
        if voice is not None:
            if func is FuncEnum.voice:
                await func(chat_id=chat_id, voice=voice, reply_markup=keyboard, caption=text)
            elif func is FuncEnum.video:
                await func(chat_id=chat_id, video_note=voice, reply_markup=keyboard)
        elif media is not None:
            await func(chat_id=chat_id, media=media)
        elif sticker is not None:
            await func(chat_id=chat_id, sticker=sticker)
        elif text is not None:
            await func(chat_id=chat_id, text=text, reply_markup=keyboard)
        # print('Отправлено ' + str(chat))
    except WrongFileIdentifier:
        print('Неправильный идентификатор файла!')
    except BadRequest:
        #print('Неправильный идентификатор файла!')
        pass
    except BotBlocked:
        print('Бот заблокирован у ' + str(chat_id))
    except Exception:
        print('Ошибка отправки для ' + str(chat_id))


async def mailing(bot_db: BotDB,
                  func,
                  pred=None,
                  text: str = None,
                  keyboard: TelegramObject = None,
                  media: MediaGroup = None,
                  sticker: str = None,
                  voice: str = None) -> None:
    """Отправляет сообщение всем пользователям в базе данных"""
    for user in bot_db.get_users():
        chat_id = user[1]
        if pred is not None:
            if pred(user):
                await send_message(chat_id, func, text=text, keyboard=keyboard, media=media, sticker=sticker, voice=voice)
        else:
            await send_message(chat_id, func, text=text, keyboard=keyboard, media=media, sticker=sticker, voice=voice)


def media_generate(text: str = None, *photos) -> MediaGroup:
    mediaGroup = MediaGroup()
    begin = 0
    if text is not None:
        mediaGroup.attach({'media': photos[0], 'type': 'photo', 'caption': text})
        begin = 1
    for i in range(begin, len(photos)):
        mediaGroup.attach({'media': photos[i], 'type': 'photo'})
    return mediaGroup
