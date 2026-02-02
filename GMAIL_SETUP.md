# Gmail API 設定指南

本指南將幫助你設定 Gmail API，以便在專案中獲取 Gmail 郵件內容。

## 步驟 1: 安裝依賴套件

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

## 步驟 2: 建立 Google Cloud 專案

### 2.1 前往 Google Cloud Console

訪問：https://console.cloud.google.com/

### 2.2 建立新專案

1. 點擊頂部的專案下拉選單
2. 點擊「新增專案」
3. 輸入專案名稱（例如：`email-summary-agent`）
4. 點擊「建立」

### 2.3 啟用 Gmail API

1. 在左側選單中選擇「API 和服務」→「程式庫」
2. 搜尋「Gmail API」
3. 點擊「Gmail API」
4. 點擊「啟用」

## 步驟 3: 建立 OAuth 2.0 憑證

### 3.1 設定 OAuth 同意畫面

1. 前往「API 和服務」→「OAuth 同意畫面」
2. 選擇「外部」（External）→ 點擊「建立」
3. 填寫必要資訊：
   - **應用程式名稱**：`Email Summary Agent`
   - **使用者支援電子郵件**：你的 Gmail 地址
   - **開發人員聯絡資訊**：你的 Gmail 地址
4. 點擊「儲存並繼續」
5. **範圍（Scopes）**：點擊「新增或移除範圍」
   - 搜尋並新增：`https://www.googleapis.com/auth/gmail.readonly`
   - 點擊「更新」→「儲存並繼續」
6. **測試使用者**：新增你的 Gmail 地址
7. 點擊「儲存並繼續」

### 3.2 建立 OAuth 2.0 用戶端 ID

1. 前往「API 和服務」→「憑證」
2. 點擊「+ 建立憑證」→ 選擇「OAuth 用戶端 ID」
3. 應用程式類型選擇「**桌面應用程式**」
4. 名稱輸入：`Email Summary Agent Desktop`
5. 點擊「建立」

### 3.3 下載憑證檔案

1. 在憑證列表中，找到剛建立的 OAuth 2.0 用戶端
2. 點擊右側的「下載」圖示（⬇️）
3. 將下載的 JSON 檔案重新命名為 `credentials.json`
4. 將 `credentials.json` 放到專案根目錄

```
email-summary-agent/
├── credentials.json  ← 放在這裡
├── agent/
├── services/
└── ...
```

⚠️ **重要**：`credentials.json` 包含敏感資訊，**不要上傳到 GitHub**！
（已經加入 `.gitignore`）

## 步驟 4: 首次授權

執行以下命令進行首次授權：

```bash
python services/gmail_service.py
```

或者：

```bash
python -c "from services.gmail_service import authenticate; authenticate()"
```

### 授權流程

1. 瀏覽器會自動開啟 Google 授權頁面
2. 選擇你的 Gmail 帳號
3. 確認權限（允許讀取郵件）
4. 授權成功後，會在專案根目錄生成 `token.json`

```
email-summary-agent/
├── credentials.json
├── token.json  ← 自動生成
├── agent/
└── ...
```

⚠️ **重要**：`token.json` 也是敏感資訊，**不要上傳到 GitHub**！

## 步驟 5: 測試 Gmail API

執行測試腳本：

```bash
python services/gmail_service.py
```

如果成功，你會看到：

```
============================================================
Gmail API 測試
============================================================
📧 搜尋郵件: after:1737532800
📬 找到 10 封郵件，開始獲取詳細內容...
  ✅ [1/10] Meeting Reminder...
  ✅ [2/10] Project Update...
  ...
✅ 成功獲取 10 封郵件

============================================================
郵件摘要:
============================================================

[1] Meeting Reminder
    寄件者: alice@example.com
    日期: Mon, 15 Jan 2024 10:00:00 +0800
    預覽: Don't forget our meeting tomorrow at 10am...
...
```

## 步驟 6: 在 Graph 中使用

更新 `agent/graph.py` 中的 `fetch_emails` 節點：

```python
def fetch_emails(state: EmailSummaryState) -> dict:
    """獲取郵件"""
    print("---Fetch Emails---")

    # 使用 Gmail API
    from services.gmail_service import fetch_emails_from_gmail

    emails = fetch_emails_from_gmail(
        time_range=state['time_range'],
        max_emails=state['max_emails']
    )

    return {"raw_emails": emails}
```

## 常見問題

### Q1: 出現 "The file token.json is not present" 錯誤

**解決方法**：刪除 `token.json` 並重新授權

```bash
rm token.json
python services/gmail_service.py
```

### Q2: 授權頁面顯示「此應用程式未經驗證」

**解決方法**：這是正常的，因為應用程式處於測試模式

1. 點擊「進階」
2. 點擊「前往 Email Summary Agent (不安全)」
3. 繼續授權流程

### Q3: Token 過期怎麼辦？

**解決方法**：程式會自動更新 Token，不需要手動處理

如果自動更新失敗，刪除 `token.json` 重新授權即可。

### Q4: 如何修改權限範圍？

**解決方法**：

1. 修改 `services/gmail_service.py` 中的 `SCOPES`
2. 刪除 `token.json`
3. 重新授權

### Q5: 如何獲取多個 Gmail 帳號的郵件？

**解決方法**：

每個帳號需要獨立的 credentials 和 token：

```python
# 帳號 1
emails_1 = fetch_emails_from_gmail(
    credentials_path='credentials_1.json',
    token_path='token_1.json'
)

# 帳號 2
emails_2 = fetch_emails_from_gmail(
    credentials_path='credentials_2.json',
    token_path='token_2.json'
)
```

## 進階用法

### 自訂搜尋查詢

```python
# 只獲取未讀郵件
emails = fetch_emails_from_gmail(query='is:unread')

# 只獲取特定寄件者的郵件
emails = fetch_emails_from_gmail(query='from:alice@example.com')

# 只獲取有附件的郵件
emails = fetch_emails_from_gmail(query='has:attachment')

# 組合查詢
emails = fetch_emails_from_gmail(
    time_range='7d',
    query='is:unread has:attachment'
)
```

### Gmail 搜尋語法

- `is:unread` - 未讀郵件
- `is:starred` - 已加星號
- `from:email@example.com` - 來自特定寄件者
- `to:email@example.com` - 寄給特定收件者
- `subject:關鍵字` - 主旨包含關鍵字
- `has:attachment` - 有附件
- `label:標籤名稱` - 特定標籤
- `in:inbox` - 收件匣
- `in:sent` - 寄件備份

更多搜尋語法：https://support.google.com/mail/answer/7190

## 相關連結

- [Gmail API 文件](https://developers.google.com/gmail/api)
- [Python 快速入門](https://developers.google.com/gmail/api/quickstart/python)
- [OAuth 2.0 說明](https://developers.google.com/identity/protocols/oauth2)

## 安全注意事項

1. ⚠️ **絕對不要**將 `credentials.json` 和 `token.json` 上傳到 GitHub
2. ✅ 使用 `.gitignore` 排除這些檔案（已設定）
3. ✅ 在生產環境使用環境變數或秘密管理服務
4. ✅ 定期檢查 Google Cloud Console 的使用情況
5. ✅ 只授予必要的最小權限

## 下一步

現在 Gmail API 已經設定完成，你可以：

1. ✅ 測試獲取真實的 Gmail 郵件
2. 🔄 實作 Claude API 進行郵件分類和摘要
3. 📨 實作 Slack 通知服務
4. 🚀 整合到完整的 LangGraph 工作流程
