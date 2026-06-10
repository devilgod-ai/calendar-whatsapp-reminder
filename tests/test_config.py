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
