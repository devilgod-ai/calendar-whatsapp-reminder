import requests


MESSAGE_TEMPLATE = "溫馨提示：您的預約「{title}」將於 {time} 結束，請準時出席。"


def _to_chat_id(phone: str) -> str:
    return phone.lstrip("+") + "@c.us"


def send_whatsapp_reminder(
    waha_api_url: str,
    to_number: str,
    event_title: str,
    end_time_str: str,
) -> tuple[bool, str]:
    body = MESSAGE_TEMPLATE.format(title=event_title, time=end_time_str)
    payload = {
        "session": "default",
        "chatId": _to_chat_id(to_number),
        "text": body,
    }
    try:
        resp = requests.post(f"{waha_api_url}/api/sendText", json=payload, timeout=30)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        return True, ""
    except Exception as e:
        return False, str(e)
