Apache Userbot — Full Safe Edition
=================================

This package is a Telethon-based userbot packaged to run on Render as a Web Service.
It intentionally excludes abusive features (no insults, no harassment, no mass unsolicited spam).
Instead it provides safe alternatives (humorous replies, opt-in autosms, limited flood for testing, triggers, muting where possible).

How to use:
1. Generate a session file locally (recommended) using Telethon StringSession.
   Save it as: sessions/<your_telegram_id>.session
2. Push this project to a Git repository and connect to Render, or upload via GitHub.
3. Deploy on Render (Web Service). The Flask app keeps the service alive.
4. Logs appear in Render's dashboard; if clients don't start, ensure sessions/*.session exists.

Security & Limits:
- Rate limits applied to avoid abuse.
- Heavy features limited (flood max 5 messages).
- All state (autosms, triggers, muted) is in-memory and resets on restart.

