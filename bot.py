import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = "8218314042:AAGflLWbojVmMfi31v2UC9XQ0aZwC31U4sQ"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

muted_users = {}
auto_reply_users = {}

def start(update, context):
    update.message.reply_text("🔥 Ты в боте АПАЧИ!")

def mute(update, context):
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        muted_users[user_id] = True
        update.message.reply_text(f"🔇 Пользователь {user_id} замучен.")
    else:
        update.message.reply_text("❌ Ответь на сообщение для мута.")

def unmute(update, context):
    if context.args:
        try:
            user_id = int(context.args[0])
            muted_users.pop(user_id, None)
            update.message.reply_text(f"✅ Пользователь {user_id} размучен.")
        except ValueError:
            update.message.reply_text("❌ Укажи ID пользователя.")
    else:
        update.message.reply_text("❌ Используй: /unmute [id]")

def autosms(update, context):
    if update.message.reply_to_message and context.args:
        user_id = update.message.reply_to_message.from_user.id
        text = " ".join(context.args)
        auto_reply_users[user_id] = text
        update.message.reply_text(f"🤖 Теперь все сообщения от {user_id} будут получать ответ: {text}")
    else:
        update.message.reply_text("❌ Ответь на сообщение и укажи текст.")

def stop_autosms(update, context):
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        auto_reply_users.pop(user_id, None)
        update.message.reply_text(f"✅ Автоответ для {user_id} выключен.")
    else:
        update.message.reply_text("❌ Ответь на сообщение.")

def edit(update, context):
    try:
        count = int(context.args[0])
        new_text = " ".join(context.args[1:])
        for _ in range(count):
            update.message.reply_text(f"(исправлено) {new_text}")
    except Exception:
        update.message.reply_text("❌ Используй: /edit [кол-во] [текст]")

def check_messages(update, context):
    user_id = update.message.from_user.id
    if user_id in muted_users:
        try:
            update.message.delete()
        except Exception as e:
            logger.error(f"Ошибка удаления сообщения: {e}")
    if user_id in auto_reply_users:
        update.message.reply_text(auto_reply_users[user_id])

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("mute", mute))
    dp.add_handler(CommandHandler("unmute", unmute))
    dp.add_handler(CommandHandler("autosms", autosms))
    dp.add_handler(CommandHandler("stopautosms", stop_autosms))
    dp.add_handler(CommandHandler("edit", edit))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_messages))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
