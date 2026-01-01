# HilAlon Bot

A Telegram bot that automates weekly family scheduling and Google Calendar event creation.

## Features

- **Interactive Schedule Planning**: Step-by-step conversation flow to plan weekly schedules
- **School Pickup Management**: Coordinate morning and afternoon school pickups between parents
- **Date Night Planning**: Schedule weekly date nights with automatic babysitter reminders
- **Kindergarten Tracking**: Track kindergarten days with automatic counter
- **Google Calendar Integration**: Automatically creates all events in Google Calendar
- **Multi-user Authorization**: Restrict bot usage to authorized users only
- **Hebrew Interface**: Bot messages are in Hebrew for user interaction

## Prerequisites

- Python 3.8 or higher
- A Telegram bot token (from [@BotFather](https://t.me/botfather))
- Google Calendar API credentials
- A Google Calendar ID

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd HilAlon_Bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials file and save it as `credentials.json` in the project root

### 4. Configure environment variables

Create a `.env` file in the project root (use `.env.example` as a template):

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=123456789,987654321
CALENDAR_ID=your_calendar_id@group.calendar.google.com
```

**How to get these values:**
- **TELEGRAM_BOT_TOKEN**: Talk to [@BotFather](https://t.me/botfather) on Telegram
- **ADMIN_CHAT_ID**: Send a message to [@userinfobot](https://t.me/userinfobot) on Telegram (comma-separated for multiple users)
- **CALENDAR_ID**: Find in Google Calendar settings under "Integrate calendar"

## Usage

### Running the bot

```bash
python telegram_bot.py
```

On first run, you'll be prompted to authorize the bot with your Google account via a browser window. A `token.json` file will be created to save your authorization for future runs.

### Using the bot

1. Start a conversation with your bot on Telegram
2. Send `/start` command
3. Follow the interactive prompts to:
   - Select pickup days for morning school runs
   - Choose date night days for each parent
   - Select kindergarten days
4. Confirm the schedule
5. The bot will create all events in your Google Calendar

### Schedule Types

The bot creates the following event types:

- **Morning School Drive** (07:30-08:00): Designated parent for morning pickup
- **Afternoon School Pickup** (16:00-16:30, Friday: 11:30-12:00): Designated parent for afternoon pickup
- **Date Nights** (20:00-22:00): Weekly date night events
- **Babysitter Reminders**: Automatic reminder 3 days before date night
- **Kindergarten Days** (09:00-17:00): Tracks kindergarten attendance with counter

## Configuration

You can customize event times and settings in [config.py](config.py):

- Event start/end times
- Reminder schedules
- Timezone settings (default: Asia/Jerusalem)
- Kindergarten counter settings

## Project Structure

```
HilAlon_Bot/
├── telegram_bot.py       # Main bot logic and conversation handlers
├── config.py             # Configuration and settings
├── schedule_logic.py     # Schedule state management
├── calendar_utils.py     # Google Calendar integration
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Running on Ubuntu Server

The bot is designed to work on Ubuntu servers. To run it as a background service:

### 1. Create a systemd service file

```bash
sudo nano /etc/systemd/system/hilalon-bot.service
```

### 2. Add the following content

```ini
[Unit]
Description=HilAlon Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/HilAlon_Bot
ExecStart=/usr/bin/python3 /path/to/HilAlon_Bot/telegram_bot.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

### 3. Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable hilalon-bot
sudo systemctl start hilalon-bot
```

### 4. Check status and logs

```bash
sudo systemctl status hilalon-bot
sudo journalctl -u hilalon-bot -f
```

## Security Notes

- **Never commit** `.env`, `credentials.json`, or `token.json` to version control
- The `.gitignore` file is configured to exclude these sensitive files
- Only authorized users (defined in ADMIN_CHAT_ID) can use the bot
- Keep your bot token and credentials secure

## Logging

The bot uses Python's built-in logging module. Logs are output to stdout/stderr and include:
- Bot startup/shutdown events
- User interactions
- Calendar event creation
- Error messages

## Dependencies

See [requirements.txt](requirements.txt) for the complete list. Main dependencies:

- `python-telegram-bot`: Telegram Bot API wrapper
- `google-api-python-client`: Google Calendar API
- `python-dotenv`: Environment variable management
- `pytz`: Timezone handling

## License

This project is for personal use.

## Contributing

This is a personal family scheduling bot. Feel free to fork and adapt for your own use.

## Support

For issues or questions, please open an issue on GitHub.
