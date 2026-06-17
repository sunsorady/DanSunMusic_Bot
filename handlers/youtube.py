import asyncio
import datetime
import logging
import os

from aiogram import types, Router, F
from aiogram.types import FSInputFile
from moviepy import VideoFileClip, AudioFileClip

import keyboards as kb
import messages as bm
from config import OUTPUT_DIR
from handlers.user import update_info
from helper import report_error
from main import bot, db, send_analytics

MAX_FILE_SIZE = 500 * 1024 * 1024

router = Router()


def get_ydl_opts(output_path):
    return {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'force_generic_extractor': False,
    }


def download_video_ytdlp(url, output_path):
    import yt_dlp
    opts = get_ydl_opts(output_path)
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=True)


def get_video_info(url):
    import yt_dlp
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


@router.message(F.text.regexp(r"(https?://(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/\S+)"))
@router.business_message(F.text.regexp(r"(https?://(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/\S+)"))
async def download_video(message: types.Message):
    business_id = message.business_connection_id

    await send_analytics(user_id=message.from_user.id, chat_type=message.chat.type, action_name="youtube_video")

    bot_url = f"t.me/{(await bot.get_me()).username}"
    file_type = "video"

    url = message.text
    try:
        if business_id is None:
            react = types.ReactionTypeEmoji(emoji="👨‍💻")
            await message.react([react])

        info = await asyncio.get_event_loop().run_in_executor(None, get_video_info, url)

        video_id = info.get('id', 'unknown')
        title = info.get('title', 'YouTube Video')
        watch_url = info.get('webpage_url', url)

        name = f"{video_id}_youtube_video.mp4"
        video_file_path = os.path.join(OUTPUT_DIR, name)

        post_caption = title

        user_captions = await db.get_user_captions(message.from_user.id)

        db_file_id = await db.get_file_id(watch_url)

        if db_file_id:
            if business_id is None:
                await bot.send_chat_action(message.chat.id, "upload_video")

            await message.answer_video(video=db_file_id[0][0],
                                       caption=bm.captions(user_captions, post_caption, bot_url),
                                       reply_markup=kb.return_audio_download_keyboard("yt",
                                                                                      watch_url) if business_id is None else None,
                                       parse_mode="HTMl")
            return

        await asyncio.get_event_loop().run_in_executor(None, download_video_ytdlp, url, video_file_path)

        if not os.path.exists(video_file_path):
            raise Exception("Downloaded file not found")

        file_size = os.path.getsize(video_file_path)

        if file_size < MAX_FILE_SIZE:
            video_clip = VideoFileClip(video_file_path)
            width, height = video_clip.size

            if business_id is None:
                await bot.send_chat_action(message.chat.id, "upload_video")

            sent_message = await message.answer_video(video=FSInputFile(video_file_path),
                                                      width=width,
                                                      height=height,
                                                      caption=bm.captions(user_captions, post_caption, bot_url),
                                                      reply_markup=kb.return_audio_download_keyboard("yt",
                                                                                                     watch_url) if business_id is None else None)
            file_id = sent_message.video.file_id

            await db.add_file(watch_url, file_id, file_type)
            await asyncio.sleep(5)
            os.remove(video_file_path)

        else:
            os.remove(video_file_path)
            if business_id is None:
                react = types.ReactionTypeEmoji(emoji="👎")
                await message.react([react])

            await message.reply("The video is too large.")

    except Exception as e:
        await report_error(bot, e, "YouTube Video", message)
        if business_id is None:
            react = types.ReactionTypeEmoji(emoji="👎")
            await message.react([react])

        await message.reply("Something went wrong :(\nPlease try again later.")

    await update_info(message)


@router.callback_query(F.data.startswith('yt_audio_'))
async def download_audio(call: types.CallbackQuery):
    bot_url = f"t.me/{(await bot.get_me()).username}"

    url = call.data.split('_')[2]

    try:
        info = await asyncio.get_event_loop().run_in_executor(None, get_video_info, url)
        video_id = info.get('id', 'unknown')
        title = info.get('title', 'YouTube Audio')

        name = f"{video_id}_youtube_audio.mp3"
        audio_file_path = os.path.join(OUTPUT_DIR, name)

        audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_file_path.replace('.mp3', '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        import yt_dlp
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([url])

        final_path = audio_file_path
        if not os.path.exists(final_path):
            base = audio_file_path.replace('.mp3', '')
            for ext in ['mp3', 'm4a', 'webm', 'opus']:
                candidate = f"{base}.{ext}"
                if os.path.exists(candidate):
                    if ext != 'mp3':
                        os.rename(candidate, final_path)
                    break

        if not os.path.exists(final_path):
            raise Exception("Audio file not found after download")

        file_size = os.path.getsize(final_path)

        if file_size > MAX_FILE_SIZE:
            os.remove(final_path)
            await call.message.reply("The audio file is too large.")
            return

        audio_duration = AudioFileClip(final_path)
        duration = round(audio_duration.duration)

        await call.answer()
        await bot.send_chat_action(call.message.chat.id, "upload_voice")

        await call.message.answer_audio(audio=FSInputFile(final_path), title=title,
                                        duration=duration,
                                        caption=bm.captions(None, None, bot_url),
                                        parse_mode="HTML")

        await asyncio.sleep(5)
        os.remove(final_path)

    except Exception as e:
        await report_error(bot, e, "YouTube Audio", call.message)
        await call.answer("Download failed", show_alert=True)


@router.message(F.text.regexp(r'(https?://)?(music\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+'))
@router.business_message(F.text.regexp(r'(https?://)?(music\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+'))
async def download_music(message: types.Message):
    business_id = message.business_connection_id

    await send_analytics(user_id=message.from_user.id, chat_type=message.chat.type, action_name="youtube_audio")

    bot_url = f"t.me/{(await bot.get_me()).username}"
    url = message.text

    if business_id is None:
        react = types.ReactionTypeEmoji(emoji="👨‍💻")
        await message.react([react])
    try:
        download_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{download_time}_youtube_audio.mp3"

        info = await asyncio.get_event_loop().run_in_executor(None, get_video_info, url)
        title = info.get('title', 'YouTube Audio')

        audio_file_path = os.path.join(OUTPUT_DIR, name)
        audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_file_path.replace('.mp3', '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        import yt_dlp
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([url])

        final_path = audio_file_path
        if not os.path.exists(final_path):
            base = audio_file_path.replace('.mp3', '')
            for ext in ['mp3', 'm4a', 'webm', 'opus']:
                candidate = f"{base}.{ext}"
                if os.path.exists(candidate):
                    if ext != 'mp3':
                        os.rename(candidate, final_path)
                    break

        if not os.path.exists(final_path):
            raise Exception("Audio file not found after download")

        file_size = os.path.getsize(final_path)

        if file_size > MAX_FILE_SIZE:
            os.remove(final_path)
            await message.reply("The audio file is too large.")
            return

        audio_duration = AudioFileClip(final_path)
        duration = round(audio_duration.duration)

        if business_id is None:
            await bot.send_chat_action(message.chat.id, "upload_voice")

        await message.answer_audio(audio=FSInputFile(final_path), title=title,
                                   duration=duration,
                                   caption=bm.captions(None, None, bot_url),
                                   parse_mode="HTML")

        await asyncio.sleep(5)
        os.remove(final_path)

    except Exception as e:
        await report_error(bot, e, "YouTube Audio", message)
        if business_id is None:
            react = types.ReactionTypeEmoji(emoji="👎")
            await message.react([react])
        await message.reply("Something went wrong :(\nPlease try again later.")

    await update_info(message)
