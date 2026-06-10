import re
from datetime import datetime, timedelta, timezone


WHATSAPP_RE = re.compile(r"WhatsApp:\s*(\+?[\d\s\-]+)")
REMINDER_MARKER_RE = re.compile(r"\[已提醒")


def extract_whatsapp_number(description: str) -> str | None:
    if not description:
        return None
    match = WHATSAPP_RE.search(description)
    return match.group(1).strip() if match else None


def is_already_reminded(description: str) -> bool:
    if not description:
        return False
    return bool(REMINDER_MARKER_RE.search(description))


def build_reminder_marker(timestamp: datetime) -> str:
    return f"[已提醒 {timestamp.strftime('%Y-%m-%d %H:%M')}]"


def needs_reminder(
    end_time: datetime,
    now: datetime,
    reminder_minutes: int = 15,
    scan_interval: int = 30,
) -> bool:
    reminder_start = end_time - timedelta(minutes=reminder_minutes)
    reminder_end = reminder_start + timedelta(minutes=scan_interval)
    return reminder_start <= now < reminder_end


def fetch_upcoming_events(service, calendar_id: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])


def mark_event_reminded(service, calendar_id: str, event: dict, now: datetime) -> None:
    description = event.get("description", "")
    marker = build_reminder_marker(now)
    new_description = (description + "\n" + marker).strip()

    service.events().update(
        calendarId=calendar_id,
        eventId=event["id"],
        body={"description": new_description},
    ).execute()
