from unittest.mock import patch, MagicMock
from whatsapp import send_whatsapp_reminder


WAHA_URL = "http://localhost:3000"


def test_send_whatsapp_reminder_formats_message():
    with patch("whatsapp.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {})

        result = send_whatsapp_reminder(
            waha_api_url=WAHA_URL,
            to_number="+85212345678",
            event_title="Doctor Appointment",
            end_time_str="15:30",
        )

    assert result == (True, "")
    call_body = mock_post.call_args[1]["json"]
    assert call_body["session"] == "default"
    assert call_body["chatId"] == "85212345678@c.us"
    assert "Doctor Appointment" in call_body["text"]
    assert "15:30" in call_body["text"]
    assert mock_post.call_args[0][0] == f"{WAHA_URL}/api/sendText"


def test_send_whatsapp_reminder_returns_false_on_network_error():
    with patch("whatsapp.requests.post") as mock_post:
        mock_post.side_effect = ConnectionError("Connection refused")

        result = send_whatsapp_reminder(
            waha_api_url=WAHA_URL,
            to_number="+85212345678",
            event_title="Test",
            end_time_str="15:30",
        )

    assert result[0] is False
    assert "Connection refused" in result[1]


def test_send_whatsapp_reminder_returns_false_on_http_error():
    with patch("whatsapp.requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=400,
            json=lambda: {"error": "Invalid chat ID"},
            text="Invalid chat ID",
        )

        result = send_whatsapp_reminder(
            waha_api_url=WAHA_URL,
            to_number="+85212345678",
            event_title="Test",
            end_time_str="15:30",
        )

    assert result[0] is False
    assert "400" in result[1] or "Invalid" in result[1]
