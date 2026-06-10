import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


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


def load_config() -> Config:
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
    values["reminder_minutes"] = int(os.getenv("REMINDER_MINUTES", "15"))
    return Config(**values)
