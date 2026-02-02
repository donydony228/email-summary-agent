# Railway 部署指南

本指南說明如何將 Email Summary Agent 部署到 Railway，並設定每日自動執行。

## 前置準備

1. Railway 帳號（免費方案即可）
2. GitHub 帳號（用於連接 Railway）
3. 已設定好的 Gmail API credentials
4. Slack Webhook URL

## 部署步驟

### 1. 準備 Credentials

首先，需要將 Gmail credentials 轉換為 base64 格式：

```bash
python encode_credentials.py
```

這個腳本會輸出需要在 Railway 設定的環境變數。

### 2. 推送代碼到 GitHub

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 3. 在 Railway 創建新專案

1. 前往 https://railway.app/
2. 點擊 "New Project"
3. 選擇 "Deploy from GitHub repo"
4. 選擇你的 email-summary-agent 倉庫
5. Railway 會自動偵測 Dockerfile 並開始構建

### 4. 設定環境變數

在 Railway 專案設定中，添加以下環境變數：

#### 必要環境變數

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# LangSmith (可選)
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING_V2=true
LANGSMITH_PROJECT=email-summary-agent

# Gmail API - Base64 編碼的 credentials
# 單一帳號模式
GMAIL_CREDENTIALS_BASE64=<從 encode_credentials.py 取得>
GMAIL_TOKEN_BASE64=<從 encode_credentials.py 取得>

# 或多帳號模式
GMAIL_MULTI_ACCOUNT=true
GMAIL_CREDENTIALS_ACCOUNT1_BASE64=<從 encode_credentials.py 取得>
GMAIL_TOKEN_ACCOUNT1_BASE64=<從 encode_credentials.py 取得>
GMAIL_CREDENTIALS_ACCOUNT2_BASE64=<從 encode_credentials.py 取得>
GMAIL_TOKEN_ACCOUNT2_BASE64=<從 encode_credentials.py 取得>
GMAIL_CREDENTIALS_ACCOUNT3_BASE64=<從 encode_credentials.py 取得>
GMAIL_TOKEN_ACCOUNT3_BASE64=<從 encode_credentials.py 取得>

# Slack
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

#### 可選環境變數

```bash
# 郵件摘要設定
EMAIL_TIME_RANGE=24h
MAX_EMAILS=20

# 調度器設定
SCHEDULE_TIME=09:00  # 每天執行的時間 (UTC 時區)
RUN_ON_STARTUP=false  # 是否在啟動時立即執行一次
```

### 5. 部署

設定完環境變數後，Railway 會自動重新部署應用程式。

## 時區設定

Railway 使用 UTC 時區。如果你希望在台灣時間早上 9:00 執行，需要設定：

```bash
SCHEDULE_TIME=01:00  # UTC 01:00 = 台灣時間 09:00
```

## 測試部署

### 方法 1: 啟動時立即執行

設定環境變數：
```bash
RUN_ON_STARTUP=true
```

然後重新部署，檢查 Slack 是否收到通知。

### 方法 2: 暫時調整執行時間

將 `SCHEDULE_TIME` 設定為幾分鐘後的時間，觀察是否正常執行。

## 查看日誌

在 Railway 專案頁面，點擊 "Deployments" → 選擇最新的部署 → "View Logs"

你會看到類似以下的日誌：

```
正在初始化 Gmail credentials...
已創建 credentials/credentials.json
已創建 credentials/token.json
郵件摘要調度器已啟動
將在每天 09:00 執行
```

## 費用說明

- Railway 免費方案每月提供 500 小時的執行時間
- 本應用持續運行，每月約使用 720 小時
- 建議使用 Railway Pro 方案（每月 $5 起）

## 故障排除

### Credentials 無效

如果看到 credentials 相關錯誤，檢查：
1. Base64 編碼是否正確
2. 環境變數名稱是否正確
3. 是否正確設定 GMAIL_MULTI_ACCOUNT

### 未收到 Slack 通知

檢查：
1. SLACK_WEBHOOK_URL 是否正確
2. Webhook 對應的 Slack 頻道是否可訪問
3. 查看日誌中的錯誤訊息

### 時間不對

Railway 使用 UTC 時區，需要轉換時間：
- 台灣時間 (UTC+8) 09:00 = UTC 01:00
- 設定 `SCHEDULE_TIME=01:00`

## 更新應用

只需推送代碼到 GitHub，Railway 會自動重新部署：

```bash
git add .
git commit -m "Update email summary logic"
git push origin main
```

## 停止運行

在 Railway 專案設定中，點擊 "Delete Service" 即可停止運行並刪除服務。
