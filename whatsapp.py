from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


MESSAGE_TEMPLATE = "溫馨提示：您的預約「{title}」將於 {time} 結束，請準時出席。"


def send_whatsapp_reminder(
    client: Client,
    from_number: str,
    to_number: str,
    event_title: str,
    end_time_str: str,
) -> tuple[bool, str]:
    body = MESSAGE_TEMPLATE.format(title=event_title, time=end_time_str)
    try:
        client.messages.create(
            from_=from_number,
            to=f"whatsapp:{to_number}",
            body=body,
        )
        return True, ""
    except TwilioRestException as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
