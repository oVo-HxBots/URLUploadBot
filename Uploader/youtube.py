# MIT License

# Copyright (c) 2022 Hash Minner

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

import os
from urllib.parse import urlparse
import wget
import asyncio

from opencc import OpenCC
from youtube_dl import YoutubeDL
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram import Client, filters

if bool(os.environ.get("WEBHOOK")):
    from Uploader.config import Config
else:
    from sample_config import Config

from Uploader.functions.help_ytdl import get_file_extension_from_url, get_resolution

YTDL_REGEX = (r"^((?:https?:)?\/\/)")
s2tw = OpenCC('s2tw.json').convert


@Client.on_callback_query(filters.regex("^ytdl_audio$"))
async def callback_query_ytdl_audio(_, callback_query):
    try:
        url = callback_query.message.reply_to_message.text
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': '%(title)s - %(extractor)s-%(id)s.%(ext)s',
            'writethumbnail': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            message = callback_query.message
            await message.reply_chat_action(enums.ChatAction.TYPING)
            info_dict = ydl.extract_info(url, download=False)
            # download
            await callback_query.edit_message_text("**Downloading audio...**")
            ydl.process_info(info_dict)
            # upload
            audio_file = ydl.prepare_filename(info_dict)
            task = asyncio.create_task(send_audio(message, info_dict,
                                                  audio_file))
            while not task.done():
                await asyncio.sleep(3)
                await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
            await message.reply_chat_action(enums.ChatAction.CANCEL)
            await message.delete()
    except Exception as e:
        await message.reply_text(e)
    await callback_query.message.reply_to_message.delete()
    await callback_query.message.delete()

    async def send_audio(message: Message, info_dict, audio_file):
        basename = audio_file.rsplit(".", 1)[-2]
        if info_dict['ext'] == 'webm':
            audio_file_weba = f"{basename}.weba"
            os.rename(audio_file, audio_file_weba)
            audio_file = audio_file_weba
        thumbnail_url = info_dict['thumbnail']
        thumbnail_file = f"{basename}.{get_file_extension_from_url(thumbnail_url)}"
        download_location = f"{Config.DOWNLOAD_LOCATION}/{message.from_user.id}.jpg"
        thumb = download_location if os.path.isfile(
            download_location) else None
        webpage_url = info_dict['webpage_url']
        title = s2tw(info_dict['title'])
        caption = f'<b><a href=\"{webpage_url}\">{title}</a></b>'
        duration = int(float(info_dict['duration']))
        performer = s2tw(info_dict['uploader'])
        await message.reply_audio(audio_file, caption=caption, duration=duration, performer=performer, title=title, parse_mode=enums.ParseMode.HTML, thumb=thumb)

        os.remove(audio_file)
        os.remove(thumbnail_file)


@Client.on_callback_query(filters.regex("^ytdl_video$"))
async def callback_query_ytdl_video(_, callback_query):
    try:
        # url = callback_query.message.text
        url = callback_query.message.reply_to_message.text
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': '%(title)s - %(extractor)s-%(id)s.%(ext)s',
            'writethumbnail': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            message = callback_query.message
            await message.reply_chat_action(enums.ChatAction.TYPING)
            info_dict = ydl.extract_info(url, download=False)
            # download
            await callback_query.edit_message_text("**Downloading video...**")
            ydl.process_info(info_dict)
            # upload
            video_file = ydl.prepare_filename(info_dict)
            task = asyncio.create_task(send_video(message, info_dict,
                                                  video_file))
            while not task.done():
                await asyncio.sleep(3)
                await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
            await message.reply_chat_action(enums.ChatAction.CANCEL)
            await message.delete()
    except Exception as e:
        await message.reply_text(e)
    await callback_query.message.reply_to_message.delete()
    await callback_query.message.delete()

    async def send_video(message: Message, info_dict, video_file):
        basename = video_file.rsplit(".", 1)[-2]
        thumbnail_url = info_dict['thumbnail']
        thumbnail_file = f"{basename}.{get_file_extension_from_url(thumbnail_url)}"
        download_location = f"{Config.DOWNLOAD_LOCATION}/{message.from_user.id}.jpg"
        thumb = download_location if os.path.isfile(
            download_location) else None
        webpage_url = info_dict['webpage_url']
        title = s2tw(info_dict['title'])
        caption = f'<b><a href=\"{webpage_url}\">{title}</a></b>'
        duration = int(float(info_dict['duration']))
        width, height = get_resolution(info_dict)
        await message.reply_video(video_file, caption=caption, duration=duration, width=width, height=height, parse_mode=enums.ParseMode.HTML, thumb=thumb)

        os.remove(video_file)
        os.remove(thumbnail_file)
