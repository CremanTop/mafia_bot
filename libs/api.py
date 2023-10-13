import asyncio
import json
from enum import Enum
from typing import Final, Callable, Optional

from aiogram.types import MediaGroup, Message
from aiogram.types.base import TelegramObject
from aiogram.utils.exceptions import WrongFileIdentifier, BotBlocked, BadRequest

from Config import Config
from libs.db import BotDB

config: Final[Config] = Config.get()
bot = config.bot


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
                       func: Callable | FuncEnum,
                       text: Optional[str] = None,
                       keyboard: Optional[TelegramObject] = None,
                       media: Optional[MediaGroup] = None,
                       sticker: Optional[str] = None,
                       voice: Optional[str] = None
                       ) -> None:
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
        # print('Неправильный запрос!')
        pass
    except BotBlocked:
        print('Бот заблокирован у ' + str(chat_id))
    except Exception:
        print('Ошибка отправки для ' + str(chat_id))


async def mailing(bot_db: BotDB,
                  func: Callable,
                  pred: Callable[[tuple], bool] = lambda x: True,
                  text: Optional[str] = None,
                  keyboard: Optional[TelegramObject] = None,
                  media: Optional[MediaGroup] = None,
                  sticker: Optional[str] = None,
                  voice: Optional[str] = None
                  ) -> None:
    """Отправляет сообщение всем пользователям в базе данных"""
    for user in bot_db.get_users():
        chat_id = user[1]
        if pred(user):
            asyncio.create_task(
                send_message(chat_id, func, text=text, keyboard=keyboard, media=media, sticker=sticker, voice=voice))


class MGroup:
    def __init__(self, path: str, name: str, mid: str) -> None:
        self.path: str = path
        self.name: str = name
        self.id: str = mid

        media_def = {
            'photo': [],
            'video': [],
            'text': ''
        }

        data: dict = JFile.read_file(path, name)
        groups: dict = data.get('media')

        if groups.get(mid) is None:
            groups[mid] = media_def.copy()
            JFile.write_file(path, name, data)

    def _update(self, func_up: Callable, m_type: str, value: str):
        data: dict = JFile.read_file(self.path, self.name)
        media_group = data['media'][self.id]
        media_group = func_up(media_group, m_type, value)
        data['media'][self.id] = media_group
        JFile.write_file(self.path, self.name, data)

    def add_media(self, media_type: str, media: str) -> None:
        def func(group: dict, m_type: str, val: str) -> dict:
            if not group[m_type].__contains__(val):
                group[m_type].append(val)
            return group

        self._update(func, media_type, media)

    def add_photo(self, photo: str) -> None:
        self.add_media('photo', photo)

    def add_video(self, video: str) -> None:
        self.add_media('video', video)

    def set_text(self, text: str) -> None:
        def func(group: dict, m_type: str, val: str) -> dict:
            group[m_type] = val
            return group

        self._update(func, 'text', text)


class JFile:
    def __init__(self, path: str, name: str) -> None:
        self.path: str = path
        self.name: str = name

        if len(self.read_file(path, name)) == 0:
            self._def_value(path, name)

    @staticmethod
    def write_file(path: str, name: str, data: dict) -> None:
        with open(f'{path}/{name}.json', 'w') as w_file:
            json.dump(data, w_file, indent=4)

    @staticmethod
    def read_file(path: str, name: str) -> dict:
        try:
            with open(f'{path}/{name}.json', 'r') as file:
                data: dict = json.load(file)
                return data
        except FileNotFoundError:
            JFile._def_value(path, name)
            return JFile.read_file(path, name)

    @staticmethod
    def _def_value(path: str, name: str) -> None:
        init_dict: dict = {
            'media': {}
        }
        JFile.write_file(path, name, init_dict)

    def read(self) -> dict:
        return self.read_file(self.path, self.name)

    def write(self, data: dict) -> None:
        self.write_file(self.path, self.name, data)

    def get_media_group(self, id_media: str) -> MGroup:
        return MGroup(self.path, self.name, id_media)


def media_generate(group: MGroup) -> MediaGroup:
    final_mediaGroup = MediaGroup()
    begin = 0

    medias: dict = JFile.read_file(group.path, group.name).get('media').get(group.id)
    media_id: list[tuple[str, str]] = []
    types = ('photo', 'video')
    for ty in types:
        for media in medias.get(ty):
            media_id.append((media, ty))
    caption = medias.get('text')
    if caption:
        if caption[:9] == 'Рассылка:':
            caption = caption[9:].strip()
        final_mediaGroup.attach({'media': media_id[0][0], 'type': media_id[0][1], 'caption': caption})
        begin = 1
    for i in range(begin, len(media_id)):
        final_mediaGroup.attach({'media': media_id[i][0], 'type': media_id[i][1]})
    return final_mediaGroup


path: str = '../files'
name: str = 'mediaGroups'


async def media_collector(message: Message) -> MGroup:
    gid = message.media_group_id
    media, m_type = '', ''
    global send
    send = True

    if len(message.photo) > 0:
        media = message.photo[0].file_id
        m_type = 'photo'
    elif message.video:
        media = message.video.file_id
        m_type = 'video'

    if gid:
        media_group: MGroup = JFile(path, name).get_media_group(gid)
        media_group.add_media(m_type, media)
        if message.caption:
            media_group.set_text(message.caption)
        await message.answer('media uploaded')

        return media_group
