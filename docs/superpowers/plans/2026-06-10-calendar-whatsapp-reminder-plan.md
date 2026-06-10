# Calendar → WhatsApp Reminder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python cron script that checks Google Calendar every 30 minutes and sends WhatsApp reminders 15 minutes before events end, with Telegram admin notifications.

**Architecture:** Single-entry-point script (`main.py`) with modular components for Google Calendar, Twilio WhatsApp, and Telegram. Cron triggers `main.py` every 30 minutes. No persistent state — reminder status is tracked by writing `[已提醒 ...]` markers into event descriptions.

**Tech Stack:** Python 3.10+, google-api-python-client, twilio, python-telegram-bot, python-dotenv

---

## File Map

| File | Responsibility |
|------|---------------|
| `requirements.txt` | Declare all dependencies |
| `.env.example` | Configuration template |
| `config.py` | Load and validate environment variables |
| `google_calendar.py` | Google Calendar API: fetch events, update description |
| `whatsapp.py` | Twilio API: send WhatsApp message |
| `telegram.py` | Telegram Bot API: send admin notifications |
| `main.py` | Orchestrator: wire everything together, entry point |

---

### Task 1: Project Setup & Config

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.py`

- [ ] **Step 1: Create requirements.txt**

```
google-api-python-client>=2.100.0
google-auth>=2.25.0
twilio>=9.0.0
python-telegram-bot>=20.7
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create .env.example**

```
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_ID=primary
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=whatsapp:+14155238886
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
REMINDER_MINUTES=15
```

- [ ] **Step 3: Write failing test for config.py**

Create `tests/test_config.py`:

```python
import os
import pytest
from config import load_config, Config


def test_load_config_reads_all_required_fields():
    os.environ["GOOGLE_CREDENTIALS_FILE"] = "test_creds.json"
    os.environ["GOOGLE_CALENDAR_ID"] = "primary"
    os.environ["TWILIO_ACCOUNT_SID"] = "AC_test"
    os.environ["TWILIO_AUTH_TOKEN"] = "token_test"
    os.environ["TWILIO_FROM_NUMBER"] = "whatsapp:+15551234567"
    os.environ["TELEGRAM_BOT_TOKEN"] = "bot_test"
    os.environ["TELEGRAM_CHAT_ID"] = "123456789"

    config = load_config()

    assert config.google_credentials_file == "test_creds.json"
    assert config.google_calendar_id == "primary"
    assert config.twilio_account_sid == "AC_test"
    assert config.twilio_auth_token == "token_test"
    assert config.twilio_from_number == "whatsapp:+15551234567"
    assert config.telegram_bot_token == "bot_test"
    assert config.telegram_chat_id == "123456789"


def test_load_config_uses_default_reminder_minutes():
    os.environ["GOOGLE_CREDENTIALS_FILE"] = "test_creds.json"
    os.environ["TWILIO_ACCOUNT_SID"] = "AC_test"
    os.environ["TWILIO_AUTH_TOKEN"] = "token_test"
    os.environ["TWILIO_FROM_NUMBER"] = "whatsapp:+15551234567"
    os.environ["TELEGRAM_BOT_TOKEN"] = "bot_test"
    os.environ["TELEGRAM_CHAT_ID"] = "123456789"

    config = load_config()
    assert config.reminder_minutes == 15


def test_load_config_missing_required_raises():
    os.environ.pop("TWILIO_ACCOUNT_SID", None)
    with pytest.raises(ValueError, match="TWILIO_ACCOUNT_SID"):
        load_config()
```

- [ ] **Step 4: Run tests to verify they fail**

```
pytest tests/test_config.py -v
```
Expected: 3 FAIL (Config not defined)

- [ ] **Step 5: Write config.py**

```python
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
```

- [ ] **Step 6: Run tests to verify they pass**

```
pytest tests/test_config.py -v
```
Expected: 3 PASS

- [ ] **Step 7: Commit**

```
git add requirements.txt .env.example config.py tests/test_config.py
git commit -m "feat: add project setup and config module"
```

---

### Task 2: Google Calendar Module

**Files:**
- Create: `google_calendar.py`
- Create: `tests/test_google_calendar.py`

- [ ] **Step 1: Write failing tests for google_calendar.py**

Create `tests/test_google_calendar.py`:

```python
import re
from unittest.mock import MagicMock, patch
from google_calendar import (
    extract_whatsapp_number,
    is_already_reminded,
    build_reminder_marker,
    needs_reminder,
    fetch_upcoming_events,
    mark_event_reminded,
)


def test_extract_whatsapp_number_with_prefix():
    desc = "WhatsApp: +85212345678\nName: Chan"
    assert extract_whatsapp_number(desc) == "+85212345678"


def test_extract_whatsapp_number_without_plus():
    desc = "WhatsApp: 85212345678\nNotes here"
    assert extract_whatsapp_number(desc) == "85212345678"


def test_extract_whatsapp_number_with_spaces():
    desc = "WhatsApp: +852 1234 5678\nOther"
    assert extract_whatsapp_number(desc) == "+852 1234 5678"


def test_extract_whatsapp_number_not_found():
    desc = "No phone here"
    assert extract_whatsapp_number(desc) is None


def test_is_already_reminded_true():
    desc = "WhatsApp: +85212345678\n[已提醒 2026-06-10 15:30]"
    assert is_already_reminded(desc) is True


def test_is_already_reminded_false():
    desc = "WhatsApp: +85212345678\nSome notes"
    assert is_already_reminded(desc) is False


def test_build_reminder_marker():
    from datetime import datetime
    now = datetime(2026, 6, 10, 15, 30)
    marker = build_reminder_marker(now)
    assert marker == "[已提醒 2026-06-10 15:30]"


def test_needs_reminder_in_window():
    from datetime import datetime, timedelta
    now = datetime(2026, 6, 10, 15, 20)
    end_time = datetime(2026, 6, 10, 15, 35)
    assert needs_reminder(end_time, now, reminder_minutes=15, scan_interval=30) is True


def test_needs_reminder_too_early():
    from datetime import datetime, timedelta
    now = datetime(2026, 6, 10, 14, 00)
    end_time = datetime(2026, 6, 10, 15, 35)
    assert needs_reminder(end_time, now, reminder_minutes=15, scan_interval=30) is False


def test_needs_reminder_too_late():
    from datetime import datetime, timedelta
    now = datetime(2026, 6, 10, 15, 55)
    end_time = datetime(2026, 6, 10, 15, 35)
    assert needs_reminder(end_time, now, reminder_minutes=15, scan_interval=30) is False


def test_fetch_upcoming_events_returns_list():
    mock_service = MagicMock()
    mock_events = MagicMock()
    mock_list = MagicMock()
    fake_event = {
        "id": "evt123",
        "summary": "Test Event",
        "start": {"dateTime": "2026-06-10T15:00:00+08:00"},
        "end": {"dateTime": "2026-06-10T15:35:00+08:00"},
        "description": "WhatsApp: +85212345678",
    }
    mock_list.execute.return_value = {"items": [fake_event]}
    mock_events.list.return_value = mock_list
    mock_service.events.return_value = mock_events

    result = fetch_upcoming_events(mock_service, "primary")
    assert len(result) == 1
    assert result[0]["id"] == "evt123"


def test_mark_event_reminded_appends_marker():
    from datetime import datetime
    mock_service = MagicMock()
    mock_events = MagicMock()
    mock_update = MagicMock()
    mock_service.events.return_value = mock_events
    mock_events.update.return_value = mock_update
    mock_update.execute.return_value = {}

    event = {
        "id": "evt123",
        "description": "WhatsApp: +85212345678\nNotes",
    }
    now = datetime(2026, 6, 10, 15, 30)

    mark_event_reminded(mock_service, "primary", event, now)

    mock_events.update.assert_called_once()
    updated_body = mock_events.update.call_args[1]["body"]
    assert "[已提醒 2026-06-10 15:30]" in updated_body["description"]
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_google_calendar.py -v
```
Expected: 10 FAIL (module not found)

- [ ] **Step 3: Write google_calendar.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_google_calendar.py -v
```
Expected: 10 PASS

- [ ] **Step 5: Commit**

```
git add google_calendar.py tests/test_google_calendar.py
git commit -m "feat: add Google Calendar module"
```

---

### Task 3: WhatsApp Module

**Files:**
- Create: `whatsapp.py`
- Create: `tests/test_whatsapp.py`

- [ ] **Step 1: Write failing tests for whatsapp.py**

Create `tests/test_whatsapp.py`:

```python
from unittest.mock import MagicMock, patch
from whatsapp import send_whatsapp_reminder


def test_send_whatsapp_reminder_formats_message():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(sid="SM_test123")

    result = send_whatsapp_reminder(
        client=mock_client,
        from_number="whatsapp:+14155238886",
        to_number="+85212345678",
        event_title="Doctor Appointment",
        end_time_str="15:30",
    )

    assert result is True
    call_args = mock_client.messages.create.call_args[1]
    assert call_args["from_"] == "whatsapp:+14155238886"
    assert call_args["to"] == "whatsapp:+85212345678"
    assert "Doctor Appointment" in call_args["body"]
    assert "15:30" in call_args["body"]


def test_send_whatsapp_reminder_returns_false_on_error():
    from twilio.base.exceptions import TwilioRestException
    mock_client = MagicMock()
    mock_response = MagicMock(status=400)
    mock_client.messages.create.side_effect = TwilioRestException(
        "Bad request", "http://example.com", status=400
    )

    result = send_whatsapp_reminder(
        client=mock_client,
        from_number="whatsapp:+14155238886",
        to_number="+85212345678",
        event_title="Test",
        end_time_str="15:30",
    )

    assert result is False
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_whatsapp.py -v
```
Expected: 2 FAIL (module not found)

- [ ] **Step 3: Write whatsapp.py**

```python
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


MESSAGE_TEMPLATE = "溫馨提示：您的預約「{title}」將於 {time} 結束，請準時出席。"


def send_whatsapp_reminder(
    client: Client,
    from_number: str,
    to_number: str,
    event_title: str,
    end_time_str: str,
) -> bool:
    body = MESSAGE_TEMPLATE.format(title=event_title, time=end_time_str)
    try:
        client.messages.create(
            from_=from_number,
            to=f"whatsapp:{to_number}",
            body=body,
        )
        return True
    except TwilioRestException:
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_whatsapp.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```
git add whatsapp.py tests/test_whatsapp.py
git commit -m "feat: add WhatsApp module"
```

---

### Task 4: Telegram Module

**Files:**
- Create: `telegram.py`
- Create: `tests/test_telegram.py`

- [ ] **Step 1: Write failing tests for telegram.py**

Create `tests/test_telegram.py`:

```python
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import notify_success, notify_skip, notify_failure, notify_system_error


def test_notify_success_formats_message():
    mock_bot = AsyncMock()
    result = notify_success(
        bot=mock_bot,
        chat_id="123",
        event_title="Doctor",
        end_time_str="15:30",
        whatsapp_number="+85212345678",
    )
    assert result is True
    call_args = mock_bot.send_message.call_args[1]
    assert call_args["chat_id"] == "123"
    assert "✅" in call_args["text"]
    assert "Doctor" in call_args["text"]
    assert "15:30" in call_args["text"]
    assert "+85212345678" in call_args["text"]


def test_notify_skip_formats_message():
    mock_bot = AsyncMock()
    result = notify_skip(
        bot=mock_bot,
        chat_id="123",
        event_title="Doctor",
        end_time_str="15:30",
    )
    assert result is True
    text = mock_bot.send_message.call_args[1]["text"]
    assert "⚠️" in text
    assert "Doctor" in text
    assert "15:30" in text
    assert "無 WhatsApp 號碼" in text


def test_notify_failure_formats_message():
    mock_bot = AsyncMock()
    result = notify_failure(
        bot=mock_bot,
        chat_id="123",
        event_title="Doctor",
        whatsapp_number="+85212345678",
        error_message="Invalid phone",
    )
    assert result is True
    text = mock_bot.send_message.call_args[1]["text"]
    assert "❌" in text
    assert "Doctor" in text
    assert "+85212345678" in text
    assert "Invalid phone" in text


def test_notify_system_error_formats_message():
    mock_bot = AsyncMock()
    result = notify_system_error(
        bot=mock_bot,
        chat_id="123",
        error_detail="Google API timeout",
    )
    assert result is True
    text = mock_bot.send_message.call_args[1]["text"]
    assert "🚨" in text
    assert "Google API timeout" in text


def test_notify_handles_telegram_error():
    from telegram.error import TelegramError
    mock_bot = AsyncMock()
    mock_bot.send_message.side_effect = TelegramError("Network error")
    result = notify_system_error(
        bot=mock_bot,
        chat_id="123",
        error_detail="test",
    )
    assert result is False
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_telegram.py -v
```
Expected: 5 FAIL (module not found)

- [ ] **Step 3: Write telegram.py**

```python
from telegram import Bot
from telegram.error import TelegramError


async def _send(bot: Bot, chat_id: str, text: str) -> bool:
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        return True
    except TelegramError:
        return False


async def notify_success(
    bot: Bot,
    chat_id: str,
    event_title: str,
    end_time_str: str,
    whatsapp_number: str,
) -> bool:
    text = (
        f"✅ 已發送提醒\n"
        f"Event: {event_title}\n"
        f"時間: {end_time_str} 結束\n"
        f"WhatsApp: {whatsapp_number}"
    )
    return await _send(bot, chat_id, text)


async def notify_skip(
    bot: Bot,
    chat_id: str,
    event_title: str,
    end_time_str: str,
) -> bool:
    text = (
        f"⚠️ 跳過 Event（無 WhatsApp 號碼）\n"
        f"Event: {event_title}\n"
        f"時間: {end_time_str} 結束"
    )
    return await _send(bot, chat_id, text)


async def notify_failure(
    bot: Bot,
    chat_id: str,
    event_title: str,
    whatsapp_number: str,
    error_message: str,
) -> bool:
    text = (
        f"❌ 發送失敗\n"
        f"Event: {event_title}\n"
        f"WhatsApp: {whatsapp_number}\n"
        f"錯誤: {error_message}"
    )
    return await _send(bot, chat_id, text)


async def notify_system_error(
    bot: Bot,
    chat_id: str,
    error_detail: str,
) -> bool:
    text = f"🚨 系統錯誤\ndetail: {error_detail}"
    return await _send(bot, chat_id, text)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_telegram.py -v
```
Expected: 5 PASS

- [ ] **Step 5: Commit**

```
git add telegram.py tests/test_telegram.py
git commit -m "feat: add Telegram notification module"
```

---

### Task 5: Main Orchestrator

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing test for main.py**

Create `tests/test_main.py`:

```python
from unittest.mock import MagicMock, AsyncMock, patch, call
from datetime import datetime, timedelta, timezone
import main


def test_process_event_with_valid_whatsapp_and_in_window():
    now = datetime(2026, 6, 10, 15, 20, tzinfo=timezone(timedelta(hours=8)))
    end_time = datetime(2026, 6, 10, 15, 35, tzinfo=timezone(timedelta(hours=8)))

    event = {
        "id": "evt1",
        "summary": "Doctor Appointment",
        "start": {"dateTime": "2026-06-10T15:00:00+08:00"},
        "end": {"dateTime": end_time.isoformat()},
        "description": "WhatsApp: +85212345678\nNotes",
    }

    mock_calendar = MagicMock()
    mock_whatsapp = MagicMock()
    mock_telegram = AsyncMock()

    mock_whatsapp.send_whatsapp_reminder.return_value = True

    main.process_event(
        event=event,
        calendar_service=mock_calendar,
        calendar_id="primary",
        twilio_client=mock_whatsapp,
        twilio_from="whatsapp:+14155238886",
        telegram_bot=mock_telegram,
        telegram_chat_id="123",
        now=now,
        reminder_minutes=15,
        scan_interval=30,
    )

    mock_whatsapp.send_whatsapp_reminder.assert_called_once()
    mock_telegram.send_message.assert_called_once()
    assert "✅" in mock_telegram.send_message.call_args[1]["text"]


def test_process_event_skips_already_reminded():
    now = datetime(2026, 6, 10, 15, 20, tzinfo=timezone(timedelta(hours=8)))
    end_time = datetime(2026, 6, 10, 15, 35, tzinfo=timezone(timedelta(hours=8)))

    event = {
        "id": "evt2",
        "summary": "Already Done",
        "start": {"dateTime": "2026-06-10T15:00:00+08:00"},
        "end": {"dateTime": end_time.isoformat()},
        "description": "WhatsApp: +85212345678\n[已提醒 2026-06-10 15:20]",
    }

    mock_calendar = MagicMock()
    mock_whatsapp = MagicMock()
    mock_telegram = AsyncMock()

    main.process_event(
        event=event,
        calendar_service=mock_calendar,
        calendar_id="primary",
        twilio_client=mock_whatsapp,
        twilio_from="whatsapp:+14155238886",
        telegram_bot=mock_telegram,
        telegram_chat_id="123",
        now=now,
        reminder_minutes=15,
        scan_interval=30,
    )

    mock_whatsapp.send_whatsapp_reminder.assert_not_called()
    mock_telegram.send_message.assert_not_called()


def test_process_event_skips_no_whatsapp_number():
    now = datetime(2026, 6, 10, 15, 20, tzinfo=timezone(timedelta(hours=8)))
    end_time = datetime(2026, 6, 10, 15, 35, tzinfo=timezone(timedelta(hours=8)))

    event = {
        "id": "evt3",
        "summary": "No Number",
        "start": {"dateTime": "2026-06-10T15:00:00+08:00"},
        "end": {"dateTime": end_time.isoformat()},
        "description": "No WhatsApp here",
    }

    mock_calendar = MagicMock()
    mock_whatsapp = MagicMock()
    mock_telegram = AsyncMock()

    main.process_event(
        event=event,
        calendar_service=mock_calendar,
        calendar_id="primary",
        twilio_client=mock_whatsapp,
        twilio_from="whatsapp:+14155238886",
        telegram_bot=mock_telegram,
        telegram_chat_id="123",
        now=now,
        reminder_minutes=15,
        scan_interval=30,
    )

    mock_whatsapp.send_whatsapp_reminder.assert_not_called()
    mock_telegram.send_message.assert_called_once()
    assert "⚠️" in mock_telegram.send_message.call_args[1]["text"]


def test_process_event_whatsapp_failure_does_not_mark():
    now = datetime(2026, 6, 10, 15, 20, tzinfo=timezone(timedelta(hours=8)))
    end_time = datetime(2026, 6, 10, 15, 35, tzinfo=timezone(timedelta(hours=8)))

    event = {
        "id": "evt4",
        "summary": "Fail Event",
        "start": {"dateTime": "2026-06-10T15:00:00+08:00"},
        "end": {"dateTime": end_time.isoformat()},
        "description": "WhatsApp: +85212345678",
    }

    mock_calendar = MagicMock()
    mock_whatsapp = MagicMock()
    mock_telegram = AsyncMock()

    mock_whatsapp.send_whatsapp_reminder.return_value = False

    main.process_event(
        event=event,
        calendar_service=mock_calendar,
        calendar_id="primary",
        twilio_client=mock_whatsapp,
        twilio_from="whatsapp:+14155238886",
        telegram_bot=mock_telegram,
        telegram_chat_id="123",
        now=now,
        reminder_minutes=15,
        scan_interval=30,
    )

    mock_whatsapp.send_whatsapp_reminder.assert_called_once()
    mock_calendar.events.assert_not_called()
    assert "❌" in mock_telegram.send_message.call_args[1]["text"]
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_main.py -v
```
Expected: 4 FAIL (main.py not found)

- [ ] **Step 3: Write main.py**

```python
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
from telegram import notify_success, notify_skip, notify_failure, notify_system_error


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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_main.py -v
```
Expected: 4 PASS

- [ ] **Step 5: Run all tests**

```
pytest tests/ -v
```
Expected: all 24 tests PASS

- [ ] **Step 6: Commit**

```
git add main.py tests/test_main.py
git commit -m "feat: add main orchestrator"
```

---

### Task 6: Final Verification

- [ ] **Step 1: Create tests/conftest.py for shared fixtures if needed, and run full test suite**

```
pytest tests/ -v
```

- [ ] **Step 2: Verify all modules can be imported without errors**

```
python -c "from config import load_config; from google_calendar import extract_whatsapp_number; from whatsapp import send_whatsapp_reminder; from telegram import notify_success; print('All imports OK')"
```

- [ ] **Step 3: Verify requirements.txt is installable**

```
pip install -r requirements.txt --dry-run
```

- [ ] **Step 4: Commit final verification**

```
git add -A
git commit -m "chore: final verification and cleanup"
```
