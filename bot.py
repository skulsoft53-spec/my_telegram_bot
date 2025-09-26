import telebot

BOT_TOKEN = "8218314042:AAGflLWbojVmMfi31v2UC9XQ0aZwC31U4sQ"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет 👋! Я твой бот и готов работать на Render 🚀")

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "Список команд:\n/start – начать\n/help – помощь")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.send_message(message.chat.id, f"Ты написал: {message.text}")

print("Бот запущен...")
bot.polling(none_stop=True)
