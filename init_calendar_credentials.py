"""
Google Calendar API 授權腳本
用於生成 calendar_credentials.json 和 calendar_token.json
"""
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Calendar API 需要的權限範圍
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_calendar(
    credentials_path: str = 'credentials/credentials_account1.json',
    token_path: str = 'credentials/calendar_token.json'
):
    """
    為 Google Calendar API 進行 OAuth 授權

    Args:
        credentials_path: OAuth 2.0 憑證文件路徑（可使用 Gmail 的同一個）
        token_path: 生成的 token 保存路徑

    Returns:
        Credentials: Google Calendar API 憑證
    """
    creds = None

    # 檢查是否已有 token
    if os.path.exists(token_path):
        print(f"找到現有的 token: {token_path}")
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # 如果沒有有效的憑證，需要進行授權
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token 已過期，正在刷新...")
            creds.refresh(Request())
        else:
            print("\n開始 OAuth 授權流程...")
            print("瀏覽器將會自動打開，請使用你想要授權的 Google 帳號登入")
            print("並授予 Calendar 權限。\n")

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)

            print(f"\n✅ 授權成功！Token 已保存到: {token_path}")

        # 保存憑證供下次使用
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    else:
        print("✅ 憑證有效，無需重新授權")

    return creds


def test_calendar_api(creds):
    """測試 Calendar API 是否正常工作"""
    try:
        service = build('calendar', 'v3', credentials=creds)

        # 獲取主日曆資訊
        calendar = service.calendars().get(calendarId='primary').execute()

        print("\n✅ Calendar API 測試成功！")
        print(f"日曆名稱: {calendar.get('summary')}")
        print(f"時區: {calendar.get('timeZone')}")

        # 列出最近 5 個事件
        print("\n最近的日曆事件:")
        events_result = service.events().list(
            calendarId='primary',
            maxResults=5,
            singleEvents=True,
            orderBy='startTime',
            timeMin='2024-01-01T00:00:00Z'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            print("  沒有找到事件")
        else:
            for event in events[:5]:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"  - {event.get('summary', '無標題')}: {start}")

        return True
    except Exception as e:
        print(f"\n❌ Calendar API 測試失敗: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Google Calendar API 授權工具")
    print("=" * 60)

    # 確保 credentials 目錄存在
    os.makedirs('credentials', exist_ok=True)

    print("\n你想要授權哪個帳號？")
    print("1. 帳號 1（個人）- credentials_account1.json")
    print("2. 帳號 2（工作）- credentials_account2.json")
    print("3. 帳號 3（紐約大學）- credentials_account3.json")

    choice = input("\n請選擇 (1/2/3，預設 1): ").strip() or "1"

    credentials_map = {
        "1": ("credentials/credentials_account1.json", "credentials/calendar_token_account1.json", "個人"),
        "2": ("credentials/credentials_account2.json", "credentials/calendar_token_account2.json", "工作"),
        "3": ("credentials/credentials_account3.json", "credentials/calendar_token_account3.json", "紐約大學"),
    }

    if choice not in credentials_map:
        print("無效的選擇，使用預設帳號 1")
        choice = "1"

    credentials_path, token_path, label = credentials_map[choice]

    print(f"\n正在為【{label}】帳號授權 Calendar API...")
    print(f"Credentials: {credentials_path}")
    print(f"Token 將保存到: {token_path}")

    # 檢查 credentials 文件是否存在
    if not os.path.exists(credentials_path):
        print(f"\n❌ 錯誤: 找不到 credentials 文件: {credentials_path}")
        print("請確保你已經從 Google Cloud Console 下載了 OAuth 2.0 憑證")
        exit(1)

    # 進行授權
    creds = authenticate_calendar(credentials_path, token_path)

    # 測試 API
    print("\n" + "=" * 60)
    print("測試 Calendar API...")
    print("=" * 60)
    test_calendar_api(creds)

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"\n你的 Calendar token 已保存到: {token_path}")
    print("\n接下來需要將此 token 轉換為 base64 編碼：")
    print(f"  base64 -i {token_path}")
