# LangGraph 定義
# 定義整個 Email Summary 的工作流程
from typing import Annotated, NotRequired
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

## EmailSummaryGraph:
# ├── 郵件獲取節點 (Fetch Emails)
# ├── 重要性分類節點 (Classify Importance)
# ├── 內容摘要節點 (Summarize Content)
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
                'token_path': 'credentials/token_account1.json'
            },
            {
                'label': '工作',
                'credentials_path': 'credentials/credentials_account2.json',
                'token_path': 'credentials/token_account2.json'
            },
            {
                'label': '紐約大學',
                'credentials_path': 'credentials/credentials_account3.json',
                'token_path': 'credentials/token_account3.json'
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
    report += f"{summary_text}\n\n"

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
builder.add_node("generate_report", generate_report)
builder.add_node("send_notification", send_notification)

# 2. 定義執行流程（邊）
builder.add_edge(START, "fetch_emails")
builder.add_edge("fetch_emails", "classify_importance")
builder.add_edge("classify_importance", "summarize_content")
builder.add_edge("summarize_content", "generate_report")
builder.add_edge("generate_report", "send_notification")
builder.add_edge("send_notification", END)

# 3. 設定入口節點（可選，如果只有一個入口可省略）
# builder.set_entry_point("fetch_emails")

# 4. 設定結束節點（可選，已經用 add_edge 到 END 了）
# builder.set_finish_point("send_notification")

# Compile graph
graph = builder.compile()
