import asyncio
from unittest.mock import AsyncMock
from telegram_notifier import notify_success, notify_skip, notify_failure, notify_system_error


def test_notify_success_formats_message():
    mock_bot = AsyncMock()
    result = asyncio.run(notify_success(
        bot=mock_bot,
        chat_id="123",
        event_title="Doctor",
        end_time_str="15:30",
        whatsapp_number="+85212345678",
    ))
    assert result is True
    call_args = mock_bot.send_message.call_args[1]
    assert call_args["chat_id"] == "123"
    assert "\u2705" in call_args["text"]
    assert "Doctor" in call_args["text"]
    assert "15:30" in call_args["text"]
    assert "+85212345678" in call_args["text"]


def test_notify_skip_formats_message():
    mock_bot = AsyncMock()
    result = asyncio.run(notify_skip(
        bot=mock_bot,
        chat_id="123",
        event_title="Doctor",
        end_time_str="15:30",
    ))
    assert result is True
    text = mock_bot.send_message.call_args[1]["text"]
    assert "\u26a0\ufe0f" in text
    assert "Doctor" in text
    assert "15:30" in text
    assert "無 WhatsApp 號碼" in text


def test_notify_failure_formats_message():
    mock_bot = AsyncMock()
    result = asyncio.run(notify_failure(
        bot=mock_bot,
        chat_id="123",
        event_title="Doctor",
        whatsapp_number="+85212345678",
        error_message="Invalid phone",
    ))
    assert result is True
    text = mock_bot.send_message.call_args[1]["text"]
    assert "\u274c" in text
    assert "Doctor" in text
    assert "+85212345678" in text
    assert "Invalid phone" in text


def test_notify_system_error_formats_message():
    mock_bot = AsyncMock()
    result = asyncio.run(notify_system_error(
        bot=mock_bot,
        chat_id="123",
        error_detail="Google API timeout",
    ))
    assert result is True
    text = mock_bot.send_message.call_args[1]["text"]
    assert "\U0001f6a8" in text
    assert "Google API timeout" in text


def test_notify_handles_send_error():
    mock_bot = AsyncMock()
    from telegram.error import TelegramError
    mock_bot.send_message.side_effect = TelegramError("Network error")
    result = asyncio.run(notify_system_error(
        bot=mock_bot,
        chat_id="123",
        error_detail="test",
    ))
    assert result is False
