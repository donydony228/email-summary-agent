# 主執行腳本
# 執行 Email Summary Agent
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def run_email_summary():
    """執行郵件摘要流程"""
    from agent.graph import graph

    # 設定執行參數
    initial_state = {
        "time_range": os.getenv("EMAIL_TIME_RANGE", "24h"),
        "max_emails": int(os.getenv("MAX_EMAILS", "20"))
    }

    # 執行 graph
    result = graph.invoke(initial_state)

    return result

if __name__ == "__main__":
    result = run_email_summary()
