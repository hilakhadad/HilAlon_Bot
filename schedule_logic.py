from config import HEBREW_DAYS, KINDERGARTEN_START_TIME, KINDERGARTEN_END_TIME


class WeeklySchedule:
    """
    Class that manages the state of the weekly schedule.
    Each user will receive their own instance of this class.
    """

    def __init__(self):
        # Lists of numbers (0-6 representing days of the week)
        self.hila_pickup_indices = []
        self.hila_date_index = None
        self.alon_date_index = None
        self.kimel_indices = []

        # --- Functions for managing selections (Logic) ---

    def toggle_pickup(self, day_index):
        if day_index in self.hila_pickup_indices:
            self.hila_pickup_indices.remove(day_index)
        else:
            self.hila_pickup_indices.append(day_index)
            self.hila_pickup_indices.sort()

    def set_date_hila(self, day_index):
        self.hila_date_index = day_index

    def set_date_alon(self, day_index):
        self.alon_date_index = day_index

    def toggle_kimel(self, day_index):
        if day_index in self.kimel_indices:
            self.kimel_indices.remove(day_index)
        else:
            self.kimel_indices.append(day_index)
            self.kimel_indices.sort()

    def clear_kimel(self):
        self.kimel_indices = []

    # --- Function that generates summary text ---
    def get_summary_text(self):
        # Convert from numbers (0,1) to day names
        hila_pu_names = [HEBREW_DAYS[i] for i in self.hila_pickup_indices]
        kimel_names = [HEBREW_DAYS[i] for i in self.kimel_indices]

        hila_date = HEBREW_DAYS[self.hila_date_index] if self.hila_date_index is not None else "לא נבחר"
        alon_date = HEBREW_DAYS[self.alon_date_index] if self.alon_date_index is not None else "לא נבחר"

        return (
            "📋 **סיכום לו\"ז שבועי:**\n\n"
            f"🎒 **איסוף הילה:** {', '.join(hila_pu_names) if hila_pu_names else 'ללא'}\n"
            f"🍷 **דייט הילה:** {hila_date}\n"
            f"🍺 **דייט אלון:** {alon_date}\n"
            f"🧸 **קימל בגן ({KINDERGARTEN_START_TIME}-{KINDERGARTEN_END_TIME}):**\n"
            f"   {', '.join(kimel_names) if kimel_names else 'ללא'}"
        )


# Helper function to retrieve the object from Telegram's Context
def get_schedule(context) -> WeeklySchedule:
    if 'schedule_obj' not in context.user_data:
        context.user_data['schedule_obj'] = WeeklySchedule()
    return context.user_data['schedule_obj']