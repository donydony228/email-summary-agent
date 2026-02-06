# AI API 服務
# 處理與 AI API 的交互，包含分類和摘要功能
import os, getpass
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Literal
from langchain_core.messages import HumanMessage, SystemMessage

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

# ===== 郵件分類相關 =====

class EmailImportance(BaseModel):
    """單封郵件的重要性評估"""
    email_id: str
    importance: Literal["high", "medium", "low"]

class EmailsClassification(BaseModel):
    """多封郵件的分類結果"""
    classifications: List[EmailImportance]

def classify_importance(emails: list[dict]) -> dict:
    """分類郵件重要性

    Args:
        emails: 郵件列表

    Returns:
        dict: {"high": [...], "medium": [], "low": [...]}
    """
    raw_emails = emails

    # 如果沒有郵件，直接返回空分類
    if not raw_emails:
        return {"high": [], "medium": [], "low": []}

    prompt = """
        You are a helpful personal assistant. Please help me classify the importance of the following email: {email_content}.
        Respond with one of the following categories only: "High", "Medium", "Low".
        Definitions:
        - High: The email is urgent, interview invitation, useful information about career like hackathons or course or competition, or from NYU professors' course announcements.
        - Medium: The email is important but does not require immediate action. Such as routine emails from NYU, colleagues, friends, or family members, or auto-response from job website like 104 website.
        - Low: The email is not important, such as newsletters or promotional content, or emails from Airbnb and Binance or other similar companies, or random people who want to connect with me on LinkedIn.
        """

    llm = ChatOpenAI(model="gpt-4o")
    structured_llm = llm.with_structured_output(EmailsClassification)

    emails_text = "\n\n".join([
        f"ID: {email['id']}\n主旨: {email['subject']}\n寄件者: {email['from']}\n內容: {email['snippet']}"
        for email in raw_emails
    ])

    result = structured_llm.invoke(
        [
            SystemMessage(content="You are a helpful personal assistant."),
            HumanMessage(content=f"Classify the importance of the following emails:\n\n{emails_text}\n\n{prompt}")
        ]
    )

    classified = {"high": [], "medium": [], "low": []}
    for classification in result.classifications:
        # 使用 next 的 default 參數避免 StopIteration
        email = next((e for e in raw_emails if e['id'] == classification.email_id), None)
        if email:
            classified[classification.importance].append(email)

    return classified


# ===== 郵件總結相關 =====

class ImportanceCount(BaseModel):
    """郵件重要性統計"""
    high: int = Field(description="高重要性郵件數量")
    medium: int = Field(description="中重要性郵件數量")
    low: int = Field(description="低重要性郵件數量")

class ImportantEmailInfo(BaseModel):
    """重要郵件資訊"""
    to: str = Field(description="收件者")
    sender: str = Field(alias="from", description="寄件者")
    subject: str = Field(description="主旨")

class EmailSummary(BaseModel):
    """總結當日信件狀況"""
    summary: str = Field(description="整體摘要文字")

def summarize_emails(emails: list[dict], classified_emails: dict) -> dict:
    """總結當日信件狀況

    Args:
        emails: 原始郵件列表
        classified_emails: 分類後的郵件 {"high": [...], "medium": [...], "low": [...]}

    Returns:
        dict: {
            "summary": str,
            "importance_count": {"high": int, "medium": int, "low": int},
            "important_emails": [{"to": str, "from": str, "subject": str}]
        }
    """
    llm = ChatOpenAI(model="gpt-4o")
    structured_llm = llm.with_structured_output(EmailSummary)

    prompt = """你是一個專業的郵件摘要助手。請分析以下郵件內容，提供簡潔的每日郵件摘要報告。

## 摘要格式要求：

1. **整體概況**（2-3句話）
   - 簡要描述今日郵件的總體情況、數量和主要類型

2. **求職相關信件**
   - 用1-2段自然的文字描述求職相關的郵件
   - 重點突出重要的郵件（如面試邀請、職缺通知、招募信息）
   - 次要的郵件（如求職網站自動回覆、LinkedIn系統通知）可以簡單帶過
   - 如果沒有此類郵件，顯示「無」

3. **紐約大學相關**
   - 用1-2段自然的文字描述學校相關的郵件
   - 重點突出重要事項（如課程通知、截止日期、重要公告）
   - 一般的郵件（如活動宣傳、訂閱電子報）可以簡單帶過
   - 如果沒有此類郵件，顯示「無」

4. **其他信件**
   - 用1段文字描述其他重要郵件
   - 忽略廣告、促銷等非重要郵件
   - 如果沒有需要關注的郵件，顯示「無」

## 注意事項：
- 使用自然流暢的段落式描述，不要逐條列舉
- 突出重要郵件的關鍵資訊（如時間、地點、需要採取的行動）
- 次要郵件簡單提及即可，不需要詳細說明
- 整體摘要保持簡潔，每個分類不超過3-4句話
- 使用繁體中文輸出

## 範例風格：
求職相關：今天收到最重要的是 A 公司邀請你在 1/25 與他們進行簡短的線上面試。另外有幾封求職網站的自動回覆信件，但不是特別重要。此外，有來自 LinkedIn 的系統訊息，有人想與你建立連結。"""

    emails_text = "\n".join([email.get('snippet', '') for email in emails])

    summary_part = structured_llm.invoke(
        [
            SystemMessage(content="You are a helpful personal assistant."),
            HumanMessage(content=f"""Please summarize the following classified emails:

郵件內容：
{emails_text}

{prompt}""")
        ]
    )

    return {
        "summary": summary_part.summary
    }