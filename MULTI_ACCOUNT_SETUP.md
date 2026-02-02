# Gmail 多帳號設定指南

本指南說明如何設定多個 Gmail 帳號，讓系統可以同時從多個信箱獲取郵件。

## 準備工作

### 1. 為每個帳號建立獨立的 OAuth 憑證

有兩種方式：

**方式 A: 為每個帳號建立獨立的 Google Cloud 專案（推薦）**

對每個 Gmail 帳號：
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案（例如：`email-agent-account1`、`email-agent-account2`、`email-agent-account3`）
3. 啟用 Gmail API
4. 設定 OAuth 同意畫面
5. 建立 OAuth 2.0 用戶端 ID（桌面應用程式）
6. 下載憑證 JSON

**方式 B: 使用同一個專案，但為每個帳號建立不同的 OAuth 用戶端**

在同一個 Google Cloud 專案中：
1. 建立多個 OAuth 2.0 用戶端 ID
2. 分別下載每個用戶端的憑證

### 2. 組織憑證檔案

將下載的憑證檔案重新命名並放到專案根目錄：

```
email-summary-agent/
├── credentials_account1.json  # 個人信箱的憑證
├── credentials_account2.json  # 工作信箱的憑證
├── credentials_account3.json  # 其他信箱的憑證
└── ...
```

**重要**：這些檔案已經在 `.gitignore` 中被排除，不會被 git 追蹤。

## 首次授權

為每個帳號分別執行授權：

### 帳號 1（個人信箱）

```bash
python -c "from services.gmail_service import authenticate; authenticate('credentials_account1.json', 'token_account1.json')"
```

瀏覽器會開啟，選擇你的**第一個 Gmail 帳號**進行授權。
授權成功後會生成 `token_account1.json`。

### 帳號 2（工作信箱）

```bash
python -c "from services.gmail_service import authenticate; authenticate('credentials_account2.json', 'token_account2.json')"
```

選擇你的**第二個 Gmail 帳號**進行授權。
授權成功後會生成 `token_account2.json`。

### 帳號 3（其他信箱）

```bash
python -c "from services.gmail_service import authenticate; authenticate('credentials_account3.json', 'token_account3.json')"
```

選擇你的**第三個 Gmail 帳號**進行授權。
授權成功後會生成 `token_account3.json`。

完成後，專案結構應該是：

```
email-summary-agent/
├── credentials_account1.json
├── credentials_account2.json
├── credentials_account3.json
├── token_account1.json        ← 自動生成
├── token_account2.json        ← 自動生成
├── token_account3.json        ← 自動生成
└── ...
```

## 使用多帳號功能

### 方法 1: 直接使用 Python API

```python
from services.gmail_service import fetch_emails_from_multiple_accounts

# 定義帳號配置
accounts = [
    {
        'label': '個人信箱',
        'credentials_path': 'credentials_account1.json',
        'token_path': 'token_account1.json'
    },
    {
        'label': '工作信箱',
        'credentials_path': 'credentials_account2.json',
        'token_path': 'token_account2.json'
    },
    {
        'label': '其他信箱',
        'credentials_path': 'credentials_account3.json',
        'token_path': 'token_account3.json'
    }
]

# 從所有帳號獲取郵件
emails = fetch_emails_from_multiple_accounts(
    accounts=accounts,
    time_range='24h',
    max_emails_per_account=50,
    query=''
)

# 每封郵件都會有 'account' 欄位標示來源
for email in emails:
    print(f"[{email['account']}] {email['subject']}")
```

### 方法 2: 使用測試腳本

```bash
# 測試單一帳號（預設）
python services/gmail_service.py

# 測試多個帳號
python services/gmail_service.py --multi
```

### 方法 3: 整合到 LangGraph

修改 `agent/graph.py` 的 `fetch_emails` 節點：

```python
def fetch_emails(state: EmailSummaryState) -> dict:
    """獲取郵件（從多個帳號）"""
    print("---Fetch Emails from Multiple Accounts---")

    from services.gmail_service import fetch_emails_from_multiple_accounts

    # 定義帳號配置
    accounts = [
        {
            'label': '個人',
            'credentials_path': 'credentials_account1.json',
            'token_path': 'token_account1.json'
        },
        {
            'label': '工作',
            'credentials_path': 'credentials_account2.json',
            'token_path': 'token_account2.json'
        },
        {
            'label': '其他',
            'credentials_path': 'credentials_account3.json',
            'token_path': 'token_account3.json'
        }
    ]

    time_range = state.get('time_range', '24h')
    max_emails = state.get('max_emails', 20)

    # 計算每個帳號應該獲取多少封郵件
    max_per_account = max_emails // len(accounts) + 1

    emails = fetch_emails_from_multiple_accounts(
        accounts=accounts,
        time_range=time_range,
        max_emails_per_account=max_per_account,
        query=''
    )

    # 確保總數不超過 max_emails
    if len(emails) > max_emails:
        emails = emails[:max_emails]

    print(f"✅ 從 {len(accounts)} 個帳號共獲取 {len(emails)} 封郵件")

    return {"raw_emails": emails}
```

## 使用環境變數（可選）

如果你想把帳號配置放在環境變數中，可以在 `.env` 中設定：

```bash
# .env
GMAIL_ACCOUNTS='[
  {
    "label": "個人",
    "credentials_path": "credentials_account1.json",
    "token_path": "token_account1.json"
  },
  {
    "label": "工作",
    "credentials_path": "credentials_account2.json",
    "token_path": "token_account2.json"
  },
  {
    "label": "其他",
    "credentials_path": "credentials_account3.json",
    "token_path": "token_account3.json"
  }
]'
```

然後在程式碼中讀取：

```python
import os
import json

accounts = json.loads(os.getenv('GMAIL_ACCOUNTS', '[]'))
```

## 過濾特定帳號的郵件

如果你想要只處理來自特定帳號的郵件：

```python
# 獲取所有帳號的郵件
all_emails = fetch_emails_from_multiple_accounts(accounts, time_range='24h')

# 只處理來自「工作信箱」的郵件
work_emails = [e for e in all_emails if e['account'] == '工作信箱']

# 按帳號分組
from collections import defaultdict

emails_by_account = defaultdict(list)
for email in all_emails:
    emails_by_account[email['account']].append(email)

# 分別處理
for account_name, emails in emails_by_account.items():
    print(f"處理 {account_name} 的 {len(emails)} 封郵件")
```

## 帳號管理最佳實踐

1. **定期檢查 Token 有效性**
   - Token 會自動更新，但如果長時間沒用可能需要重新授權

2. **為帳號命名**
   - 使用有意義的標籤（如「個人」、「工作」、「客戶服務」）
   - 方便後續分析和報告

3. **安全性**
   - 確保所有 `credentials_*.json` 和 `token_*.json` 都在 `.gitignore` 中
   - 不要將這些檔案上傳到 GitHub 或任何公開位置
   - 考慮使用環境變數或密鑰管理服務

4. **效能優化**
   - 如果帳號很多，考慮使用並行處理（可以修改函數使用 `ThreadPoolExecutor`）
   - 設定合理的 `max_emails_per_account` 避免 API 配額問題

## 常見問題

### Q1: 授權時選錯帳號怎麼辦？

刪除對應的 `token_*.json` 並重新執行授權命令。

### Q2: 能否動態添加/移除帳號？

可以，只需修改 `accounts` 列表配置即可。不需要的帳號直接從列表中移除。

### Q3: 郵件會不會重複？

不會。每個帳號的郵件都有唯一的 `id` 和 `account` 欄位，可以用來區分。

### Q4: API 配額會不會有問題？

Gmail API 免費配額是每天 250 quota units/user。
- 讀取郵件列表：1 unit per request
- 讀取單封郵件：5 units per message

如果有 3 個帳號，每個獲取 50 封郵件：
- 列表請求：3 units
- 郵件內容：150 * 5 = 750 units
- 總計：753 units

遠低於每日 1,000,000,000 units 的限制，所以不用擔心。

### Q5: 可以為不同帳號設定不同的時間範圍嗎？

可以，修改函數讓每個帳號配置包含自己的 `time_range` 和 `query`：

```python
accounts = [
    {
        'label': '個人',
        'credentials_path': 'credentials_account1.json',
        'token_path': 'token_account1.json',
        'time_range': '24h',  # 個人信箱只看最近 24 小時
        'query': 'is:unread'  # 只看未讀
    },
    {
        'label': '工作',
        'credentials_path': 'credentials_account2.json',
        'token_path': 'token_account2.json',
        'time_range': '7d',   # 工作信箱看最近 7 天
        'query': ''
    }
]
```

## 下一步

完成多帳號設定後，你可以：

1. ✅ 在 LangSmith Studio 中測試多帳號功能
2. 🤖 修改 AI 分類邏輯，根據帳號來源進行不同的處理
3. 📊 在報告中按帳號分組顯示郵件摘要
4. 🔔 為不同帳號設定不同的通知規則
