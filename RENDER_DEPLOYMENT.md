# Render 部署指南

本指南幫助你將 Email Summary Agent API 部署到 Render（永久免費）。

## Render 免費方案特性

✅ **優點**：
- 永久免費（每月 750 小時）
- 自動 HTTPS
- 從 GitHub 自動部署

⚠️ **限制**：
- 15 分鐘不活動會休眠（cold start）
- Cold start 啟動需要 30-60 秒
- 已通過 BackgroundTasks 優化，避免 Slack 超時

---

## 步驟 1: 準備 GitHub Repository

確保你的專案已推送到 GitHub：

```bash
git add .
git commit -m "準備部署到 Render"
git push origin main
```

---

## 步驟 2: 在 Render 創建 Web Service

1. **登入 Render**：
   - 前往 https://render.com
   - 使用 GitHub 帳號登入

2. **創建新服務**：
   - 點擊 "New +" → "Web Service"
   - 選擇你的 GitHub repository (`email-summary-agent`)
   - 允許 Render 訪問該 repo

3. **配置服務**：
   - **Name**: `email-summary-agent-api` (或任意名稱)
   - **Region**: Singapore (最接近台灣)
   - **Branch**: `main`
   - **Root Directory**: 留空
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: 選擇 **Free**

4. **點擊 "Create Web Service"**

---

## 步驟 3: 設定環境變量

在 Render Dashboard → 你的服務 → "Environment" 頁籤，添加所有環境變量：

### OpenAI
```
OPENAI_API_KEY=sk-...
```

### Gmail 帳號 1（個人）
```
GMAIL_CREDENTIALS_ACCOUNT1_BASE64=<base64 編碼的 credentials>
GMAIL_TOKEN_ACCOUNT1_BASE64=<base64 編碼的 token>
```

### Gmail 帳號 2（工作）
```
GMAIL_CREDENTIALS_ACCOUNT2_BASE64=<base64 編碼的 credentials>
GMAIL_TOKEN_ACCOUNT2_BASE64=<base64 編碼的 token>
```

### Gmail 帳號 3（紐約大學）
```
GMAIL_CREDENTIALS_ACCOUNT3_BASE64=<base64 編碼的 credentials>
GMAIL_TOKEN_ACCOUNT3_BASE64=<base64 編碼的 token>
```

### Gmail 配置
```
GMAIL_MULTI_ACCOUNT=true
```

### Slack（Phase 1 Webhook）
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Slack Bot（Phase 2B）
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=<從 Slack App Basic Information 獲取>
SLACK_CHANNEL_ID=C01234ABCDE
```

### Google Calendar
```
GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials/calendar_credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=credentials/calendar_token.json
```

**保存後，Render 會自動重新部署。**

---

## 步驟 4: 獲取 Render URL

部署成功後，你會獲得一個 URL，類似：
```
https://email-summary-agent-api.onrender.com
```

測試健康檢查：
```bash
curl https://email-summary-agent-api.onrender.com/health
```

應該返回：
```json
{"status": "healthy"}
```

---

## 步驟 5: 配置 Slack App Interactivity

1. 前往 https://api.slack.com/apps
2. 選擇你的 Slack App
3. 左側選單 → "Interactivity & Shortcuts"
4. 開啟 "Interactivity"
5. **Request URL** 填入：
   ```
   https://your-app.onrender.com/slack/interactive
   ```
   （將 `your-app` 替換為你的實際 Render URL）
6. 點擊 "Save Changes"

---

## 步驟 6: 測試 Slack 互動

### 方法 1: 觸發完整工作流（從 GitHub Actions）

更新 `.github/workflows/daily-summary.yml`：

```yaml
- name: Trigger Email Summary via API
  run: |
    curl -X POST https://your-app.onrender.com/webhook/email-summary
```

### 方法 2: 手動測試（本地觸發）

```bash
curl -X POST https://your-app.onrender.com/webhook/email-summary
```

如果有檢測到事件，會在 Slack 中看到互動訊息（按鈕）。

---

## 步驟 7: 處理 Cold Start（可選優化）

### 問題
Render 免費方案 15 分鐘不活動會休眠，下次請求需要 30-60 秒啟動。

### 解決方案 1: Cron Job 保持喚醒（推薦）

使用免費的 cron 服務每 14 分鐘 ping 一次：

1. 註冊 https://cron-job.org（免費）
2. 創建新 Cron Job：
   - URL: `https://your-app.onrender.com/health`
   - 間隔: 每 14 分鐘
   - Method: GET

### 解決方案 2: 接受 Cold Start

如果你的使用量不高，可以接受 cold start。API 已優化為立即回應 Slack，實際處理在後台進行。

---

## 故障排除

### 問題 1: Slack 說 "url_verification failed"

**原因**: Slack 在設定 Request URL 時會發送驗證請求。

**解決**:
添加 URL 驗證處理到 `api/server.py`（如果需要）。
或者：先部署 API，確保 `/slack/interactive` 端點可訪問，再設定 Slack。

### 問題 2: 部署失敗 "Module not found"

**原因**: 依賴未正確安裝。

**解決**:
檢查 Render Logs，確保所有依賴都在 `requirements.txt` 中。

### 問題 3: API 回應 500 錯誤

**原因**: 環境變量未設定或程式碼錯誤。

**解決**:
1. 檢查 Render → Environment 變量是否完整
2. 查看 Render → Logs 找出錯誤訊息

---

## 成本估算

| 項目 | 每月成本 |
|------|----------|
| Render Free Tier | **$0** |
| OpenAI GPT-4o (分類+摘要+事件檢測) | ~$2-3 |
| Google APIs | $0 (在免費額度內) |
| **總計** | **~$2-3/月** |

---

## 下一步

- ✅ 部署到 Render
- ✅ 配置 Slack App
- ✅ 測試互動功能
- 🔜 實施 Phase 2A (簡化 HITL) 或完整 Phase 2B

如有問題，檢查 Render Logs：
```
Dashboard → Your Service → Logs
```
