# Email Summary Agent - HITL 擴展實施計劃

## 概述

為現有的 Email Summary Agent 添加 **Human-in-the-Loop (HITL)** 功能：識別郵件中的行程/事件，通過 Slack 確認後自動加入 Google Calendar。

## 架構變更總覽

### 現有流程
```
fetch_emails → classify → summarize → generate_report → send_notification
```

### 擴展後流程
```
fetch_emails → classify → summarize → detect_events
                                           ↓
                     [有事件] → request_confirmation (Slack)
                                     ↓
                              create_calendar_events
                                     ↓
                     [無事件] ←──────┘
                         ↓
                 generate_report → send_notification
```

## 實施策略：漸進式方案（推薦）

考慮到完整 HITL 的複雜性（需要 Web 服務器、Slack App 配置），推薦分階段實施：

### Phase 1: 事件檢測 (優先級 ⭐⭐⭐⭐)
**預估時間**: 2-3 小時
**風險**: 低
**價值**: 中

**實施內容**:
- 使用 GPT-4o 從郵件中提取事件資訊
- 檢測面試、會議、課程等行程
- 在報告中顯示檢測到的事件（暫不確認）

**技術細節**:
- 新增文件: `services/event_service.py`
- 新增節點: `detect_events`
- 擴展狀態: 添加 `detected_events: list[dict]`
- Pydantic 模型: `DetectedEvent`, `EventsDetection`

### Phase 2A: 簡化版 HITL - Email 確認 (優先級 ⭐⭐⭐)
**預估時間**: 3-4 小時
**風險**: 中
**價值**: 中

**實施內容**:
- 整合 Google Calendar API
- 生成確認連結發送到 Slack
- 用戶點擊連結確認後創建 Calendar 事件
- 無需 Web 服務器（使用靜態頁面 + Webhook）

**技術細節**:
- 新增文件: `services/calendar_service.py`
- 修改: `services/slack_service.py` (添加確認訊息)
- 新增節點: `create_calendar_events`
- 依賴: Google Calendar API credentials

**優點**: 簡單、無需服務器
**缺點**: 用戶體驗較差（需要點擊郵件/連結）

### Phase 2B: 完整版 HITL - Slack App 互動 (優先級 ⭐⭐⭐⭐⭐)
**預估時間**: 6-8 小時（首次設置）
**風險**: 高
**價值**: 高

**實施內容**:
- 創建 Slack App，啟用 Interactivity
- 實現 Block Kit 互動訊息（按鈕確認）
- 部署 FastAPI 服務接收 Slack 回調
- 使用 LangGraph checkpointer 實現工作流程中斷和恢復

**技術細節**:
- 新增文件: `api/server.py` (FastAPI 服務)
- 升級: `services/slack_service.py` (Slack Web API + Block Kit)
- 新增節點: `request_confirmation` (帶 NodeInterrupt)
- 部署: Railway / Render (免費)
- 依賴: `slack-sdk`, `fastapi`, `uvicorn`

**優點**: 最佳用戶體驗、完整功能
**缺點**: 需要 Web 服務器、配置較複雜

---

## 關鍵文件變更

### 新增文件

1. **`services/event_service.py`** (事件檢測)
   ```python
   class DetectedEvent(BaseModel):
       id: str
       email_id: str
       title: str
       start_time: datetime
       end_time: datetime
       location: Optional[str]
       description: Optional[str]
       confidence: float

   def detect_events_from_emails(emails: list[dict]) -> list[dict]
   ```

2. **`services/calendar_service.py`** (Google Calendar)
   ```python
   def authenticate_calendar() -> Credentials
   def get_calendar_service() -> Resource
   def create_calendar_event(event_data: dict) -> str
   ```

3. **`api/server.py`** (僅 Phase 2B)
   ```python
   @app.post("/slack/interactive")
   async def handle_slack_interaction(request: Request)

   @app.post("/webhook/email-summary")
   async def trigger_email_summary()
   ```

### 修改文件

1. **`agent/graph.py`**
   - 擴展 `EmailSummaryState`:
     ```python
     # HITL 相關
     detected_events: NotRequired[list[dict]]
     pending_confirmations: NotRequired[list[str]]
     confirmed_events: NotRequired[list[dict]]
     calendar_events_created: NotRequired[list[str]]
     ```

   - 添加新節點函數:
     ```python
     def detect_events(state: EmailSummaryState) -> dict
     def request_confirmation(state: EmailSummaryState) -> dict  # Phase 2B
     def create_calendar_events(state: EmailSummaryState) -> dict
     ```

   - 更新 graph 構建:
     ```python
     # 添加節點
     builder.add_node("detect_events", detect_events)
     builder.add_node("create_calendar_events", create_calendar_events)

     # 添加條件路由
     def should_request_confirmation(state: EmailSummaryState) -> str:
         events = state.get('detected_events', [])
         return "request_confirmation" if events else "skip_confirmation"

     builder.add_conditional_edges(
         "detect_events",
         should_request_confirmation,
         {
             "request_confirmation": "request_confirmation",
             "skip_confirmation": "generate_report"
         }
     )

     # 編譯（Phase 2B 需要 checkpointer）
     checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
     graph = builder.compile(checkpointer=checkpointer)
     ```

2. **`services/slack_service.py`**
   - Phase 1: 添加事件顯示到報告
   - Phase 2A: 添加確認連結訊息
   - Phase 2B: 升級到 Slack Web API + Block Kit
     ```python
     def send_event_confirmation_request(events: list[dict]) -> str:
         """發送 Block Kit 互動訊息"""
         blocks = [...]  # 包含按鈕的 Block Kit
         response = slack_client.chat_postMessage(...)
         return response['ts']
     ```

3. **`requirements.txt`**
   ```
   # Google Calendar (已有 google-auth, google-api-python-client)

   # Phase 2B only
   slack-sdk
   fastapi
   uvicorn
   ```

4. **`.env.example`**
   ```env
   # Google Calendar
   GOOGLE_CALENDAR_CREDENTIALS_PATH=credentials/calendar_credentials.json
   GOOGLE_CALENDAR_TOKEN_PATH=credentials/calendar_token.json

   # Phase 2B only
   SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   ```

---

## 詳細實現方案

### 1. 事件檢測服務

```python
# services/event_service.py
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DetectedEvent(BaseModel):
    """檢測到的事件"""
    id: str  # 唯一標識
    email_id: str  # 來源郵件 ID
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)  # 置信度 0-1

class EventsDetection(BaseModel):
    """事件檢測結果"""
    events: list[DetectedEvent]

def detect_events_from_emails(emails: list[dict]) -> list[dict]:
    """從郵件中檢測事件/行程

    Args:
        emails: 郵件列表

    Returns:
        list[dict]: 檢測到的事件列表
    """
    if not emails:
        return []

    llm = ChatOpenAI(model="gpt-4o")
    structured_llm = llm.with_structured_output(EventsDetection)

    prompt = """你是一個專業的行程助手。請分析以下郵件，檢測其中的事件/行程資訊。

## 檢測規則：
1. **明確的事件**：面試、會議、課程、活動等
2. **時間資訊**：必須包含明確的日期和時間
3. **置信度**：
   - 0.9-1.0: 明確的行程邀請（如 Google Calendar 邀請、面試確認）
   - 0.7-0.9: 包含時間地點的活動通知
   - 0.5-0.7: 模糊的時間資訊（需要用戶確認）
   - < 0.5: 不提取

## 輸出格式：
為每個檢測到的事件生成：
- id: 使用 email_id + '_event_' + 序號
- title: 事件標題
- start_time: 開始時間（ISO格式）
- end_time: 結束時間（如果沒有明確說明，預設1小時）
- location: 地點（如果有）
- description: 詳細說明
- confidence: 置信度分數

## 待分析郵件：
"""

    emails_text = "\n\n".join([
        f"ID: {email['id']}\n主旨: {email['subject']}\n寄件者: {email['from']}\n內容: {email['body'][:500]}"
        for email in emails
    ])

    result = structured_llm.invoke(prompt + emails_text)

    # 過濾低置信度事件
    filtered_events = [
        e.model_dump() for e in result.events
        if e.confidence >= 0.7
    ]

    return filtered_events
```

### 2. Google Calendar 服務

```python
# services/calendar_service.py
import os
import pickle
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# 權限範圍
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_calendar(
    credentials_path: str = 'credentials/calendar_credentials.json',
    token_path: str = 'credentials/calendar_token.json'
) -> Credentials:
    """Google Calendar API 認證"""
    creds = None

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds

def get_calendar_service():
    """獲取 Calendar API 服務實例"""
    creds = authenticate_calendar()
    return build('calendar', 'v3', credentials=creds)

def create_calendar_event(event_data: dict) -> str:
    """創建 Calendar 事件

    Args:
        event_data: {
            'title': str,
            'start_time': datetime,
            'end_time': datetime,
            'location': str,
            'description': str
        }

    Returns:
        str: 創建的事件 ID
    """
    service = get_calendar_service()

    # 格式化事件
    event = {
        'summary': event_data['title'],
        'location': event_data.get('location', ''),
        'description': event_data.get('description', ''),
        'start': {
            'dateTime': event_data['start_time'].isoformat(),
            'timeZone': 'Asia/Taipei',
        },
        'end': {
            'dateTime': event_data['end_time'].isoformat(),
            'timeZone': 'Asia/Taipei',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # 1天前
                {'method': 'popup', 'minutes': 30},  # 30分鐘前
            ],
        },
    }

    # 創建事件
    created_event = service.events().insert(
        calendarId='primary',
        body=event
    ).execute()

    return created_event['id']
```

### 3. Slack Block Kit 互動訊息（Phase 2B）

```python
# services/slack_service.py 新增函數

def send_event_confirmation_request(events: list[dict]) -> str:
    """發送事件確認請求（Slack 互動訊息）"""
    from slack_sdk import WebClient

    client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
    channel_id = os.getenv('SLACK_CHANNEL_ID')

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "檢測到行程/事件，請確認是否加入日曆"
            }
        },
        {"type": "divider"}
    ]

    for event in events:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{event['title']}*\n時間: {event['start_time']} - {event['end_time']}\n地點: {event.get('location', '無')}"
                }
            },
            {
                "type": "actions",
                "block_id": f"event_{event['id']}",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "確認加入"},
                        "style": "primary",
                        "value": event['id'],
                        "action_id": "confirm_event"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "跳過"},
                        "style": "danger",
                        "value": event['id'],
                        "action_id": "skip_event"
                    }
                ]
            }
        ])

    response = client.chat_postMessage(
        channel=channel_id,
        blocks=blocks
    )

    return response['ts']  # message timestamp
```

---

## 部署架構對比

### 選項 A: GitHub Actions Only (Phase 1)
- ✅ 完全免費
- ✅ 無需額外配置
- ✅ 事件檢測（報告模式）
- ❌ 無法自動加入 Calendar

### 選項 B: GitHub Actions + 簡化 HITL (Phase 1 + 2A)
- ✅ 免費
- ✅ 可以加入 Calendar
- ⚠️ 用戶體驗一般（需點擊連結）
- ⚠️ 需要配置 Google Calendar API

### 選項 C: Railway + FastAPI + Slack App (Phase 1 + 2B)
- ✅ 最佳用戶體驗（Slack 內直接確認）
- ✅ 完整功能
- ⚠️ 需要部署 Web 服務器（Railway $5/月免費額度）
- ⚠️ 需要配置 Slack App

---

## 成本估算

| 項目 | 每月成本 |
|------|----------|
| OpenAI GPT-4o (事件檢測) | ~$1.00 |
| Railway Free Tier (Phase 2B) | $0 (在免費額度內) |
| **總計** | **~$1.00/月** |

---

## 測試與驗證

### Phase 1 驗證 (事件檢測)
```bash
# 準備測試郵件（包含面試邀請）
python test_event_detection.py

# 檢查生成的報告
# 應該看到 "檢測到的事件" 章節
```

### Phase 2A 驗證 (簡化 HITL)
```bash
# 測試確認連結
# 1. 觸發流程
# 2. 檢查 Slack 訊息
# 3. 點擊連結
# 4. 驗證 Calendar 事件創建
```

### Phase 2B 驗證 (完整 HITL)
```bash
# 測試 Slack 互動
# 1. 觸發流程
# 2. 在 Slack 中點擊按鈕
# 3. 驗證 Calendar 事件創建
# 4. 檢查工作流程恢復
```

---

## 風險與緩解

### 風險 1: 事件檢測準確率低
**緩解**:
- 設定高置信度閾值（≥ 0.7）
- 優化提示詞，提供明確的檢測規則
- 允許用戶在確認時編輯事件詳情

### 風險 2: Slack App 配置複雜 (Phase 2B)
**緩解**:
- 提供詳細的配置指南
- 先實現 Phase 2A 驗證流程
- 考慮使用 Telegram Bot 作為替代

### 風險 3: Google Calendar API 配額限制
**緩解**:
- 批次創建事件
- 緩存已創建的事件避免重複
- 使用指數退避處理限流

---

## 推薦實施順序

1. **立即開始**: Phase 1 (事件檢測)
   - 低風險，中等價值
   - 獨立功能，可以先在報告中展示
   - 收集反饋，了解檢測準確度

2. **接下來**: Phase 2A (簡化 HITL)
   - 簡單實現
   - 可以實際使用
   - 驗證 Calendar 整合

3. **可選升級**: Phase 2B (完整 HITL)
   - 最佳用戶體驗
   - 需要更多時間配置
   - 適合長期使用

---

## 下一步行動

請確認你希望實施的方案：
- [ ] 只實施 Phase 1 (事件檢測)
- [ ] Phase 1 + Phase 2A (簡化 HITL)
- [ ] 完整實施 Phase 1 + 2B (完整 HITL)

確認後，我將開始實施代碼。
