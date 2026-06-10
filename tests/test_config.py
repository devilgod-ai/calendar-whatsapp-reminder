import pytest
from config import load_config, Config


def test_load_config_reads_all_required_fields(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", "test_creds.json")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "primary")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_test")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token_test")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "whatsapp:+15551234567")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot_test")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    config = load_config()

    assert config.google_credentials_file == "test_creds.json"
    assert config.google_calendar_id == "primary"
    assert config.twilio_account_sid == "AC_test"
    assert config.twilio_auth_token == "token_test"
    assert config.twilio_from_number == "whatsapp:+15551234567"
    assert config.telegram_bot_token == "bot_test"
    assert config.telegram_chat_id == "123456789"


def test_load_config_uses_default_reminder_minutes(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", "test_creds.json")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_test")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token_test")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "whatsapp:+15551234567")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot_test")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    config = load_config()
    assert config.reminder_minutes == 15


def test_load_config_missing_required_raises(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", "test_creds.json")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token_test")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "whatsapp:+15551234567")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot_test")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")
    with pytest.raises(ValueError, match="TWILIO_ACCOUNT_SID"):
        load_config()
