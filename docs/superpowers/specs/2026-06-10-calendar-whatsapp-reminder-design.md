# Calendar → WhatsApp Reminder Service Design

## Overview

A Python cron-based service that every 30 minutes scans Google Calendar for events, sends WhatsApp reminders to customers 15 minutes before each event ends, and notifies the administrator via Telegram of all results.

## Technology Stack

| Component       | Choice                  |
|-----------------|-------------------------|
| Language        | Python 3.10+            |
| Scheduler       | System cron (Windows Task Scheduler or Linux cron) |
| Google Calendar | google-api-python-client |
| WhatsApp        | Twilio API for WhatsApp |
| Telegram Alert  | python-telegram-bot     |
| Config          | python-dotenv (.env)    |

## Project Structure

```
calendar-reminder/
├── main.py              # Entry point, orchestrates the flow
├── config.py            # Loads .env configuration
├── google_calendar.py   # Google Calendar API: read events, mark reminded
├── whatsapp.py          # Twilio: send WhatsApp message
├── telegram.py          # Telegram: send admin notifications
├── requirements.txt
├── .env.example
└── README.md
```

## Core Flow

```
Cron (every 30 min) → main.py
  │
  ├─ 1. Authenticate Google Calendar (Service Account)
  ├─ 2. Fetch upcoming events from primary calendar
  ├─ 3. For each event:
  │     ├─ Parse WhatsApp number from description (regex: WhatsApp:\s*(\+?\d+))
  │     ├─ Check if event ends within [15min, 15min+30min) from now
  │     ├─ Check if NOT already marked [已提醒 ...] in description
  │     └─ If all conditions met:
  │           ├─ Send WhatsApp via Twilio
  │           ├─ On success: mark event description with [已提醒 YYYY-MM-DD HH:MM]
  │           └─ Send Telegram notification (success or failure)
  │
  └─ 4. Log all results
```

## Event Description Format

Events in Google Calendar must include a WhatsApp number in the description:

```
WhatsApp: +85212345678
客戶姓名: 陳先生
(any other content...)

[已提醒 2026-06-10 15:30]
```

### Extraction Rules

- Extract WhatsApp number: regex `WhatsApp:\s*(\+?\d[\d\s-]+)`
- If no match found → skip event, send Telegram `⚠️ skip` notification
- Check for reminder marker: `[已提醒` — if found, skip event

## Time Window Logic

```
reminder_window_start = event_end_time - REMINDER_MINUTES (default 15)
reminder_window_end   = reminder_window_start + SCAN_INTERVAL (30 min)

Event is eligible if: reminder_window_start ≤ now < reminder_window_end
```

This ensures each event is captured exactly once per scan cycle.

## WhatsApp Message Template

```
溫馨提示：您的預約「{event_title}」將於 {HH:MM} 結束，請準時出席。
```

- `{event_title}` replaced with Google Calendar event title
- `{HH:MM}` replaced with event end time in 24-hour format (e.g., 15:30)

## Telegram Notification Format

### Success

```
✅ 已發送提醒
Event: {event_title}
時間: {HH:MM} 結束
WhatsApp: {phone_number}
```

### Skipped (no WhatsApp number)

```
⚠️ 跳過 Event（無 WhatsApp 號碼）
Event: {event_title}
時間: {HH:MM} 結束
```

### Twilio Send Failure

```
❌ 發送失敗
Event: {event_title}
WhatsApp: {phone_number}
錯誤: {error_message}
```

### System Error (Google API, network, etc.)

```
🚨 系統錯誤
detail: {error_detail}
```

## Configuration (.env)

```
# Google Calendar
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_ID=primary

# Twilio (WhatsApp)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=whatsapp:+14155238886

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Reminder
REMINDER_MINUTES=15
```

## Google Calendar Authentication

Use **Service Account** with domain-wide delegation to the target calendar:

1. Create a Service Account in Google Cloud Console
2. Enable Google Calendar API
3. Download JSON credentials → `credentials.json`
4. Share the target calendar with the service account email (or use domain-wide delegation for G Suite)

## Error Handling

| Scenario | Action | Telegram |
|----------|--------|----------|
| Google API unreachable | Log, exit(1) | 🚨 system error |
| Event has no WhatsApp number | Skip event | ⚠️ skip |
| Twilio send fails | Skip event, do NOT mark | ❌ failure |
| Telegram send fails | Log warning, continue | (none) |
| Network timeout | Retry up to 3 times with exponential backoff | 🚨 if all retries fail |

### Key Principle

An event is **only marked `[已提醒]` if WhatsApp was successfully sent**. On failure, it will be retried in the next scan cycle.

## Scheduling

### Windows (Task Scheduler)

```
schtasks /create /tn "CalendarReminder" /tr "python D:\AI\PixelArt\calendar-reminder\main.py" /sc minute /mo 30
```

### Linux (cron)

```
*/30 * * * * cd /path/to/calendar-reminder && python main.py
```

## Dependencies (requirements.txt)

```
google-api-python-client
google-auth
twilio
python-telegram-bot
python-dotenv
```
