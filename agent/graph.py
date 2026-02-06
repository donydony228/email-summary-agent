# LangGraph 定義
# 定義整個 Email Summary 的工作流程
from typing import Annotated, NotRequired
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt

## EmailSummaryGraph:
# ├── 郵件獲取節點 (Fetch Emails)
# ├── 重要性分類節點 (Classify Importance)
# ├── 內容摘要節點 (Summarize Content)
# ├── 事件判斷節點 (Event Detection)
# ├── 報告生成節點 (Generate Report)
# └── 通知發送節點 (Send Notification)

## Define state
class EmailSummaryState(TypedDict):
    """Email Summary Agent 的狀態定義"""

    # 輸入參數（必填）
    time_range: str  # "24h", "7d", "30d" 等
    max_emails: int  # 最多處理幾封郵件

    # 郵件資料（可選，執行時產生）
    raw_emails: NotRequired[list[dict]]  # Gmail API 回傳的原始郵件
    # 每個 dict 包含: {id, subject, sender, body, date, ...}

    # 分類結果（可選）
    classified_emails: NotRequired[dict[str, list[dict]]]
    # 格式: {"high": [...], "medium": [...], "low": [...]}

    # 摘要結果（可選）
    email_summaries: NotRequired[dict]
    # dict 包含: {summary, importance_count, important_emails}

    # 事件判斷結果（可選）
    detected_events: NotRequired[list[dict]]
    confirmed_events: NotRequired[list[dict]]  # 用戶確認的事件
    # dict 包含: ["事件標題", "相關信件標題", "起始時間", "結束時間", ...]

    # 最終輸出（可選）
    final_report: NotRequired[str]  # Markdown 格式的最終報告
    report_sent: NotRequired[bool]  # 是否已成功發送

    # 執行記錄（可選）
    messages: NotRequired[Annotated[list[str], add_messages]]  # 執行日誌

    # 錯誤處理（可選）
    error: NotRequired[str | None]
    retry_count: NotRequired[int]


## Define nodes
def fetch_emails(state: EmailSummaryState) -> dict:
    """獲取郵件"""
    time_range = state.get('time_range', '24h')
    max_emails = state.get('max_emails', 20)

    import os
    use_multi_account = os.getenv('GMAIL_MULTI_ACCOUNT', 'false').lower() == 'true'

    if use_multi_account:
        from services.gmail_service import fetch_emails_from_multiple_accounts

        accounts = [
            {
                'label': '個人',
                'credentials_path': 'credentials/credentials_account1.json',
                'token_path': 'credentials/token_account1.json',
                'credentials_base64_env': 'GMAIL_CREDENTIALS_ACCOUNT1_BASE64',
                'token_base64_env': 'GMAIL_TOKEN_ACCOUNT1_BASE64'
            },
            {
                'label': '工作',
                'credentials_path': 'credentials/credentials_account2.json',
                'token_path': 'credentials/token_account2.json',
                'credentials_base64_env': 'GMAIL_CREDENTIALS_ACCOUNT2_BASE64',
                'token_base64_env': 'GMAIL_TOKEN_ACCOUNT2_BASE64'
            },
            {
                'label': '紐約大學',
                'credentials_path': 'credentials/credentials_account3.json',
                'token_path': 'credentials/token_account3.json',
                'credentials_base64_env': 'GMAIL_CREDENTIALS_ACCOUNT3_BASE64',
                'token_base64_env': 'GMAIL_TOKEN_ACCOUNT3_BASE64'
            }
        ]

        max_per_account = (max_emails // len(accounts)) + 1

        emails = fetch_emails_from_multiple_accounts(
            accounts=accounts,
            time_range=time_range,
            max_emails_per_account=max_per_account,
            query=''
        )

        if len(emails) > max_emails:
            emails = emails[:max_emails]

    else:
        from services.gmail_service import fetch_emails_from_gmail

        emails = fetch_emails_from_gmail(time_range, max_emails)

        if len(emails) > max_emails:
            emails = emails[:max_emails]

    return {"raw_emails": emails}

def classify_importance(state: EmailSummaryState) -> dict:
    """分類郵件重要性"""
    from services.ai_service import classify_importance
    classified = classify_importance(state['raw_emails'])

    return {"classified_emails": classified}

def summarize_content(state: EmailSummaryState) -> dict:
    """摘要郵件內容"""
    from services.ai_service import summarize_emails

    raw_emails = state.get('raw_emails', [])
    classified = state.get('classified_emails', {})

    summaries = summarize_emails(raw_emails, classified)

    return {"email_summaries": summaries}

def detect_events(state: EmailSummaryState) -> dict:
    """判斷是否有重要事件"""
    from services.event_service import detect_events_from_emails

    raw_emails = state.get('raw_emails', [])

    events = detect_events_from_emails(raw_emails)

    return {"detected_events": events}

def request_confirmation(state: EmailSummaryState) -> dict:
    """請求用戶確認事件（中斷點）"""
    events = state.get('detected_events', [])
    
    if not events:
        return {"confirmed_events": []}
    
    # 發送 Slack 互動訊息
    from services.slack_service import send_event_confirmation_request
    message_ts = send_event_confirmation_request(events)
    
    # 中斷工作流，等待用戶回應
    confirmed = interrupt({
        "message": "等待用戶確認事件",
        "events": events,
        "message_ts": message_ts
    })
    
    return {"confirmed_events": confirmed}

def create_calendar_events(state: EmailSummaryState) -> dict:
    """創建 Calendar 事件"""
    confirmed_events = state.get('confirmed_events', [])
    
    if not confirmed_events:
        return {"calendar_events_created": []}
    
    from services.calendar_service import create_calendar_event
    
    created_ids = []
    for event_id in confirmed_events:
        # 從 detected_events 中找到完整事件資料
        events = state.get('detected_events', [])
        event = next(e for e in events if e['id'] == event_id)
        
        # 創建 Calendar 事件
        calendar_id = create_calendar_event(event)
        created_ids.append(calendar_id)
    
    return {"calendar_events_created": created_ids}

def generate_report(state: EmailSummaryState) -> dict:
    """生成最終報告"""
    import datetime
    summaries = state.get('email_summaries', {})
    raw_emails = state.get('raw_emails', [])
    classified_emails = state.get('classified_emails', {})

    summary_text = summaries.get('summary', '')

    # 計算各類別郵件數量
    high_emails = classified_emails.get('high', [])
    medium_emails = classified_emails.get('medium', [])
    low_emails = classified_emails.get('low', [])

    report = "# 每日郵件摘要\n\n"
    report += f"**時間範圍**: {state.get('time_range', 'N/A')}\n\n"
    report += f"**執行日期**: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
    report += f"**總郵件數**: {len(raw_emails)}\n\n"

    report += "## 重要性統計\n\n"
    report += f"- 高重要性: {len(high_emails)} 封\n"
    report += f"- 中重要性: {len(medium_emails)} 封\n"
    report += f"- 低重要性: {len(low_emails)} 封\n\n"

    report += "## 摘要內容\n\n"
    # 處理 AI 返回的文本中的 \n 轉義序列
    formatted_summary = summary_text.replace('\\n', '\n')
    report += f"{formatted_summary}\n\n"

    report += "## 事件列表\n\n"
    events = state.get('events', [])
    if events:
        for event in events:
            report += f"- {event}\n"
    else:
        report += "無檢測到的事件。\n"

    if high_emails:
        report += "## 重要郵件列表\n\n"
        for email in high_emails:
            report += f"- **{email.get('subject', '無主旨')}**\n"
            report += f"  - 寄件者: {email.get('from', '未知')}\n"
            if email.get('date'):
                report += f"  - 日期: {email.get('date')}\n"
            report += "\n"

    return {"final_report": report}

def send_notification(state: EmailSummaryState) -> dict:
    """發送通知"""
    from services.slack_service import send_slack_notification

    final_report = state.get('final_report', '')
    success = send_slack_notification(final_report)

    return {"report_sent": success}


# Build graph
builder = StateGraph(EmailSummaryState)

# 1. 加入所有節點
builder.add_node("fetch_emails", fetch_emails)
builder.add_node("classify_importance", classify_importance)
builder.add_node("summarize_content", summarize_content)
builder.add_node("detect_events", detect_events)
builder.add_node("request_confirmation", request_confirmation)
builder.add_node("create_calendar_events", create_calendar_events)
builder.add_node("generate_report", generate_report)
builder.add_node("send_notification", send_notification)

# 2. 定義執行流程（邊）
builder.add_edge(START, "fetch_emails")
builder.add_edge("fetch_emails", "classify_importance")
builder.add_edge("classify_importance", "summarize_content")
builder.add_edge("summarize_content", "detect_events")
builder.add_edge("detect_events", "generate_report")
builder.add_edge("generate_report", "send_notification")

# 條件路由：發送通知後，如果有事件 → 請求確認；無事件 → 結束
def should_request_confirmation(state: EmailSummaryState) -> str:
    events = state.get('detected_events', [])
    return "request_confirmation" if events else "end"

builder.add_conditional_edges(
    "send_notification",
    should_request_confirmation,
    {
        "request_confirmation": "request_confirmation",
        "end": END
    }
)

builder.add_edge("request_confirmation", "create_calendar_events")
builder.add_edge("create_calendar_events", END)

# 5. 編譯 graph（使用 checkpointer）
import sqlite3

# 創建持久化的 SQLite 連接和 checkpointer
conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
graph = builder.compile(checkpointer=checkpointer)
