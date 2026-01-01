import sys, os
import pytz

# --- 1. TELEGRAM SETTINGS ---
# Values are loaded from environment variables
# If not set, the bot will use default values for error identification

# ⚠️ Required environment variable (TELEGRAM_BOT_TOKEN)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "enter_your_bot_token_here")

# ⚠️ Required environment variable (ADMIN_CHAT_ID)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "enter_your_chat_id_here")

# Weekly reminder scheduling
REMINDER_HOUR = 20  # 20:00 (8 PM)
REMINDER_MINUTE = 0
REMINDER_DAY_OF_WEEK = 3  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun (APScheduler format)

# --- 2. GOOGLE CALENDAR SETTINGS ---
# Credentials file created after Google Cloud registration


def resource_path(rel):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.dirname(__file__), rel)


CALENDAR_CREDENTIALS_FILE = resource_path("credentials.json")

# ⚠️ Required environment variable (CALENDAR_ID)
CALENDAR_ID = os.getenv("CALENDAR_ID", "enter_your_calendar_id_here")

# Timezone setting (very important for event accuracy)
TIME_ZONE = pytz.timezone('Asia/Jerusalem')

# --- 3. EVENT TIMES (HH:MM:SS format) ---

# Morning school drive
DRIVE_START_TIME = "07:30:00"
DRIVE_END_TIME = "08:00:00"

# School pickup (afternoon) - Sunday to Thursday
RETURN_START_TIME = "16:00:00"
RETURN_END_TIME = "16:30:00"

FRIDAY_RETURN_START_TIME = "11:30:00"
FRIDAY_RETURN_END_TIME = "12:00:00"

# Kindergarten (Kimel)
KINDERGARTEN_START_TIME = "09:00:00"
KINDERGARTEN_END_TIME = "17:00:00"

# Weekly date night
DATENIGHT_START_TIME = "20:00:00"
DATENIGHT_END_TIME = "22:00:00"

# Babysitter reminder (3 days before date night)
BABYSITTER_REMINDER_START_TIME = "12:00:00"
BABYSITTER_REMINDER_END_TIME = "13:00:00"
BABYSITTER_REMINDER_DAYS_BEFORE = 3

# --- 4. KIMEL COUNTER SETTINGS ---
KIMEL_COUNTER_KEY = "kimel_count"
KIMEL_INITIAL_COUNT = 9  # Initial counter value
KIMEL_MAX_COUNT = 10  # Maximum count before reset
KIMEL_RESET_COUNT = 1  # Value to reset to after reaching max

# --- 5. LOGIC & UI CONSTANTS ---

# Day names for display (indices 0-6)
HEBREW_DAYS = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]

# Conversation states
STATE_PICKUP, STATE_DATE_HILA, STATE_DATE_ALON, STATE_KIMEL, STATE_CONFIRM = range(5)

# Callback data prefixes
# These allow the bot to identify which step a pressed button belongs to
PREFIX_PICKUP = "PU_"
PREFIX_DATE_HILA = "DH_"
PREFIX_DATE_ALON = "DA_"
PREFIX_KIMEL = "KI_"

# Special button actions
ACTION_DONE = "DONE"
ACTION_NONE = "NONE"
ACTION_CONFIRM = "CONFIRM"
ACTION_CANCEL = "CANCEL"

COLOR_ID = '10'

try:
    # 1. Read the string (e.g., "12345,67890")
    ADMIN_IDS_STR = os.environ.get("ADMIN_CHAT_ID", "")

    # 2. Split by comma, filter whitespace, and convert to integers
    AUTHORIZED_USER_IDS = [int(i.strip()) for i in ADMIN_IDS_STR.split(',') if i.strip()]

except ValueError:
    print("⚠️ Error: Ensure ADMIN_CHAT_ID environment variable contains only comma-separated numbers.")
    AUTHORIZED_USER_IDS = []  # Block everyone if there's an error for security