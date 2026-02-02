# GitHub Actions 部署指南

使用 GitHub Actions 每天自動執行郵件摘要，完全免費。

## 優勢

- 完全免費（每月 2000 分鐘）
- 無需額外服務器
- 自動從 GitHub 運行
- 易於設置和管理

## 部署步驟

### 1. 準備 Credentials

在本地運行以下命令，將 Gmail credentials 轉換為 base64：

```bash
python encode_credentials.py
```

這會輸出類似以下的內容：

```
GMAIL_CREDENTIALS_BASE64=
eyJ3ZWIiOnsiY2xpZW50X2lkIjo...

GMAIL_TOKEN_BASE64=
eyJ0b2tlbiI6InlhMjkuYTBB...
```

### 2. 設定 GitHub Secrets

1. 前往你的 GitHub 倉庫
2. 點擊 `Settings` → `Secrets and variables` → `Actions`
3. 點擊 `New repository secret`
4. 添加以下 secrets：

#### 必要 Secrets

**OpenAI API**
```
Name: OPENAI_API_KEY
Value: your_openai_api_key
```

**Slack Webhook**
```
Name: SLACK_WEBHOOK_URL
Value: your_slack_webhook_url
```

**Gmail Credentials（單一帳號模式）**
```
Name: GMAIL_CREDENTIALS_BASE64
Value: <從 encode_credentials.py 取得>

Name: GMAIL_TOKEN_BASE64
Value: <從 encode_credentials.py 取得>
```

**或者 Gmail Credentials（多帳號模式）**
```
Name: GMAIL_MULTI_ACCOUNT
Value: true

Name: GMAIL_CREDENTIALS_ACCOUNT1_BASE64
Value: <從 encode_credentials.py 取得>

Name: GMAIL_TOKEN_ACCOUNT1_BASE64
Value: <從 encode_credentials.py 取得>

Name: GMAIL_CREDENTIALS_ACCOUNT2_BASE64
Value: <從 encode_credentials.py 取得>

Name: GMAIL_TOKEN_ACCOUNT2_BASE64
Value: <從 encode_credentials.py 取得>

Name: GMAIL_CREDENTIALS_ACCOUNT3_BASE64
Value: <從 encode_credentials.py 取得>

Name: GMAIL_TOKEN_ACCOUNT3_BASE64
Value: <從 encode_credentials.py 取得>
```

#### 可選 Secrets

**LangSmith（可選）**
```
Name: LANGSMITH_API_KEY
Value: your_langsmith_api_key

Name: LANGSMITH_TRACING_V2
Value: true

Name: LANGSMITH_PROJECT
Value: email-summary-agent
```

**郵件摘要設定（可選）**
```
Name: EMAIL_TIME_RANGE
Value: 24h

Name: MAX_EMAILS
Value: 20
```

### 3. 推送代碼到 GitHub

```bash
git add .
git commit -m "Add GitHub Actions workflow"
git push origin main
```

### 4. 調整執行時間（可選）

workflow 文件位於 `.github/workflows/email-summary.yml`

預設每天 UTC 00:00 執行（台灣時間 08:00）。

如果要修改時間，編輯 cron 表達式：

```yaml
on:
  schedule:
    # 每天 UTC 01:00 執行（台灣時間 09:00）
    - cron: '0 1 * * *'
```

**Cron 時間對照表（台灣時間 UTC+8）：**
- 台灣 08:00 = UTC 00:00 → `'0 0 * * *'`
- 台灣 09:00 = UTC 01:00 → `'0 1 * * *'`
- 台灣 10:00 = UTC 02:00 → `'0 2 * * *'`
- 台灣 18:00 = UTC 10:00 → `'0 10 * * *'`

### 5. 手動測試

GitHub Actions 設定了 `workflow_dispatch`，可以手動觸發：

1. 前往 GitHub 倉庫
2. 點擊 `Actions` 標籤
3. 選擇 `Daily Email Summary` workflow
4. 點擊 `Run workflow` → `Run workflow`

查看執行結果和日誌。

## 查看執行狀態

### 查看 Workflow 運行歷史

1. 前往 GitHub 倉庫
2. 點擊 `Actions` 標籤
3. 查看所有運行記錄

### 查看詳細日誌

1. 點擊任一運行記錄
2. 點擊 `run-email-summary` job
3. 展開各個步驟查看詳細日誌

### 接收通知

如果執行失敗，GitHub 會發送郵件通知你。

可以在 `Settings` → `Notifications` 中調整通知設定。

## 費用說明

- GitHub Actions 免費方案：每月 2000 分鐘
- 每天運行一次，每次約 2-5 分鐘
- 每月使用約 60-150 分鐘，遠低於免費額度
- **完全免費，無需信用卡**

## 故障排除

### Credentials 初始化失敗

檢查：
1. GitHub Secrets 名稱是否正確
2. Base64 編碼是否完整（沒有換行或截斷）
3. 單一/多帳號模式設定是否正確

### Workflow 沒有執行

檢查：
1. workflow 文件是否在 `.github/workflows/` 目錄
2. 文件名是否為 `.yml` 結尾
3. cron 語法是否正確
4. Actions 是否在倉庫設定中啟用

### 未收到 Slack 通知

檢查：
1. `SLACK_WEBHOOK_URL` secret 是否正確
2. 查看 workflow 日誌中的錯誤訊息
3. Webhook URL 是否仍然有效

### Python 依賴安裝失敗

通常是網路問題，重新運行 workflow 即可。

## 停止運行

### 暫時停止

1. 前往 `Actions` 標籤
2. 選擇 `Daily Email Summary`
3. 點擊右上角 `...` → `Disable workflow`

### 永久刪除

刪除 `.github/workflows/email-summary.yml` 文件並推送到 GitHub。

## 進階設定

### 設定多個執行時間

```yaml
on:
  schedule:
    # 每天早上 8:00
    - cron: '0 0 * * *'
    # 每天晚上 18:00
    - cron: '0 10 * * *'
```

### 只在工作日執行

```yaml
on:
  schedule:
    # 週一到週五
    - cron: '0 0 * * 1-5'
```

### 設定執行超時

在 job 中添加 `timeout-minutes`：

```yaml
jobs:
  run-email-summary:
    runs-on: ubuntu-latest
    timeout-minutes: 10  # 10 分鐘超時
```

## 與 Railway 比較

| 特性 | GitHub Actions | Railway |
|------|----------------|---------|
| 費用 | 永久免費 | 30 天免費試用 |
| 設置難度 | 簡單 | 簡單 |
| 執行方式 | 定時觸發 | 持續運行 |
| 適用場景 | 低頻率任務 | 高頻率/即時任務 |
| 資源限制 | 2000 分鐘/月 | 需付費 |

對於每天運行一次的郵件摘要，GitHub Actions 是最佳選擇。
