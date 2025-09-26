Apache Userbot — Safe Edition
----------------------------

This package provides a Telethon userbot with a reduced, safer feature set.
Removed/disabled features: mass unsolicited messaging, automated insulting/harassment ("байт"),
high-rate flooding, tools designed to facilitate DDoS or spam.

Included (safe) features:
- .пинг — health check
- .дд N — delete your last N messages
- .ред N текст — edit your last N messages
- .автосмс (reply) текст — auto-reply to a user's messages (opt-in, moderated)
- .автосмсстоп — stop auto-reply
- .мут / .мутстоп — best-effort deletion of messages from a user where allowed
- .аниме [tag] — send a random anime image
- +триггер phrase|response — exact-match triggers (limited to 10)

How to use:
1) Generate a Telethon session string locally (recommended) and save it as sessions/<your_id>.session
   Example (locally):
     from telethon.sessions import StringSession
     from telethon import TelegramClient
     client = TelegramClient(StringSession(), API_ID, API_HASH)
     await client.start()  # enter phone + code locally
     print(client.session.save())  # save to file sessions/<your_id>.session

2) Deploy to Render or any VPS. Ensure requirements installed:
   pip install -r requirements.txt
   Start: python3 main.py

Notes:
- State (autosms, muted, triggers) is stored in memory and resets on restart.
- This edition intentionally omits or disables abusive features. Use responsibly.
