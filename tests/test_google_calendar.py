from unittest.mock import MagicMock
from google_calendar import (
    extract_whatsapp_number,
    is_already_reminded,
    _build_reminder_marker,
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
    assert extract_whatsapp_number(desc) == "+85212345678"


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
    marker = _build_reminder_marker(now)
    assert marker == "[已提醒 2026-06-10 15:30]"


def test_needs_reminder_in_window():
    from datetime import datetime
    now = datetime(2026, 6, 10, 15, 20)
    end_time = datetime(2026, 6, 10, 15, 35)
    assert needs_reminder(end_time, now, reminder_minutes=15, scan_interval=30) is True


def test_needs_reminder_too_early():
    from datetime import datetime
    now = datetime(2026, 6, 10, 14, 00)
    end_time = datetime(2026, 6, 10, 15, 35)
    assert needs_reminder(end_time, now, reminder_minutes=15, scan_interval=30) is False


def test_needs_reminder_too_late():
    from datetime import datetime
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
    mock_events.patch.return_value = mock_update
    mock_update.execute.return_value = {}

    event = {
        "id": "evt123",
        "description": "WhatsApp: +85212345678\nNotes",
    }
    now = datetime(2026, 6, 10, 15, 30)

    result = mark_event_reminded(mock_service, "primary", event, now)

    assert result is True
    mock_events.patch.assert_called_once()
    updated_body = mock_events.patch.call_args[1]["body"]
    assert "[已提醒 2026-06-10 15:30]" in updated_body["description"]
