import asyncio
import time
import os
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.custom import Button

API_ID = 39163151
API_HASH = '3c0e92ad7b268eca1eb1a33a9baa7d1d'
BOT_TOKEN = '8699194957:AAEalLeB1AEYWvhsEiQwUHzZyvhqB8oHfAw'

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

bot_client = TelegramClient(os.path.join(SESSION_DIR, 'bot_session'), API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_client = None
user_auth_data = {}
active_bites = {}
PREFIX = '.'

# ========== ВСЕ ОСКОРБЛЕНИЯ ==========
insults = [
    "я твою мать ебал", "я твою мать ебал в жопу", "я твою мать ебал в рот",
    "я твою мать ебал в глотку", "я твою мать ебал в пизду", "я твою мать ебал в анал",
    "я твою мать ебал до крови", "я твою мать ебал до гноя", "я твою мать ебал до мяса",
    "я твою мать ебал до костей", "я твою мать ебал до кишок", "я твою мать ебал до рвоты",
    "я твою мать ебал шлангом", "я твою мать ебал ломом", "я твою мать ебал арматурой",
    "я твою мать ебал кувалдой", "твоя мать шалава", "твоя мать блядина", "твоя мать падаль",
    "твоя мать мусорная яма", "твоя мать гнойная рана", "твоя мать сифилитичная дыра",
    "твоя мать трипперная вонь", "твоя мать сосет у параши", "твоя мать лижет у помойки",
    "твоя мать глотает в подворотне", "твоя мать обсасывает в сортире", "твоя мать вылизывает в канализации",
    "твоя мать заглатывает за спайс", "твоя мать дрочит на вокзале", "твоя мать мастурбирует в ночлежке",
    "твоя мать кончает под забором", "твой отец пьет мочу", "твой отец спит с козой", "твой отец лижет пол",
    "твой отец сосет у бомжей", "твой отец продал паспорт", "твой отец кончил в себя", "твоя бабка шлюха века",
    "твоя бабка ебется с дедом", "твоя бабка сосет сквозь гроб", "твоя сестра даёт за чипсы",
    "твоя сестра сосет в подвале", "твоя сестра ложится под всех", "твой брат петух конченый",
    "твой брат дрочит на школу", "твой брат импотент хуев", "ты гнойный мешок", "ты недоносок", "ты выкидыш",
    "ты ссанье подзаборное", "ты фекальная масса", "ты мокрота из мамкиной матки", "ты спермотоксикоз",
    "ты отребье человеческое", "ты гниющий труп", "ты биомусор", "ты ублюдок конченый", "ты мразь ебанная",
    "ты тварь дрожащая", "ты гнида вшивая", "ты пиздюк петушиный", "ты ссыкло безъяйцевое", "ты импотент хуев",
    "ты даже стоять не можешь", "ты даже на коленях говно", "ты трясешься как заяц", "ты боишься собственной тени",
    "ты хуже любой шалавы", "ты хуже любой бляди", "ты хуже помойной крысы", "ты даже на органы не годен",
    "ты пустое место", "ты ноль без палки", "ты даже хуже нуля", "я ломал твои ребра об асфальт",
    "я выбивал твои зубы о бордюр", "я проламывал твой череп о стену", "я вырывал твой язык об унитаз",
    "я отрубал твои пальцы", "я раздроблял твои колени", "я выкалывал твои глаза ломом", "я сломал твою челюсть",
    "я перебил тебе позвоночник", "я разорвал тебе сухожилия", "я сжег твою морду кислотой", "я отрезал тебе уши",
    "я забил твою глотку грязью", "я засунул твою башку в унитаз", "я твою рожу об асфальт тер",
    "я твои кости собакам скормил", "я твое тело в выгребную яму скинул", "а ты даже не рыпнулся",
    "а ты даже не пискнул", "а ты даже мать не защитил", "ты просто смотрел как ее трахают",
    "ты лизал пол пока мать работала", "ты стоял в углу и дрочил", "ты кончал в штаны от страха",
    "ты обоссался когда я посмотрел", "ты обосрался когда я кашлянул", "ты ссыкло конченое с детства",
    "ты тряпка без воли", "ты мешок без яиц", "ты кусок дерьма в человеческой оболочке",
    "ты даже ответить ничего не сможешь", "ты проглотишь язык и будешь молчать", "потому что ты никто",
    "потому что ты ничто", "потому что ты пустота", "я твой бог", "я твой господин", "я твой повелитель",
    "я твой палач", "я твой судья", "я твоя смерть", "ты умрешь в грязи", "ты сдохнешь под забором",
    "ты захлебнешься собственной рвотой", "ты сгниешь заживо", "тебя сожрут черви", "тебя разложат бактерии",
    "тебя размажут по асфальту", "ты даже памяти о себе не оставишь", "ты даже могилы не заслужишь",
    "тебя похоронят в выгребной яме", "тебя закопают на свалке", "тебя скинут в канаву", "и никто не придет",
    "никто не всплакнет", "никто не вспомнит", "потому что ты никто и звать тебя никак"
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
                await asyncio.sleep(0.2)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except:
                pass

# ========== ОСНОВНОЙ ОБРАБОТЧИК ==========
@bot_client.on(events.NewMessage)
async def handler(event):
    global user_client, user_auth_data, active_bites
    
    user_id = event.sender_id
    text = event.raw_text.strip()
    chat_id = event.chat_id
    
    # АВТОРИЗАЦИЯ (личка с ботом)
    if chat_id == user_id:
        if text == '/start':
            if user_client and user_client.is_connected():
                await event.reply("✅ Уже авторизован. Команды: .байт @username")
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
        
        # Ввод кода
        if user_id in user_auth_data:
            auth = user_auth_data[user_id]
            if auth.get('state') == 'password_waiting':
                try:
                    await user_client.sign_in(password=text)
                    del user_auth_data[user_id]
                    await event.reply("✅ Авторизован!\n\n.байт @username")
                except Exception as e:
                    await event.reply(f"❌ Неверный пароль: {e}")
                return
            else:
                if len(text) >= 3:
                    try:
                        await user_client.sign_in(
                            phone=auth['phone'],
                            code=text,
                            phone_code_hash=auth['phone_code_hash']
                        )
                        del user_auth_data[user_id]
                        await event.reply("✅ Авторизован!\n\n.байт @username")
                    except SessionPasswordNeededError:
                        user_auth_data[user_id]['state'] = 'password_waiting'
                        await event.reply("🔐 Введи 2FA пароль:")
                    except Exception as e:
                        await event.reply(f"❌ {e}")
            return
        return
    
    # КОМАНДЫ В ГРУППАХ И ЛС
    if not user_client:
        return
    if not text.startswith(PREFIX):
        return
    
    parts = text[len(PREFIX):].split()
    if not parts:
        return
    cmd = parts[0].lower()
    
    if cmd == 'пинг':
        start = time.time()
        msg = await event.reply('🏓 Понг...')
        await msg.edit(f'🏓 Понг! {round((time.time()-start)*1000)}ms')
        return
    
    if cmd == 'байт' and len(parts) > 1:
        target = parts[1].replace('@', '')
        try:
            entity = await user_client.get_entity(target)
            target_id = entity.id
            key = f"{chat_id}_{target_id}"
            if key not in active_bites:
                stop = asyncio.Event()
                task = asyncio.create_task(bite_loop(target_id, chat_id, stop))
                active_bites[key] = (task, stop)
                await event.edit('Добавлен.')
            else:
                await event.edit('Уже активен')
        except:
            await event.edit('Не найден')
        return
    
    if cmd == 'байт' and event.is_reply:
        target_msg = await event.get_reply_message()
        target_id = target_msg.sender_id
        key = f"{chat_id}_{target_id}"
        if key not in active_bites:
            stop = asyncio.Event()
            task = asyncio.create_task(bite_loop(target_id, chat_id, stop))
            active_bites[key] = (task, stop)
            await event.edit('Добавлен.')
        else:
            await event.edit('Уже активен')
        return
    
    if cmd == 'байтстоп':
        for key in list(active_bites.keys()):
            if key.startswith(f"{chat_id}_"):
                task, stop = active_bites[key]
                stop.set()
                task.cancel()
                del active_bites[key]
        await event.edit('Остановлен')
        return
    
    if cmd == 'команды':
        await event.reply('📋 .байт @username | .байтстоп | .пинг')
        return

# ========== INLINE КНОПКИ ==========
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
            await event.edit("✅ Авторизован!\n\n.байт @username", buttons=get_clear_keyboard())
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
                await event.edit("✅ Авторизован!\n\n.байт @username", buttons=get_clear_keyboard())
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
    await bot_client.start()
    me = await bot_client.get_me()
    print(f'✅ Бот: @{me.username}')
    print('👉 Напиши /start, авторизуй свой аккаунт')
    await bot_client.run_until_disconnected()

with bot_client:
    bot_client.loop.run_until_complete(main())