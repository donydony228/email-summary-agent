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