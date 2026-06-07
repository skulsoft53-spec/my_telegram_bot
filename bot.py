import asyncio
import os
import random
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.custom import Button

API_ID = 39163151
API_HASH = '3c0e92ad7b268eca1eb1a33a9baa7d1d'
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# Заглушка для Render
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

# Клиент для авторизации (бот)
auth_client = TelegramClient(
    os.path.join(SESSION_DIR, 'bot_session'),
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

# Клиент для твоего аккаунта
user_client = None
user_auth_data = {}
active_attacks = {}

def get_digit_keyboard():
    return [
        [Button.inline("1"), Button.inline("2"), Button.inline("3")],
        [Button.inline("4"), Button.inline("5"), Button.inline("6")],
        [Button.inline("7"), Button.inline("8"), Button.inline("9")],
        [Button.inline("0"), Button.inline("◀️"), Button.inline("✅")]
    ]

def get_clear_keyboard():
    return Button.clear()

# ========== ВСЕ ОСКОРБЛЕНИЯ С ФАНТАЗИЕЙ ==========
lines_list = [
"я твою мать трахал в очереди за хлебом, она ещё благодарила что не с пустыми руками",
"у твоего отца сперма была бракованной, поэтому ты получился кривым даже на мораль",
"твоя мать сосёт у ментов за справку о несудимости для меня",
"я заставил твою мать танцевать на капоте моей машины за три копейки и синяк",
"твой отец кончил в твою мать под звуки похоронного марша, вот ты и вышел таким депрессивным",
"я имел твою мать на помойке, она ещё и мусор сортировала между моими заходами",
"твоя бабка ебётся с дедом через гроб, потому что боится что он её на том свете трахать будет",
"я твоей матери всю спину исполосовал ремнём, она сказала что давно не чувствовала себя такой живой",
"у твоих родителей семейный контракт: мать шлюха, отец сводник, а ты их бракованный товар",
"я заставил твою мать вылизать пол в морге за бутылку пива, она ещё и добавки попросила",
"твой отец сосёт у алкашей за возможность поспать в их будке",
"я трахал твою мать стоя на эскалаторе, люди аплодировали",
"твоя мать кончила когда я назвал её блядью, сказала что это ласково",
"я заставил твоего отца смотреть как я ебу его жену через дверной глазок, он плакал и дрочил",
"твоя бабка в молодости была лучшей шлюхой в своём селе, теперь ты продолжаешь её дело",
"я твою мать выебал на кладбище, она сказала что там теплее чем дома",
"у твоих родителей такой низкий потолок, что они могут стоя трахаться только в позе 'унижение'",
"я заставил твою мать стирать мои носки языком за ужин",
"твой отец делает минет убогим за возможность просто постоять рядом с нормальным мужиком",
"я выебал твою мать на глазах у твоего отца, он записал это на видео и продаёт на рынке",
"твоя мать сосёт так глубоко, что достаёт до моих ранних воспоминаний",
"я заставил твоего отца лизать пол после того как твоя мать на него нассала",
"твоя семья — это замкнутый круг деградации, ты его вершина и дно одновременно",
"я трахал твою мать на кухне, а она варила пельмени для моего кобеля",
"твой отец просил у меня разрешения просто посмотреть на кончик моего члена, я отказал",
"я заставил твою мать рыть могилу для твоей самооценки, она старательно копает до сих пор",
"твои родители скинулись по копейке чтобы купить одну презерватив, но было поздно",
"я твою мать ебал в примерочной, она потом украла трусы чтобы было что снять в следующий раз",
"твой отец продал твою мать за пачку сигарет, я вернул её за полпачки",
"я заставил твою мать петь гимн России пока я её имел, она знает все слова",
"твоя мать визжала так что у соседей сработали датчики движения на панике",
"я выебал твою мать на собеседовании, она получила должность швабры",
"твой отец плачет когда видит член, потому что напоминает ему о его никчёмности",
"я заставил твою мать делать мне минет в очереди за хлебом, люди аплодировали",
"твоя семья — это цирк уродов, а ты главный клоун без грима",
"я трахал твою мать на похоронах, она сказала что это лучший секс в её жизни",
"твой отец подтирается твоими школьными грамотами, говорит бумага качественная",
"я заставил твою мать лизать мои подошвы за право дышать моим воздухом",
"твоя мать сказала что я лучше тебя во всём, даже в том чтобы быть никчёмным",
"я выебал твою мать в машине скорой помощи, она попросила ещё и укол адреналина",
"твой отец мечтает чтобы я его выебал, но я брезгую даже через резину",
"я заставил твою мать кричать моё имя в церкви, батюшка сказал 'аминь'",
"твоя мать брала в рот всю футбольную команду, а потом жаловалась что мяч не тот",
"я твоего отца заставил подписывать отказ от тебя кровью на коленке",
"твоя мать сосёт так глубоко, что достаёт до моих детских обид и засасывает их",
"я трахал твою мать в библиотеке, она теперь считает себя образованной шлюхой",
"твой отец кончил в твою мать через трубочку, потому что член сломался о её тупость",
"я заставил твою мать стирать мою грязную совесть языком за еду",
"твоя бабка на том свете уже дрочит на мою тень, потому что при жизни не успела",
"я имел твою мать на крыше хрущёвки, соседи думали что гром",
"твой отец делает минет у бомжей за право переночевать рядом с теплотрассой",
"я твоей матери всю спину исполосовал проводами, она сказала что это массаж",
"твоя мать визжала так громко, что я оглох на левое ухо, но оно того стоило",
"я заставил твоего отца смотреть порно с твоей матерью и плакать от бессилия",
"твоя мать кончает когда я просто называю её фамилию вслух",
"я трахал твою мать на пороге её хаты, она потом ещё спасибо сказала за тёплый пол",
"твой отец продал твою детскую коляску за бутылку, чтобы отметить мою победу",
"я заставил твою мать рыть яму для твоего будущего, она старательно копает до сих пор",
"твои родители использовали тебя как бракованный презерватив, но забыли выбросить",
"я твою мать имел в примерочной, она потом украла трусы чтобы было что снять",
"твой отец сосёт у алкашей за право облизать их ботинки",
"я заставил твою мать танцевать на столе в отделе полиции, её арестовали",
"твоя мать визжала так что у соседей сработали датчики движения и вызвали ментов",
"я выебал твою мать на собеседовании, она получила должность швабры и гордится",
"твой отец плачет когда видит член, потому что напоминает ему о его никчёмности",
"я заставил твою мать делать мне минет в очереди за хлебом, люди кидали мелочь",
"твоя семья — это цирк уродов, а ты главный клоун без грима и без зрителей",
"я трахал твою мать на похоронах, она попросила ещё, пришлось повторить",
"твой отец подтирается твоими школьными грамотами, говорит бумага мягкая",
"я заставил твою мать лизать мои подошвы за право дышать моим воздухом",
"твоя мать сказала что я лучше тебя во всём, даже в том чтобы быть никчёмным",
"я выебал твою мать в машине скорой помощи, она попросила укол адреналина",
"твой отец мечтает чтобы я его выебал, но я брезгую даже через три презерватива",
"я заставил твою мать кричать моё имя в церкви, батюшка сказал 'аминь' и попросил добавки"
]

# ========== АТАКА С ПРЕВОСХОДСТВОМ ==========
async def attack_loop(user_id, target, chat_id, stop_event):
    global user_client
    if not user_client:
        return
    
    boss_lines = [
        "Я БОСС, А ТЫ ПРОСТО МОЯ ПЕДАЛЬ",
        "ТЫ ТЕРПИШЬ, ПОТОМУ ЧТО Я ТАК РЕШИЛ",
        "Я ЗДЕСЬ ГЛАВНЫЙ, ТВОЯ РОЛЬ — СКУЛИТЬ",
        "ТЫ ПРОИГРАЛ ЕЩЁ ДО ТОГО КАК Я НАЧАЛ",
        "Я КОМАНДУЮ, ТЫ ПОВИНУЕШЬСЯ",
        "ЭТО НЕ ТРОЛЛИНГ, ЭТО ТВОЯ НОВАЯ РАБОТА",
        "Я БОСС, А ТЫ МОЙ ЛИЧНЫЙ ТРЕНАЖЁР",
        "ТЫ ДАЖЕ НЕ ЖЕРТВА, ТЫ РАСХОДНЫЙ МАТЕРИАЛ",
        "Я ВЕДУ ЭТУ ИГРУ, А ТЫ ПРОСТО МЯЧ",
        "ТВОЁ ТЕРПЕНИЕ — МОЙ ТРОФЕЙ",
        "Я БОСС ЭТОЙ БЕСЕДЫ, А ТЫ МОЙ ЭХО-БОТ",
        "ТЫ УЖЕ СЛОМАЛСЯ, А Я ТОЛЬКО НАЧАЛ",
        "Я РАЗДАЮ ТВОИ СТРАДАНИЯ КАК ВИЗИТКИ",
        "ТЫ НЕ ТЕРПИШЬ, ТЫ НАСЛАЖДАЕШЬСЯ",
        "Я БОСС, А ТВОЯ ЖИЗНЬ — ТИТРЫ К МОЕЙ ПОБЕДЕ",
        "ТЫ ПРОСТО ФОН ДЛЯ МОИХ СЛОВ",
        "Я ЗДЕСЬ КОРОЛЬ, А ТЫ ПРИДВОРНЫЙ ШУТ",
        "ТЫ ДАЖЕ НЕ ВРАГ, ТЫ МОЯ ТЕНЬ",
        "Я БОСС, А ТЫ МОЯ КНОПКА ПАУЗЫ",
        "ТЫ ТЕРПИШЬ, ПОТОМУ ЧТО ВЫБОРА НЕТ"
    ]
    
    counter = 0
    while not stop_event.is_set():
        for line in lines_list:
            if stop_event.is_set():
                break
            
            # Отправляем обычное оскорбление
            try:
                await user_client.send_message(chat_id, f'@{target} {line}')
                await asyncio.sleep(0.3)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except:
                pass
            
            counter += 1
            
            # Каждые 2-3 сообщения вставляем капс-фразу
            if counter % random.randint(2, 3) == 0:
                boss_msg = random.choice(boss_lines)
                try:
                    await user_client.send_message(chat_id, f'@{target} {boss_msg}')
                    await asyncio.sleep(0.3)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except:
                    pass
        
        await asyncio.sleep(0.3)

# ========== АВТОРИЗАЦИЯ (ТОЛЬКО ЛС) ==========
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
            await event.reply("✅ Аккаунт уже авторизован. Пиши .байт @username в любом чате")
            return
        buttons = [[Button.request_phone("📱 Поделиться номером", resize=True)]]
        await event.reply("🔐 Отправь номер своего аккаунта", buttons=buttons)
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
            await event.reply(f"✅ Код на {phone[-4:]}\n\nВведи код кнопками:", buttons=get_digit_keyboard())
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
                await event.edit("✅ Аккаунт авторизован!\n\nТеперь пиши .байт @username в любом чате", buttons=get_clear_keyboard())
                
                # Запускаем обработчик команд
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
                            task = asyncio.create_task(attack_loop(user_id, target, chat, stop))
                            active_attacks[key] = (task, stop)
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
                await event.edit("✅ Аккаунт авторизован!\n\nТеперь пиши .байт @username в любом чате", buttons=get_clear_keyboard())
                
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
                            task = asyncio.create_task(attack_loop(user_id, target, chat, stop))
                            active_attacks[key] = (task, stop)
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

# ========== ЗАПУСК ==========
async def main():
    await auth_client.start()
    me = await auth_client.get_me()
    print(f'✅ Бот: @{me.username}')
    print('👉 Напиши боту /start, авторизуй свой аккаунт')
    print('👉 После авторизации пиши .байт @username в ЛЮБОМ чате')
    print('👉 Атака от твоего лица, каждые 2-3 сообщения — КАПС-фраза про БОССА')
    await auth_client.run_until_disconnected()

with auth_client:
    auth_client.loop.run_until_complete(main())
