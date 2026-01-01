import datetime
import os.path
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import config as cfg

logger = logging.getLogger(__name__)

# Calendar access permissions
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service():
    """
    Function responsible for connecting to Google.
    If it's the first time, a browser window will open for authorization.
    After that, a token.json file will be created to save the connection.
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(cfg.CALENDAR_CREDENTIALS_FILE):
                raise FileNotFoundError(f"Missing credentials file: {cfg.CALENDAR_CREDENTIALS_FILE}")

            flow = InstalledAppFlow.from_client_secrets_file(
                cfg.CALENDAR_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_console()

        # Save token for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service


def get_next_weekday(start_date, weekday_index):
    """
    Calculates the nearest date of a specific day of the week.
    weekday_index: 0=Sunday, 1=Monday ... 6=Saturday (according to our indices)
    """
    # Convert to Python's weekday indices (0=Monday, 6=Sunday)
    # Our format: 0=Sunday -> Python: 6
    # Our format: 1=Monday -> Python: 0
    python_weekday = (weekday_index - 1) % 7

    days_ahead = python_weekday - start_date.weekday()
    if days_ahead <= 0:
        # If this day has already passed this week (or is today), set to next week
        days_ahead += 7

    return start_date + datetime.timedelta(days=days_ahead)


def create_event(service, summary, description, start_dt, end_dt,
                 color_id=None, reminder_minutes=(30, 10)):

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'Asia/Jerusalem',
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'Asia/Jerusalem',
        },
    }

    if color_id:
        event['colorId'] = color_id

    if reminder_minutes:
        mins = sorted({int(m) for m in reminder_minutes if m and int(m) > 0}, reverse=True)

        event['reminders'] = {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': m} for m in mins
            ]
        }

    try:
        service.events().insert(calendarId=cfg.CALENDAR_ID, body=event).execute()
        logger.info(f"Created event: {summary} at {start_dt}")
        return True
    except Exception as e:
        logger.error(f"Failed to create event {summary}: {e}")
        return False



def create_weekly_events_in_calendar(schedule_obj, bot_data):
    """
    The main function!
    Receives the schedule object (WeeklySchedule) created in the bot,
    iterates over it and creates all events in Google Calendar.
    """
    service = get_calendar_service()
    today = datetime.date.today()
    created_count = 0

    # --- 1. Pickups (Sunday to Friday) ---
    for day_idx in range(6):  # 0-5 (Sunday to Friday)
        target_date = get_next_weekday(today, day_idx)

        # Determine drivers
        if day_idx in schedule_obj.hila_pickup_indices:
            morning_driver = "הילה"
            return_driver = "אלון"
        else:
            morning_driver = "אלון"
            return_driver = "הילה"

        # --- A. Create morning pickup event ---
        start_iso = f"{target_date}T{cfg.DRIVE_START_TIME}"
        end_iso = f"{target_date}T{cfg.DRIVE_END_TIME}"

        dt_start = datetime.datetime.fromisoformat(start_iso)
        dt_end = datetime.datetime.fromisoformat(end_iso)

        create_event(service, f"🎒 {morning_driver} על אלה וקימל", "Created by HilAlon Bot", dt_start, dt_end, color_id=cfg.COLOR_ID)
        created_count += 1

        # --- B. Create return event (afternoon) ---
        # Set return times (using RETURN_START_TIME)
        return_start_time = cfg.RETURN_START_TIME
        return_end_time = cfg.RETURN_END_TIME

        # If Friday has a shorter day (different from 16:30), add logic here:
        if day_idx == 5:
           return_start_time = cfg.FRIDAY_RETURN_START_TIME
           return_end_time = cfg.FRIDAY_RETURN_END_TIME

        return_start_iso = f"{target_date}T{return_start_time}"
        return_end_iso = f"{target_date}T{return_end_time}"

        dt_return_start = datetime.datetime.fromisoformat(return_start_iso)
        dt_return_end = datetime.datetime.fromisoformat(return_end_iso)

        # Create the event
        create_event(service, f"🏠 {return_driver} על אלה וקימל", "Created by HilAlon Bot", dt_return_start, dt_return_end, color_id=cfg.COLOR_ID)
        created_count += 1

    # --- 2. Hila's date night + reminder ---
    if schedule_obj.hila_date_index is not None:
        date_day = get_next_weekday(today, schedule_obj.hila_date_index)

        # A. Create date night event
        dt_start = datetime.datetime.fromisoformat(f"{date_day}T{cfg.DATENIGHT_START_TIME}")
        dt_end = datetime.datetime.fromisoformat(f"{date_day}T{cfg.DATENIGHT_END_TIME}")

        create_event(service, "🍷 דייט הילה", "Created by HilAlon Bot", dt_start, dt_end, color_id=cfg.COLOR_ID, reminder_minutes=[60])
        created_count += 1

        reminder_date = date_day - datetime.timedelta(days=cfg.BABYSITTER_REMINDER_DAYS_BEFORE)  # 3 days

        rem_start = f"{reminder_date}T{cfg.BABYSITTER_REMINDER_START_TIME}"
        rem_end = f"{reminder_date}T{cfg.BABYSITTER_REMINDER_END_TIME}"

        dt_rem_start = datetime.datetime.fromisoformat(rem_start)
        dt_rem_end = datetime.datetime.fromisoformat(rem_end)

        create_event(
            service,
            "⏰ בייביסיטר: הילה דואגת",
            "Created by HilAlon Bot",
            dt_rem_start,
            dt_rem_end,
            color_id=cfg.COLOR_ID,
            reminder_minutes=[0]
        )
        created_count += 1

    # --- 3. Alon's date night + reminder ---
    if schedule_obj.alon_date_index is not None:
        date_day = get_next_weekday(today, schedule_obj.alon_date_index)

        # A. Create date night event
        dt_start = datetime.datetime.fromisoformat(f"{date_day}T{cfg.DATENIGHT_START_TIME}")
        dt_end = datetime.datetime.fromisoformat(f"{date_day}T{cfg.DATENIGHT_END_TIME}")

        create_event(service, "🍺 דייט אלון", "Created by HilAlon Bot", dt_start, dt_end, color_id=cfg.COLOR_ID, reminder_minutes=[60])
        created_count += 1

        # B. Create babysitter reminder (3 days before)
        reminder_date = date_day - datetime.timedelta(days=cfg.BABYSITTER_REMINDER_DAYS_BEFORE)  # 3 days

        rem_start = f"{reminder_date}T{cfg.BABYSITTER_REMINDER_START_TIME}"
        rem_end = f"{reminder_date}T{cfg.BABYSITTER_REMINDER_END_TIME}"

        dt_rem_start = datetime.datetime.fromisoformat(rem_start)
        dt_rem_end = datetime.datetime.fromisoformat(rem_end)

        create_event(
            service,
            "⏰ בייביסיטר: אלון דואג",
            "Created by HilAlon Bot",
            dt_rem_start,
            dt_rem_end,
            color_id=cfg.COLOR_ID,
            reminder_minutes=[0]
        )
        created_count += 1

    # --- 4. Kimel to kindergarten ---
    kimel_counter = bot_data.get(cfg.KIMEL_COUNTER_KEY, cfg.KIMEL_INITIAL_COUNT)

    for day_idx in schedule_obj.kimel_indices:
        target_date = get_next_weekday(today, day_idx)

        # Update the title with current counter
        title = f"🧸 קימל בגן מס' {kimel_counter}"

        # Create Kimel event
        start_iso = f"{target_date}T{cfg.KINDERGARTEN_START_TIME}"
        end_iso = f"{target_date}T{cfg.KINDERGARTEN_END_TIME}"
        dt_start = datetime.datetime.fromisoformat(start_iso)
        dt_end = datetime.datetime.fromisoformat(end_iso)

        create_event(service, title, "Created by HilAlon Bot", dt_start, dt_end, color_id=cfg.COLOR_ID)
        created_count += 1


        kimel_counter += 1
        if kimel_counter > cfg.KIMEL_MAX_COUNT:
            kimel_counter = cfg.KIMEL_RESET_COUNT  # Reset to 1 after reaching max

    bot_data[cfg.KIMEL_COUNTER_KEY] = kimel_counter

    return f"✅ הסתיים בהצלחה! נוצרו {created_count} אירועים ביומן."