# 多帳號快速開始指南

這是一個快速設定指南，幫助你在 5-10 分鐘內完成三個 Gmail 帳號的整合。

## 步驟 1: 準備憑證（每個帳號）

為每個 Gmail 帳號準備 OAuth 2.0 憑證：

### 方式 A: 使用同一個 Google Cloud 專案（簡單）

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇你已有的專案（或建立新專案）
3. 前往「API 和服務」→「憑證」
4. 點擊「+ 建立憑證」→「OAuth 用戶端 ID」
5. 選擇「桌面應用程式」
6. 命名為 `Account 1` / `Account 2` / `Account 3`
7. 分別下載三個憑證檔案

### 方式 B: 為每個帳號建立獨立專案（安全）

對每個帳號重複完整的 [GMAIL_SETUP.md](GMAIL_SETUP.md) 流程。

## 步驟 2: 重新命名憑證檔案

將下載的 JSON 檔案重新命名並放到專案根目錄：

```bash
# 專案根目錄
cd /path/to/email-summary-agent

# 重新命名憑證檔案
mv ~/Downloads/client_secret_XXX1.json credentials_account1.json
mv ~/Downloads/client_secret_XXX2.json credentials_account2.json
mv ~/Downloads/client_secret_XXX3.json credentials_account3.json
```

## 步驟 3: 授權每個帳號

為每個帳號執行授權（瀏覽器會自動開啟）：

```bash
# 授權第一個帳號（個人信箱）
python -c "from services.gmail_service import authenticate; authenticate('credentials_account1.json', 'token_account1.json')"

# 授權第二個帳號（工作信箱）
python -c "from services.gmail_service import authenticate; authenticate('credentials_account2.json', 'token_account2.json')"

# 授權第三個帳號（其他信箱）
python -c "from services.gmail_service import authenticate; authenticate('credentials_account3.json', 'token_account3.json')"
```

**注意**：每次授權時，確保在瀏覽器中選擇**正確的 Gmail 帳號**！

完成後，你會看到以下檔案：

```
✅ credentials_account1.json
✅ credentials_account2.json
✅ credentials_account3.json
✅ token_account1.json        (自動生成)
✅ token_account2.json        (自動生成)
✅ token_account3.json        (自動生成)
```

## 步驟 4: 測試多帳號功能

```bash
# 測試多帳號獲取
python services/gmail_service.py --multi
```

你應該會看到類似這樣的輸出：

```
============================================================
從 3 個帳號獲取郵件
============================================================

📧 [1/3] 正在獲取帳號: 個人信箱
   Credentials: credentials_account1.json
   Token: token_account1.json
搜尋郵件: after:1769914970
找到 15 封郵件，開始獲取詳細內容...
✅ 帳號 [個人信箱] 獲取成功: 15 封郵件

📧 [2/3] 正在獲取帳號: 工作信箱
   Credentials: credentials_account2.json
   Token: token_account2.json
搜尋郵件: after:1769914970
找到 8 封郵件，開始獲取詳細內容...
✅ 帳號 [工作信箱] 獲取成功: 8 封郵件

📧 [3/3] 正在獲取帳號: 其他信箱
   Credentials: credentials_account3.json
   Token: token_account3.json
搜尋郵件: after:1769914970
找到 12 封郵件，開始獲取詳細內容...
✅ 帳號 [其他信箱] 獲取成功: 12 封郵件

============================================================
✅ 總共獲取: 35 封郵件
============================================================
```

## 步驟 5: 在 LangGraph 中啟用多帳號模式

### 選項 A: 使用環境變數（推薦）

在 `.env` 中添加：

```bash
GMAIL_MULTI_ACCOUNT=true
```

然後直接使用：

```bash
langgraph dev
```

### 選項 B: 修改程式碼

直接修改 [agent/graph.py](agent/graph.py:48-111) 中的 `accounts` 配置：

```python
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
```

並將 `use_multi_account = False` 改為 `use_multi_account = True`。

## 步驟 6: 在 LangSmith Studio 測試

1. 啟動開發伺服器：
   ```bash
   langgraph dev
   ```

2. 前往 [LangSmith Studio](https://smith.langchain.com/)

3. 測試輸入：
   ```json
   {
     "time_range": "24h",
     "max_emails": 30
   }
   ```

4. 查看執行結果，你會看到來自三個帳號的郵件！

## 常見問題排查

### 問題 1: 授權時選錯帳號了

```bash
# 刪除 token 並重新授權
rm token_accountX.json
python -c "from services.gmail_service import authenticate; authenticate('credentials_accountX.json', 'token_accountX.json')"
```

### 問題 2: 找不到憑證檔案

確保檔案在正確的位置：

```bash
ls -la credentials_*.json token_*.json
```

應該看到所有 6 個檔案。

### 問題 3: 某個帳號獲取失敗

查看錯誤訊息，通常是：
- Token 過期：刪除 token 重新授權
- 憑證路徑錯誤：檢查檔案名稱
- API 未啟用：前往 Google Cloud Console 啟用 Gmail API

### 問題 4: 郵件數量不對

檢查：
1. 時間範圍是否正確（預設 24h）
2. 每個帳號的 `max_emails_per_account` 設定
3. 該時間範圍內是否真的有那麼多郵件

## 進階配置

### 為不同帳號設定不同的過濾條件

修改 [agent/graph.py](agent/graph.py) 中的帳號配置：

```python
accounts = [
    {
        'label': '個人',
        'credentials_path': 'credentials_account1.json',
        'token_path': 'token_account1.json',
        'query': 'is:unread',  # 只獲取未讀郵件
    },
    {
        'label': '工作',
        'credentials_path': 'credentials_account2.json',
        'token_path': 'token_account2.json',
        'query': 'from:boss@company.com OR from:client@company.com',  # 只獲取特定寄件者
    },
]
```

### 按帳號分別處理郵件

在 `classify_importance` 或其他節點中：

```python
def classify_importance(state: EmailSummaryState) -> dict:
    raw_emails = state.get('raw_emails', [])

    # 按帳號分組
    personal_emails = [e for e in raw_emails if e.get('account') == '個人']
    work_emails = [e for e in raw_emails if e.get('account') == '工作']

    # 分別處理
    # 個人郵件可能用不同的分類邏輯
    # 工作郵件可能有更嚴格的重要性判斷

    ...
```

## 下一步

現在你已經完成多帳號設定，可以：

1. ✅ 實作 AI 分類邏輯（根據帳號來源調整）
2. ✅ 在報告中按帳號分組顯示
3. ✅ 為不同帳號設定不同的通知規則
4. ✅ 實作郵件去重（如果有轉發的情況）

詳細說明請參考 [MULTI_ACCOUNT_SETUP.md](MULTI_ACCOUNT_SETUP.md)。
