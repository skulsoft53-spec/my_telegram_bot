import asyncio
import random
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

BOT_TOKEN = '8531970927:AAEvLAk3pQJCQpfCOX7CSU20gY6zvYZnmi0'
MY_USERNAME = 'sixuta'

# ========== УНИКАЛЬНЫЕ ОСКОРБЛЕНИЯ ДЛЯ .ку ==========
insults = [
    "я твою мать ебал", "я твою мать ебал в жопу", "я твою мать ебал в рот",
    "я твою мать ебал в глотку", "я твою мать ебал в пизду", "я твою мать ебал в анал",
    "я твою мать ебал до крови", "я твою мать ебал до гноя", "я твою мать ебал до мяса",
    "я твою мать ебал до костей", "я твою мать ебал до кишок", "я твою мать ебал до рвоты",
    "я твою мать ебал шлангом", "я твою мать ебал ломом", "я твою мать ебал арматурой",
    "я твою мать ебал кувалдой", "твоя мать шалава", "твоя мать блядина", "твоя мать падаль",
    "твоя мать мусорная яма", "твоя мать гнойная рана", "твоя мать сифилитичная дыра",
    "твоя мать трипперная вонь", "твоя мать сосет у параши", "твоя мать лижет у помойки",
    "твоя мать глотает в подворотне", "твой отец пьет мочу", "твой отец спит с козой",
    "твой отец лижет пол", "твой отец сосет у бомжей", "твоя бабка шлюха века",
    "твоя бабка ебется с дедом", "твоя бабка сосет сквозь гроб", "твоя сестра даёт за чипсы",
    "твоя сестра сосет в подвале", "твой брат петух конченый", "твой брат дрочит на школу",
    "ты гнойный мешок", "ты недоносок", "ты выкидыш", "ты ссанье подзаборное",
    "ты фекальная масса", "ты мокрота из мамкиной матки", "ты спермотоксикоз",
    "ты отребье человеческое", "ты гниющий труп", "ты биомусор", "ты ублюдок конченый",
    "ты мразь ебанная", "ты тварь дрожащая", "ты гнида вшивая", "ты пиздюк петушиный",
    "ты ссыкло безъяйцевое", "ты импотент хуев", "ты даже стоять не можешь",
    "ты даже на коленях говно", "ты трясешься как заяц", "ты боишься собственной тени",
    "ты хуже любой шалавы", "ты хуже любой бляди", "ты хуже помойной крысы",
    "ты даже на органы не годен", "ты пустое место", "ты ноль без палки", "ты даже хуже нуля",
    "я ломал твои ребра об асфальт", "я выбивал твои зубы о бордюр",
    "я проламывал твой череп о стену", "я вырывал твой язык об унитаз",
    "я отрубал твои пальцы", "я раздроблял твои колени", "я выкалывал твои глаза ломом",
    "я сломал твою челюсть", "я перебил тебе позвоночник", "я разорвал тебе сухожилия",
    "я сжег твою морду кислотой", "я отрезал тебе уши", "а ты даже не рыпнулся",
    "а ты даже мать не защитил", "ты просто смотрел как ее трахают", "ты стоял в углу и дрочил",
    "ты кончал в штаны от страха", "ты ссыкло конченое с детства", "ты тряпка без воли",
    "ты мешок без яиц", "ты кусок дерьма в человеческой оболочке", "потому что ты никто",
    "потому что ты ничто", "я твой бог", "я твой палач", "я твой судья", "я твоя смерть",
    "ты умрешь в грязи", "ты сдохнешь под забором", "тебя сожрут черви",
    "тебя размажут по асфальту", "ты даже могилы не заслужишь", "тебя закопают на свалке",
    "и никто не придет", "никто не вспомнит",
]

# ========== АВТО-ОТВЕТЫ С УПОМИНАНИЕМ (100+ ПРО РОДИТЕЛЕЙ) ==========
auto_replies_with_mention = [
    "твоя мать шалава, @{}",
    "твоя мать блядина, @{}",
    "твоя мать падаль, @{}",
    "твою мать ебали всем подъездом, @{}",
    "твоя мать сосет у параши, @{}",
    "твоя мать лижет пол в морге, @{}",
    "твоя мать дрочит на вокзале, @{}",
    "твоя мать кончает под забором, @{}",
    "твоя мать мастурбирует в ночлежке, @{}",
    "твоя мать заглатывает за спайс, @{}",
    "твоя мать обсасывает в сортире, @{}",
    "твой отец пьет мочу, @{}",
    "твой отец спит с козой, @{}",
    "твой отец лижет пол, @{}",
    "твой отец сосет у бомжей, @{}",
    "твой отец продал паспорт, @{}",
    "твой отец кончил в себя, @{}",
    "твоя бабка шлюха века, @{}",
    "твоя бабка ебется с дедом, @{}",
    "твоя бабка сосет сквозь гроб, @{}",
    "твоя сестра даёт за чипсы, @{}",
    "твоя сестра сосет в подвале, @{}",
    "твоя сестра ложится под всех, @{}",
    "твой брат петух конченый, @{}",
    "твой брат дрочит на школу, @{}",
    "твой брат импотент хуев, @{}",
    "у твоей матери лицо как у пердака, @{}",
    "твою мать ебали в очереди за хлебом, @{}",
    "твою мать трахали на свалке, @{}",
    "твою мать драли в канализации, @{}",
    "твою мать имели в морге, @{}",
    "твоя мать визжала как поросенок, @{}",
    "твоя мать кончала от моего голоса, @{}",
    "твой отец плачет когда видит член, @{}",
    "твой отец мечтает чтобы я его выебал, @{}",
    "твоя бабка на том свете уже дрочит на меня, @{}",
    "твоя сестра сосет за еду, @{}",
    "твой брат делает минет убогим, @{}",
]

auto_replies_without_mention = [
    "иди нахуй", "пошёл нахуй", "закрой ебало", "отъебись", "соси хуй",
    "заебал уже", "ты чё, дурак?", "вали отсюда", "иди в жопу", "иди в пизду",
    "ты никто", "ты ничто", "ты ошибка природы", "ты хуже помойной крысы",
    "иди вон", "заткни пасть", "не беси", "отстань", "надоел",
]

auto_reply_enabled = True

async def start(update: Update, context):
    await update.message.reply_text(
        "👹 **Бот-тролль активен!**\n\n"
        "📌 Команды:\n"
        "`.ку @username` — оскорбить пользователя\n"
        "`.кустоп` — выключить авто-ответ\n"
        "`.кустарт` — включить авто-ответ\n\n"
        "🤖 Бот отвечает на мат и оскорбления родителей",
        parse_mode='Markdown'
    )

async def cmd_insult(update: Update, context):
    text = update.message.text.strip()
    match = re.search(r'\.ку\s+@?(\w+)', text)
    if not match:
        await update.message.reply_text("❌ Укажи юзернейм: `.ку @username`")
        return
    target = match.group(1)
    for insult in insults:
        await update.message.reply_text(f'@{target} {insult}')
        await asyncio.sleep(0.05)

async def cmd_stop(update: Update, context):
    global auto_reply_enabled
    auto_reply_enabled = False
    await update.message.reply_text("🛑 Авто-ответ выключен. Для включения: `.кустарт`")

async def cmd_start_auto(update: Update, context):
    global auto_reply_enabled
    auto_reply_enabled = True
    await update.message.reply_text("✅ Авто-ответ включен")

async def auto_reply(update: Update, context):
    global auto_reply_enabled
    if not auto_reply_enabled:
        return
    
    text = update.message.text.lower()
    user = update.message.from_user
    username = user.username.lower() if user.username else ""
    
    if username == MY_USERNAME.lower():
        return
    if text.startswith('.ку') or text.startswith('.кустоп') or text.startswith('.кустарт'):
        return
    
    # Ответ на сообщение бота
    if update.message.reply_to_message and update.message.reply_to_message.from_user.username == (await context.bot.get_me()).username:
        await update.message.reply_text(random.choice(auto_replies_without_mention))
        return
    
    # Триггеры на оскорбления родителей и мат
    trigger_words = ["твоя мать", "твою мать", "твой отец", "твоя мама", "мать твою", "сука", "бля", "хуй", "пизда", "ебал", "заебал", "дебил", "идиот", "лох", "тварь", "мразь", "урод", "чмо"]
    
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
                text="👹 **Бот-тролль включен в этом чате!**\n\nКоманды: `.ку @username`, `.кустоп`, `.кустарт`",
                parse_mode='Markdown'
            )
            return

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'^\.ку\s'), cmd_insult))
    app.add_handler(MessageHandler(filters.Regex(r'^\.кустоп$'), cmd_stop))
    app.add_handler(MessageHandler(filters.Regex(r'^\.кустарт$'), cmd_start_auto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member))
    print("✅ Бот-тролль запущен (100+ авто-ответов про родителей)")
    app.run_polling()

if __name__ == "__main__":
    main()