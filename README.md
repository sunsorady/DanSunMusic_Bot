# Music Playground Telegram Bot

A Telegram bot for downloading media from TikTok, Twitter/X, and YouTube.

### Features

- Download videos & audio from YouTube
- Download media from TikTok and Twitter/X
- Admin panel: view users, broadcast messages, ban/unban
- User statistics and settings

### Setup

1. Clone the repo:

       git clone https://github.com/sunsorady/DanSunMusic_Bot.git
       cd DanSunMusic_Bot

2. Install dependencies:

       pip install -r requirements.txt

3. Create a `.env` file:

       BOT_TOKEN = YOUR_BOT_TOKEN
       db_auth = DATABASE_URL
       admin_id = YOUR_TELEGRAM_ID
       CHANNEL_ID = YOUR_CHANNEL_ID

4. Run:

       python main.py

### Docker

    docker compose up -d

### License

MIT
