import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    google_credentials_file: str
    google_calendar_id: str
    waha_api_url: str
    telegram_bot_token: str
    telegram_chat_id: str
    reminder_minutes: int
    scan_interval: int


def load_config() -> Config:
    load_dotenv()

    required = [
        "GOOGLE_CREDENTIALS_FILE",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    reminder_raw = os.getenv("REMINDER_MINUTES", "15")
    try:
        reminder_minutes = int(reminder_raw)
    except ValueError:
        raise ValueError(f"Invalid REMINDER_MINUTES value: {reminder_raw}")

    scan_raw = os.getenv("SCAN_INTERVAL_MINUTES", "30")
    try:
        scan_interval = int(scan_raw)
    except ValueError:
        raise ValueError(f"Invalid SCAN_INTERVAL_MINUTES value: {scan_raw}")

    return Config(
        google_credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", ""),
        google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        waha_api_url=os.getenv("WAHA_API_URL", "http://localhost:3000"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        reminder_minutes=reminder_minutes,
        scan_interval=scan_interval,
    )
