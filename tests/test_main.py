from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
import asyncio
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
    mock_telegram_bot = AsyncMock()

    with patch("main.send_whatsapp_reminder", return_value=(True, "")) as mock_send_whatsapp, \
         patch("main.mark_event_reminded", return_value=True) as mock_mark:
        asyncio.run(main.process_event(
            event=event,
            calendar_service=mock_calendar,
            calendar_id="primary",
            waha_api_url="http://localhost:3000",
            telegram_bot=mock_telegram_bot,
            telegram_chat_id="123",
            now=now,
            reminder_minutes=15,
            scan_interval=30,
        ))

        mock_send_whatsapp.assert_called_once()
        mock_mark.assert_called_once()
        mock_telegram_bot.send_message.assert_called_once()
        assert "\u2705" in mock_telegram_bot.send_message.call_args[1]["text"]


def test_process_event_skips_already_reminded():
    now = datetime(2026, 6, 10, 15, 20, tzinfo=timezone(timedelta(hours=8)))
    end_time = datetime(2026, 6, 10, 15, 35, tzinfo=timezone(timedelta(hours=8)))

    event = {
        "id": "evt2",
        "summary": "Already Done",
        "start": {"dateTime": "2026-06-10T15:00:00+08:00"},
        "end": {"dateTime": end_time.isoformat()},
        "description": "WhatsApp: +85212345678\n[\u5df2\u63d0\u9192 2026-06-10 15:20]",
    }

    mock_calendar = MagicMock()
    mock_telegram_bot = AsyncMock()

    with patch("main.send_whatsapp_reminder") as mock_send_whatsapp:
        asyncio.run(main.process_event(
            event=event,
            calendar_service=mock_calendar,
            calendar_id="primary",
            waha_api_url="http://localhost:3000",
            telegram_bot=mock_telegram_bot,
            telegram_chat_id="123",
            now=now,
            reminder_minutes=15,
            scan_interval=30,
        ))

        mock_send_whatsapp.assert_not_called()
        mock_telegram_bot.send_message.assert_not_called()


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
    mock_telegram_bot = AsyncMock()

    with patch("main.send_whatsapp_reminder") as mock_send_whatsapp:
        asyncio.run(main.process_event(
            event=event,
            calendar_service=mock_calendar,
            calendar_id="primary",
            waha_api_url="http://localhost:3000",
            telegram_bot=mock_telegram_bot,
            telegram_chat_id="123",
            now=now,
            reminder_minutes=15,
            scan_interval=30,
        ))

        mock_send_whatsapp.assert_not_called()
        mock_telegram_bot.send_message.assert_called_once()
        assert "\u26a0\ufe0f" in mock_telegram_bot.send_message.call_args[1]["text"]


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
    mock_telegram_bot = AsyncMock()

    with patch("main.send_whatsapp_reminder", return_value=(False, "Bad request")) as mock_send_whatsapp, \
         patch("main.mark_event_reminded") as mock_mark:
        asyncio.run(main.process_event(
            event=event,
            calendar_service=mock_calendar,
            calendar_id="primary",
            waha_api_url="http://localhost:3000",
            telegram_bot=mock_telegram_bot,
            telegram_chat_id="123",
            now=now,
            reminder_minutes=15,
            scan_interval=30,
        ))

        mock_send_whatsapp.assert_called_once()
        mock_mark.assert_not_called()
        assert "\u274c" in mock_telegram_bot.send_message.call_args[1]["text"]
