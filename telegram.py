from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Bot


async def _send(bot: "Bot", chat_id: str, text: str) -> bool:
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        return True
    except Exception:
        return False


async def notify_success(
    bot: "Bot",
    chat_id: str,
    event_title: str,
    end_time_str: str,
    whatsapp_number: str,
) -> bool:
    text = (
        f"\u2705 已發送提醒\n"
        f"Event: {event_title}\n"
        f"時間: {end_time_str} 結束\n"
        f"WhatsApp: {whatsapp_number}"
    )
    return await _send(bot, chat_id, text)


async def notify_skip(
    bot: "Bot",
    chat_id: str,
    event_title: str,
    end_time_str: str,
) -> bool:
    text = (
        f"\u26a0\ufe0f 跳過 Event（無 WhatsApp 號碼）\n"
        f"Event: {event_title}\n"
        f"時間: {end_time_str} 結束"
    )
    return await _send(bot, chat_id, text)


async def notify_failure(
    bot: "Bot",
    chat_id: str,
    event_title: str,
    whatsapp_number: str,
    error_message: str,
) -> bool:
    text = (
        f"\u274c 發送失敗\n"
        f"Event: {event_title}\n"
        f"WhatsApp: {whatsapp_number}\n"
        f"錯誤: {error_message}"
    )
    return await _send(bot, chat_id, text)


async def notify_system_error(
    bot: "Bot",
    chat_id: str,
    error_detail: str,
) -> bool:
    text = f"\U0001f6a8 系統錯誤\ndetail: {error_detail}"
    return await _send(bot, chat_id, text)
