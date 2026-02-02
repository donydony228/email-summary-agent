# Email Summary Agent

一個基於 AI 的 Gmail 信件總結系統，使用 LangGraph 構建智能代理工作流程，自動獲取、分類、摘要郵件，並透過 Slack 發送通知。

## 專案簡介

此系統透過整合 Gmail API、Claude API 和 LangGraph，自動化處理郵件總結流程：
- 自動獲取指定時間範圍內的郵件
- 使用 AI 智能分類郵件重要性
- 生成簡潔的郵件摘要
- 產生結構化報告
- 透過 Slack 推送通知

## 功能特色

- **智能分類**：使用 AI 自動判斷郵件重要性
- **精準摘要**：提取關鍵資訊，節省閱讀時間
- **工作流程管理**：使用 LangGraph 構建可視化、可維護的 Agent 流程
- **多渠道通知**：支援 Slack、Email 等多種通知方式
- **易於部署**：使用 GitHub Actions 免費部署
- **定時執行**：每日自動執行，無需維護服務器

## 專案結構

```
email-summary-agent/
├── main.py                      # 主執行腳本
├── init_credentials.py          # Credentials 初始化
├── encode_credentials.py        # Base64 編碼工具
├── agent/
│   ├── __init__.py
│   ├── graph.py                # LangGraph 工作流程定義
│   ├── nodes.py                # 各節點實作
│   └── prompts.py              # Prompt 模板
├── services/
│   ├── __init__.py
│   ├── gmail_service.py        # Gmail API 服務
│   ├── ai_service.py           # AI 分類與摘要服務
│   └── slack_service.py        # Slack 通知服務
├── .github/
│   └── workflows/
│       └── email-summary.yml   # GitHub Actions 工作流程
├── .env.example                # 環境變數範例
├── .gitignore
└── requirements.txt            # Python 依賴套件
```

## 系統架構

### 核心組件

#### 1. LangGraph 流程控制層
```
EmailSummaryGraph:
├── 郵件獲取節點 (Fetch Emails)
├── 重要性分類節點 (Classify Importance)
├── 內容摘要節點 (Summarize Content)
├── 報告生成節點 (Generate Report)
└── 通知發送節點 (Send Notification)
```

#### 2. 服務層
- **Gmail API 連接器**：支援 OAuth 2.0 認證，獲取郵件內容
- **Claude API**：使用 Claude Sonnet 4.5 進行分類和摘要
- **Slack Webhook**：發送格式化的通知訊息

#### 3. 數據層（可選擴展）
- 向量資料庫（Pinecone 或 Weaviate）：儲存郵件嵌入
- PostgreSQL：儲存處理記錄和用戶偏好

## 快速開始

### 前置需求

- Python 3.9 或以上版本
- Gmail 帳號
- Claude API Key（從 [Anthropic Console](https://console.anthropic.com/) 取得）
- Slack Webhook URL（可選）

### 安裝步驟

1. **Clone 專案**
```bash
git clone <repository-url>
cd email-summary-agent
```

2. **建立虛擬環境**
```bash
python -m venv venv
source venv/bin/activate  # Windows 使用: venv\Scripts\activate
```

3. **安裝依賴套件**
```bash
pip install -r requirements.txt
```

4. **設定環境變數**

複製 `.env.example` 為 `.env`：
```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入以下資訊：
```env
# Claude API
CLAUDE_API_KEY=your_claude_api_key_here

# Gmail API
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# Slack (可選)
SLACK_WEBHOOK_URL=your_slack_webhook_url_here

# 應用設定
PORT=8000
```

5. **設定 Gmail API**

a. 前往 [Google Cloud Console](https://console.cloud.google.com/)
b. 建立新專案或選擇現有專案
c. 啟用 Gmail API
d. 建立 OAuth 2.0 憑證（桌面應用程式）
e. 下載憑證檔案並儲存為 `credentials.json` 於專案根目錄

6. **首次授權 Gmail**
```bash
# 執行後會開啟瀏覽器進行 OAuth 授權
python -c "from services.gmail_service import authenticate; authenticate()"
```

### 啟動專案

**開發模式**
```bash
# 使用 uvicorn 啟動 FastAPI 伺服器
uvicorn main:app --reload --port 8000
```

**生產模式**
```bash
# 使用 gunicorn + uvicorn workers
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**直接執行 Agent（無 API 模式）**
```bash
python main.py
```

### 測試 API

啟動後，可以透過以下方式測試：

```bash
# 觸發郵件摘要
curl -X POST http://localhost:8000/api/summarize

# 查看健康狀態
curl http://localhost:8000/health
```

API 文件：訪問 `http://localhost:8000/docs` 查看 Swagger UI

## 部署

### 推薦：使用 GitHub Actions（永久免費）

GitHub Actions 是最推薦的部署方式，完全免費且易於設置。

詳細部署步驟請參考：[GitHub Actions 部署指南](GITHUB_ACTIONS_GUIDE.md)

**快速步驟：**
1. 運行 `python encode_credentials.py` 生成 base64 編碼的 credentials
2. 在 GitHub 倉庫設定 Secrets（Settings → Secrets and variables → Actions）
3. 推送代碼到 GitHub
4. Workflow 會自動每天執行

**優勢：**
- 完全免費（每月 2000 分鐘）
- 無需信用卡
- 自動執行，無需維護服務器
- 易於調整執行時間

## 使用說明

### 基本工作流程

1. 系統從 Gmail 獲取指定時間範圍的郵件
2. AI 分析每封郵件的重要性（高/中/低）
3. 生成每封重要郵件的摘要
4. 整合成結構化報告
5. 透過 Slack 或 Email 發送通知

### 自訂設定

可以在各個模組中自訂：
- **Prompts**（`agent/prompts.py`）：調整 AI 分類和摘要的提示詞
- **Nodes**（`agent/nodes.py`）：修改各節點的處理邏輯
- **Graph**（`agent/graph.py`）：調整工作流程順序

## 技術棧

- **AI Agent**：LangGraph
- **LLM**：OpenAI GPT-4o
- **郵件服務**：Gmail API
- **通知服務**：Slack Webhook
- **部署平台**：GitHub Actions

## 開發注意事項

- 所有敏感資訊（API Keys、Tokens）都應存放在 `.env` 檔案和 GitHub Secrets 中
- Gmail API 有配額限制，建議合理設定郵件獲取範圍
- OpenAI API 按 Token 計費，注意控制摘要長度
- 建議使用虛擬環境隔離專案依賴
- GitHub Actions 免費方案每月 2000 分鐘，足夠每日運行

## 授權

MIT License

## 貢獻

歡迎提交 Issue 或 Pull Request！
