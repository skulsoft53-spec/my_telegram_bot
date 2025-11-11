# userbot_alia_render.py
from telethon import TelegramClient, events, Button

# ==== Настройки ====
api_id = 22603193
api_hash = '52012f357acfda33579dd701d7b4a131'
phone = '+17652635639'  # твой номер телефона
session_name = 'userbot_render'

# ==== Инициализация клиента ====
client = TelegramClient(session_name, api_id, api_hash)

# ==== Главное меню ====
main_menu = [
    [Button.inline("🛠 Команды", b'commands'), Button.inline("🎮 Игры", b'games')],
    [Button.inline("📊 Статистика", b'stats'), Button.inline("ℹ️ Инфо", b'info')]
]

# ==== Списки команд ALYAUB ====
commands_list = [
    '/kick', '/ban', '/mute', '/unmute', '/warn', '/unwarn',
    '/promote', '/demote', '/pin', '/unpin', '/delmsg', '/id',
    '/online', '/members', '/messages', '/report', '/settings',
    '/byte'  # команда как в ALYAUB
]

games_list = ['Игра 1', 'Игра 2', 'Игра 3']

stats_list = """
Статистика чата:
- /members - участники
- /messages - количество сообщений
- /online - кто онлайн
- /id - информация о чате
"""

info_text = "Юзер-бот от твоего имени. Версия 1.0\nВсе команды ALYAUB интегрированы."

# ==== Обработка команды /start ====
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Привет! Главное меню:", buttons=main_menu)

# ==== Обработка нажатий кнопок ====
@client.on(events.CallbackQuery)
async def callback(event):
    data = event.data.decode('utf-8')
    
    if data == 'commands':
        await event.edit("Команды ALYAUB:", buttons=[
            [Button.inline(cmd, cmd.encode())] for cmd in commands_list
        ])
    elif data == 'games':
        await event.edit("Игры:", buttons=[
            [Button.inline(game, game.encode())] for game in games_list
        ])
    elif data == 'stats':
        await event.edit(stats_list)
    elif data == 'info':
        await event.edit(info_text)
    elif data in commands_list:
        # Обработка конкретной команды
        if data == '/byte':
            await event.respond("Команда /byte выполнена! ⚡")
        else:
            await event.respond(f"Выполняю команду: {data}")

# ==== Запуск клиента ====
client.start(phone)
print("Userbot запущен и онлайн!")
client.run_until_disconnected()