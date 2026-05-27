import asyncio
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from flask import Flask

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile

import yt_dlp

# ----------------- FLASK (Render Web Service) -----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ----------------- BOT -----------------

TOKEN = os.getenv("TOKEN")  # ⚠️ положи TOKEN в Render ENV

bot = Bot(token=TOKEN)
dp = Dispatcher()

executor = ThreadPoolExecutor(max_workers=3)
semaphore = asyncio.Semaphore(2)


# ----------------- FILE CHECK -----------------

def wait_file(path, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return True
        time.sleep(0.5)
    return False


# ----------------- DOWNLOAD VIDEO -----------------

def download_video(url, filename):
    ydl_opts = {
        "outtmpl": filename,
        "format": "best",  # стабильнее чем mp4
        "noplaylist": True,
        "quiet": True,
        "retries": 10,
        "socket_timeout": 30,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# ----------------- DOWNLOAD AUDIO -----------------

def download_audio(url, filename_base):
    ydl_opts = {
        "outtmpl": filename_base,
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "retries": 10,
        "socket_timeout": 30,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# ----------------- START -----------------

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Отправь TikTok ссылку\n\n"
        "📹 Я скачаю видео\n"
        "🎵 и отдельно музыку"
    )


# ----------------- MAIN HANDLER -----------------

@dp.message()
async def handler(message: types.Message):

    url = message.text

    if "tiktok.com" not in url:
        await message.answer("❌ Это не TikTok ссылка")
        return

    await message.answer("📥 Скачиваю...")

    base = f"{message.from_user.id}_{int(time.time())}"
    video_file = base + ".mp4"
    audio_file = base + ".mp3"

    try:
        async with semaphore:
            loop = asyncio.get_event_loop()

            # 📹 VIDEO
            await loop.run_in_executor(
                executor,
                download_video,
                url,
                video_file
            )

            # 🎵 AUDIO
            await loop.run_in_executor(
                executor,
                download_audio,
                url,
                base
            )

        # ⏳ защита от Render lag
        if not wait_file(video_file):
            await message.answer("❌ Видео не скачалось")
            return

        if not wait_file(audio_file):
            await message.answer("⚠️ Музыка не найдена")

        video = FSInputFile(video_file)
        audio = FSInputFile(audio_file)

        await asyncio.sleep(1)
        await message.answer_video(video, caption="📹 Видео готово")
        await message.answer_audio(audio, caption="🎵 Музыка")

    except Exception as e:
        await message.answer(f"❌ Ошибка:\n{e}")

    finally:
        for f in [video_file, audio_file]:
            if os.path.exists(f):
                os.remove(f)


# ----------------- MAIN -----------------

async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(main())
