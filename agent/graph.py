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
    email_summaries: NotRequired[list[dict]]
    # 每個 dict 包含: {email_id, importance, summary, key_points}

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
    print("---Fetch Emails---")

    time_range = state.get('time_range', '24h')
    max_emails = state.get('max_emails', 20)

    # 選擇使用單一帳號或多帳號模式
    # 可以透過環境變數 GMAIL_MULTI_ACCOUNT=true 來啟用多帳號模式
    import os
    use_multi_account = os.getenv('GMAIL_MULTI_ACCOUNT', 'false').lower() == 'true'

    if use_multi_account:
        # === 多帳號模式 ===
        from services.gmail_service import fetch_emails_from_multiple_accounts

        # 定義帳號配置
        # 你可以根據需要修改這裡的配置
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

        # 計算每個帳號應該獲取多少封郵件
        max_per_account = (max_emails // len(accounts)) + 1

        emails = fetch_emails_from_multiple_accounts(
            accounts=accounts,
            time_range=time_range,
            max_emails_per_account=max_per_account,
            query=''
        )

        # 確保總數不超過 max_emails
        if len(emails) > max_emails:
            emails = emails[:max_emails]

        print(f"從 {len(accounts)} 個帳號共獲取 {len(emails)} 封郵件")

    else:
        # === 單一帳號模式（預設）===
        from services.gmail_service import fetch_emails_from_gmail

        emails = fetch_emails_from_gmail(time_range, max_emails)

        # 確保不超過 max_emails（額外保護）
        if len(emails) > max_emails:
            emails = emails[:max_emails]

    return {"raw_emails": emails}

def classify_importance(state: EmailSummaryState) -> dict:
    """分類郵件重要性"""
    print("---Classify Importance---")

    # Call AI Service 進行分類
    from services.ai_service import classify_importance
    classified = classify_importance(state['raw_emails'])

    return {"classified_emails": classified}

def summarize_content(state: EmailSummaryState) -> dict:
    """摘要郵件內容"""
    print("---Summarize Content---")

    # TODO: 使用 Claude API 生成摘要
    # from services.claude_service import summarize_emails
    # summaries = summarize_emails(state['classified_emails'])

    # 模擬摘要
    summaries = []
    raw_emails = state.get('raw_emails', [])
    classified = state.get('classified_emails', {})

    for email in raw_emails:
        # 判斷重要性
        importance = 'low'
        if email in classified.get('high', []):
            importance = 'high'
        elif email in classified.get('medium', []):
            importance = 'medium'

        summaries.append({
            'email_id': email['id'],
            'importance': importance,
            'summary': f"Summary of {email['subject']}",
            'key_points': ['Point 1', 'Point 2']
        })

    return {"email_summaries": summaries}

def generate_report(state: EmailSummaryState) -> dict:
    """生成最終報告"""
    print("---Generate Report---")

    # TODO: 格式化報告
    # from services.report_service import generate_markdown_report
    # report = generate_markdown_report(state['email_summaries'])

    # 模擬報告生成
    summaries = state.get('email_summaries', [])

    report = "#Daily Email Summary\n\n"
    report += f"**Time Range**: {state.get('time_range', 'N/A')}\n\n"
    report += f"**Total Emails**: {len(summaries)}\n\n"

    # 按重要性分組
    for importance in ['high', 'medium', 'low']:
        emails_in_category = [s for s in summaries if s['importance'] == importance]
        if emails_in_category:
            report += f"## {importance.upper()} Priority ({len(emails_in_category)})\n\n"
            for summary in emails_in_category:
                report += f"### {summary['email_id']}\n"
                report += f"{summary['summary']}\n\n"

    return {"final_report": report}

def send_notification(state: EmailSummaryState) -> dict:
    """發送通知"""
    print("---Send Notification---")

    # TODO: 發送到 Slack
    # from services.slack_service import send_slack_notification
    # success = send_slack_notification(state['final_report'])

    # 模擬發送
    print(f"Sending report to Slack...")
    print(state.get('final_report', ''))

    return {"report_sent": True}


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
