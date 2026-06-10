from unittest.mock import MagicMock
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

    assert result == (True, "")
    call_args = mock_client.messages.create.call_args[1]
    assert call_args["from_"] == "whatsapp:+14155238886"
    assert call_args["to"] == "whatsapp:+85212345678"
    assert "Doctor Appointment" in call_args["body"]
    assert "15:30" in call_args["body"]


def test_send_whatsapp_reminder_returns_false_on_error():
    from twilio.base.exceptions import TwilioRestException
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = TwilioRestException(
        status=400, uri="http://example.com", msg="Bad request"
    )

    result = send_whatsapp_reminder(
        client=mock_client,
        from_number="whatsapp:+14155238886",
        to_number="+85212345678",
        event_title="Test",
        end_time_str="15:30",
    )

    assert result[0] is False
    assert "Bad request" in result[1]
