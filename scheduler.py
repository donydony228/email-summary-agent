# 定時執行調度器
# 每天定時運行 Email Summary Agent
import os
import time
import schedule
from datetime import datetime
from init_credentials import init_credentials
from main import run_email_summary

def job():
    """執行郵件摘要任務"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始執行郵件摘要...")
    
    try:
        result = run_email_summary()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 執行完成")
        print(f"報告已發送: {result.get('report_sent', False)}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 執行失敗: {str(e)}")

def main():
    """主程式"""
    print("正在初始化 Gmail credentials...")
    init_credentials()
    
    # 從環境變數讀取執行時間，預設為每天早上 9:00
    schedule_time = os.getenv("SCHEDULE_TIME", "09:00")
    
    print(f"郵件摘要調度器已啟動")
    print(f"將在每天 {schedule_time} 執行")
    
    # 設定每天執行的時間
    schedule.every().day.at(schedule_time).do(job)
    
    # 如果設定立即執行，則先執行一次
    if os.getenv("RUN_ON_STARTUP", "false").lower() == "true":
        print("啟動時立即執行一次...")
        job()
    
    # 持續運行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分鐘檢查一次

if __name__ == "__main__":
    main()
