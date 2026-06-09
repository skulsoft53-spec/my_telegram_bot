import asyncio
import random
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

BOT_TOKEN = '8531970927:AAEvLAk3pQJCQpfCOX7CSU20gY6zvYZnmi0'
MY_USERNAME = 'sixuta'

# ========== ВСЕ ОСКОРБЛЕНИЯ ==========
insults = [
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
    "я твою мать ебал шлангом",
    "я твою мать ебал ломом",
    "я твою мать ебал арматурой",
    "я твою мать ебал кувалдой",
    "твоя мать шалава",
    "твоя мать блядина",
    "твоя мать падаль",
    "твоя мать мусорная яма",
    "твоя мать гнойная рана",
    "твоя мать сифилитичная дыра",
    "твоя мать трипперная вонь",
    "твоя мать сосет у параши",
    "твоя мать лижет у помойки",
    "твоя мать глотает в подворотне",
    "твой отец пьет мочу",
    "твой отец спит с козой",
    "твой отец лижет пол",
    "твой отец сосет у бомжей",
    "твоя бабка шлюха века",
    "твоя бабка ебется с дедом",
    "твоя бабка сосет сквозь гроб",
    "твоя сестра даёт за чипсы",
    "твоя сестра сосет в подвале",
    "твой брат петух конченый",
    "твой брат дрочит на школу",
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
    "ты трясешься как заяц",
    "ты боишься собственной тени",
    "ты хуже любой шалавы",
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
    "а ты даже не рыпнулся",
    "а ты даже мать не защитил",
    "ты просто смотрел как ее трахают",
    "ты стоял в углу и дрочил",
    "ты кончал в штаны от страха",
    "ты ссыкло конченое с детства",
    "ты тряпка без воли",
    "ты мешок без яиц",
    "ты кусок дерьма в человеческой оболочке",
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

# ========== ТРИГГЕРЫ ==========
trigger_words = [
    "сын шлюхи", "сукин сын", "твоя мать", "твою мать", "твой отец",
    "сука", "бля", "блядь", "шлюха", "хуй", "пизда", "ебал", "ебать",
    "заебал", "уебок", "мудак", "пидор", "дебил", "идиот", "лох", "тварь",
    "мразь", "урод", "чмо",
]

# ========== АВТО-ОТВЕТЫ ==========
auto_replies_with_mention = [
    "твоя мать шалава, @{}",
    "иди нахуй, @{}",
    "@{}, сын шлюхи",
    "@{}, сукин сын",
    "@{}, закрой свой пиздатый рот",
    "@{}, твою мать ебали всем подъездом",
    "@{}, твоя мать сосет у параши",
    "@{}, твой отец кончил в твою мать через трубочку",
    "@{}, твоя бабка ещё при жизни была проституткой",
    "@{}, твоя сестра даёт за чипсы",
    "@{}, твой брат петух конченый",
    "заткнись, @{}, а то я твою мать снова выебу",
    "@{}, ты даже не человек",
    "@{}, ты пустое место",
    "@{}, ты ошибка природы",
    "@{}, тебя даже черви жрут с брезгливостью",
    "@{}, твоя жизнь — ошибка",
    "@{}, ты хуже помойной крысы",
    "@{}, у тебя лицо как у пердака",
    "@{}, твой мозг весит меньше моего члена",
    "@{}, ты даже на органы не годен",
    "@{}, иди в пизду",
    "@{}, в жопу иди",
    "@{}, отсоси",
]

auto_replies_without_mention = [
    "иди нахуй", "пошёл нахуй", "закрой ебало", "рот закрой", "отъебись",
    "соси хуй", "заебал уже", "ты чё, дурак?", "вали отсюда", "иди в жопу",
    "иди в пизду", "ты кто вообще такой?", "твоё мнение нихуя не важно",
    "ты никто", "ты ничто", "ты пустота", "ты ошибка природы",
    "твоя жизнь — ошибка", "тебя даже черви брезгуют", "ты хуже помойной крысы",
    "ты даже не человек", "ты гнойный мешок", "ты биомусор", "ты отребье",
    "иди вон", "пошёл вон", "заткни пасть", "не беси", "отстань", "надоел",
]

def split_text(text, limit=4000):
    if len(text) <= limit:
        return [text]
    parts = []
    lines = text.split('\n')
    current = []
    current_len = 0
    for line in lines:
        if current_len + len(line) + 1 > limit:
            parts.append('\n'.join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += len(line) + 1
    if current:
        parts.append('\n'.join(current))
    return parts

async def start(update: Update, context):
    await update.message.reply_text(
        "👹 **Бот-тролль активен!**\n\n"
        "📌 Команда: `.ку @username`\n"
        "🤖 Бот отвечает на мат",
        parse_mode='Markdown'
    )

async def cmd_insult(update: Update, context):
    text = update.message.text.strip()
    match = re.search(r'\.ку\s+@?(\w+)', text)
    if not match:
        await update.message.reply_text("❌ Укажи юзернейм: `.ку @username`")
        return
    
    target = match.group(1)
    full_text = '\n'.join([f'@{target} {i}' for i in insults])
    
    parts = split_text(full_text)
    for part in parts:
        await update.message.reply_text(part)
        await asyncio.sleep(0.1)  # МАКСИМАЛЬНО БЫСТРО

async def cmd_stop(update: Update, context):
    await update.message.reply_text("🛑 Авто-ответ выключен")

async def auto_reply(update: Update, context):
    text = update.message.text.lower()
    user = update.message.from_user
    username = user.username.lower() if user.username else ""
    
    if username == MY_USERNAME.lower():
        return
    if text.startswith('.ку') or text.startswith('.кустоп'):
        return
    
    for word in trigger_words:
        if word in text:
            if random.random() > 0.5:
                reply = random.choice(auto_replies_with_mention).format(username)
            else:
                reply = random.choice(auto_replies_without_mention)
            await update.message.reply_text(reply)
            return

async def new_chat_member(update: Update, context):
    for member in update.message.new_chat_members:
        if member.username == (await context.bot.get_me()).username:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="👹 **Бот-тролль включен в этом чате!**\n\nКоманда: `.ку @username`",
                parse_mode='Markdown'
            )
            return

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'^\.ку\s'), cmd_insult))
    app.add_handler(MessageHandler(filters.Regex(r'^\.кустоп$'), cmd_stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member))
    
    print("✅ Бот-тролль запущен")
    app.run_polling()

if __name__ == "__main__":
    main()