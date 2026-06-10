import sys
import asyncio
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build
from twilio.rest import Client
from telegram import Bot

from config import load_config
from google_calendar import (
    extract_whatsapp_number,
    is_already_reminded,
    needs_reminder,
    fetch_upcoming_events,
    mark_event_reminded,
)
from whatsapp import send_whatsapp_reminder
from telegram_notifier import notify_success, notify_skip, notify_failure, notify_system_error


async def process_event(
    event: dict,
    calendar_service,
    calendar_id: str,
    twilio_client: Client,
    twilio_from: str,
    telegram_bot: Bot,
    telegram_chat_id: str,
    now: datetime,
    reminder_minutes: int,
    scan_interval: int,
) -> None:
    description = event.get("description", "")
    event_title = event.get("summary", "(no title)")

    end_str = event.get("end", {}).get("dateTime", "")
    if not end_str:
        return
    end_time = datetime.fromisoformat(end_str)

    if not needs_reminder(end_time, now, reminder_minutes, scan_interval):
        return

    if is_already_reminded(description):
        return

    end_time_str = end_time.strftime("%H:%M")

    whatsapp_number = extract_whatsapp_number(description)
    if whatsapp_number is None:
        await notify_skip(telegram_bot, telegram_chat_id, event_title, end_time_str)
        return

    success = send_whatsapp_reminder(
        client=twilio_client,
        from_number=twilio_from,
        to_number=whatsapp_number,
        event_title=event_title,
        end_time_str=end_time_str,
    )

    if success:
        mark_event_reminded(calendar_service, calendar_id, event, now)
        await notify_success(
            telegram_bot, telegram_chat_id, event_title, end_time_str, whatsapp_number
        )
    else:
        await notify_failure(
            telegram_bot,
            telegram_chat_id,
            event_title,
            whatsapp_number,
            "Twilio send failed",
        )


async def run() -> None:
    config = load_config()

    credentials = service_account.Credentials.from_service_account_file(
        config.google_credentials_file,
        scopes=["https://www.googleapis.com/auth/calendar.events"],
    )
    calendar_service = build("calendar", "v3", credentials=credentials)

    twilio_client = Client(config.twilio_account_sid, config.twilio_auth_token)
    telegram_bot = Bot(token=config.telegram_bot_token)

    now = datetime.now(timezone.utc)
    events = fetch_upcoming_events(calendar_service, config.google_calendar_id)

    for event in events:
        try:
            await process_event(
                event=event,
                calendar_service=calendar_service,
                calendar_id=config.google_calendar_id,
                twilio_client=twilio_client,
                twilio_from=config.twilio_from_number,
                telegram_bot=telegram_bot,
                telegram_chat_id=config.telegram_chat_id,
                now=now,
                reminder_minutes=config.reminder_minutes,
                scan_interval=30,
            )
        except Exception as e:
            await notify_system_error(telegram_bot, config.telegram_chat_id, str(e))


def main():
    try:
        asyncio.run(run())
    except Exception as e:
        config = load_config()
        bot = Bot(token=config.telegram_bot_token)
        asyncio.run(notify_system_error(bot, config.telegram_chat_id, str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
