import pytest
from config import load_config, Config


def test_load_config_reads_all_required_fields(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", "test_creds.json")
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "primary")
    monkeypatch.setenv("WAHA_API_URL", "http://localhost:3000")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot_test")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    config = load_config()

    assert config.google_credentials_file == "test_creds.json"
    assert config.google_calendar_id == "primary"
    assert config.waha_api_url == "http://localhost:3000"
    assert config.telegram_bot_token == "bot_test"
    assert config.telegram_chat_id == "123456789"


def test_load_config_uses_default_reminder_minutes(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", "test_creds.json")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot_test")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    config = load_config()
    assert config.reminder_minutes == 15


def test_load_config_missing_required_raises(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_FILE", "test_creds.json")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        load_config()
