# AI API 服務
# 處理與 AI API 的交互，包含分類和摘要功能
import os, getpass
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing import List, Literal
from langchain_core.messages import HumanMessage, SystemMessage

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")

class EmailImportance(BaseModel):
    """單封郵件的重要性評估"""
    email_id: str
    importance: Literal["high", "medium", "low"]

class EmailsClassification(BaseModel):
    """多封郵件的分類結果"""
    classifications: List[EmailImportance]

def classify_importance(emails: list[dict]) -> dict:
    """分類郵件重要性"""
    print("---Classify Importance---")
    
    raw_emails = emails
    prompt = """
        You are a helpful personal assistant. Please help me classify the importance of the following email: {email_content}.
        Respond with one of the following categories only: "High", "Medium", "Low".
        Definitions:
        - High: The email is urgent, interview invitation, useful information about career like hackathons or course or competition, or from NYU professors' course announcements.
        - Medium: The email is important but does not require immediate action. Such as routine emails from NYU, colleagues, friends, or family members, or auto-response from job website like 104.
        - Low: The email is not important, such as newsletters or promotional content, or emails from Airbnb and Binance or other similar companies.
        """
    
    # 使用 Claude 進行分類
    llm = ChatOpenAI(model="gpt-4o")
    structured_llm = llm.with_structured_output(EmailsClassification)
    
    # 準備郵件資訊
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
    
    # 轉換為 state 格式
    classified = {"high": [], "medium": [], "low": []}
    for classification in result.classifications:
        email = next(e for e in raw_emails if e['id'] == classification.email_id)
        classified[classification.importance].append(email)
    
    return classified