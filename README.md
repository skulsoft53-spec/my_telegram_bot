# Apache Safe Bot (ready-to-deploy)
This package contains a safe Telegram bot using aiogram v2 and SQLite for templates.
**Important**: This project **does NOT** include malicious features (no account takeover, no mass deletion of other users' messages, no insults/spam).

## Files
- `main.py` - main bot code
- `requirements.txt` - dependencies
- `Procfile` - for Heroku/Render (starts python main.py)
- `example.env` - example environment variables to set

## Setup (Replit / Render / Heroku)
1. Put the files into your project.
2. Create environment variables:
   - `BOT_TOKEN` - your bot token (from BotFather)
   - `OWNER_ID` - your Telegram user id (optional, for /stopbot)
3. Install deps: `pip install -r requirements.txt`
4. Run: `python main.py`

## Notes
- Templates are stored in `data.db` (SQLite) in the working directory.
- `repeat` command is rate-limited and capped to avoid abuse.
- To keep the bot alive on free hosts you may need a pinging service (UptimeRobot) or use a paid "always on" option.