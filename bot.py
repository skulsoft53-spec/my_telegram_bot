import asyncio
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import yt_dlp

# ----------------- WEB SERVER (Render) -----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ----------------- TELEGRAM BOT -----------------

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

executor = ThreadPoolExecutor(max_workers=3)
semaphore = asyncio.Semaphore(3)


# ----------------- DOWNLOAD FUNCTIONS -----------------

def download_video_sync(url, filename):
    ydl_opts = {
        "outtmpl": filename,
        "format": "mp4",
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_audio_sync(url, filename_base):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filename_base,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# ----------------- COMMANDS -----------------

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Отправь TikTok ссылку\n\n"
        "📹 Я скачаю видео\n"
        "🎵 и сразу музыку из него"
    )


@dp.message()
async def handler(message: types.Message):

    url = message.text

    if "tiktok.com" not in url:
        await message.answer("❌ Это не TikTok ссылка")
        return

    await message.answer("📥 Скачиваю видео и музыку...")

    base = f"{message.from_user.id}_{int(time.time())}"
    video_file = base + ".mp4"
    audio_file = base + ".mp3"

    try:
        async with semaphore:
            loop = asyncio.get_event_loop()

            # 📹 видео
            await loop.run_in_executor(
                executor,
                download_video_sync,
                url,
                video_file
            )

            # 🎵 музыка (из этого же видео)
            await loop.run_in_executor(
                executor,
                download_audio_sync,
                url,
                base
            )

        video = types.FSInputFile(video_file)
        audio = types.FSInputFile(audio_file)

        await message.answer_video(video, caption="📹 Видео готово")
        await message.answer_audio(audio, caption="🎵 Музыка из видео")

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
