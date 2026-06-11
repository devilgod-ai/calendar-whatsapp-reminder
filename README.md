# Calendar WhatsApp Reminder

定時掃描 Google Calendar，在預約結束前透過 WhatsApp 發送提醒給客戶，並透過 Telegram 通知管理員。

## 架構

```
Google Calendar ─→ main.py ─→ WAHA API ─→ 客戶 WhatsApp
                      │
                      └──→ Telegram Bot ─→ 管理員
```

## 前置需求

- Python 3.10+
- Docker（運行 WAHA WhatsApp API）
- Google Calendar Service Account
- Telegram Bot Token

## 部署步驟

### 1. WAHA WhatsApp API

可以在本機或另一台伺服器執行。

```bash
docker run -d -p 3000:3000 devlike/whatsapp-http-api
```

開啟 `http://<伺服器IP>:3000`，用手機 WhatsApp 掃描 QR 碼完成配對。

> ⚠️ 若 WAHA 在遠端伺服器，請確保該伺服器的 3000 port 有對外開放（或使用 VPN／SSH tunnel）。

### 2. Google Calendar Service Account

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立專案 → 啟用 Google Calendar API
3. 建立 Service Account → 下載 JSON 金鑰，命名為 `credentials.json`
4. 在 Google Calendar 中將該 Service Account Email 分享給要讀取的日曆（權限：檢視）

### 3. Telegram Bot

1. 在 Telegram 搜尋 [@BotFather](https://t.me/BotFather)
2. 輸入 `/newbot` 建立機器人，取得 Token
3. 與機器人對話一次，然後訪問 `https://api.telegram.org/bot<TOKEN>/getUpdates` 取得 Chat ID

### 4. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env`：

```env
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_ID=primary

# WAHA 在本機
WAHA_API_URL=http://localhost:3000

# WAHA 在遠端伺服器（擇一使用）
# WAHA_API_URL=http://192.168.1.100:3000
# WAHA_API_URL=https://waha.example.com

TELEGRAM_BOT_TOKEN=你的機器人Token
TELEGRAM_CHAT_ID=你的Chat ID
REMINDER_MINUTES=15
```

### 5. 安裝依賴

```bash
pip install -r requirements.txt
```

### 6. 在 Google Calendar 事件描述中加上 WhatsApp 號碼

在每個事件的描述中加入（範例）：

```
WhatsApp: +85212345678
```

### 7. 執行程式

```bash
python main.py
```

建議設定定時執行（每 30 分鐘）：

**Linux (crontab)：**
```cron
*/30 * * * * cd /path/to/project && python main.py
```

**Windows (工作排程器)：**
```
程式: python
引數: main.py
開始位置: C:\path\to\project
觸發程序: 每30分鐘一次
```

## 行為說明

- 掃描當日所有事件
- 若事件結束時間在 `REMINDER_MINUTES`（預設 15 分鐘）內，則發送提醒
- 已發送過的事件會標記 `[已提醒 YYYY-MM-DD HH:MM]`，不會重複發送
- 發送成功 / 跳過 / 失敗皆會透過 Telegram 通知管理員
- 事件描述沒有 `WhatsApp:` 號碼則跳過並通知管理員
