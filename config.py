import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    google_credentials_file: str
    google_calendar_id: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    telegram_bot_token: str
    telegram_chat_id: str
    reminder_minutes: int
    scan_interval_minutes: int


def load_config() -> Config:
    load_dotenv()

    required = {
        "GOOGLE_CREDENTIALS_FILE": "google_credentials_file",
        "TWILIO_ACCOUNT_SID": "twilio_account_sid",
        "TWILIO_AUTH_TOKEN": "twilio_auth_token",
        "TWILIO_FROM_NUMBER": "twilio_from_number",
        "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
        "TELEGRAM_CHAT_ID": "telegram_chat_id",
    }
    values = {}
    for env_key, attr in required.items():
        value = os.getenv(env_key, "")
        if not value:
            raise ValueError(f"Missing required env var: {env_key}")
        values[attr] = value

    values["google_calendar_id"] = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    reminder_raw = os.getenv("REMINDER_MINUTES", "15")
    try:
        values["reminder_minutes"] = int(reminder_raw)
    except ValueError:
        raise ValueError(f"Invalid REMINDER_MINUTES value: {reminder_raw}")

    scan_raw = os.getenv("SCAN_INTERVAL_MINUTES", "30")
    try:
        values["scan_interval_minutes"] = int(scan_raw)
    except ValueError:
        raise ValueError(f"Invalid SCAN_INTERVAL_MINUTES value: {scan_raw}")

    return Config(**values)
