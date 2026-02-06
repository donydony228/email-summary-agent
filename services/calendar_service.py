"""
Google Calendar API 服務
處理 Google Calendar 事件創建
"""
import os
import pickle
import base64
import json
import tempfile
from datetime import datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Calendar API 權限範圍
SCOPES = ['https://www.googleapis.com/auth/calendar']


def authenticate_calendar(
    credentials_path: str = 'credentials/calendar_credentials.json',
    token_path: str = 'credentials/calendar_token.json',
    token_base64_env: str = None
) -> Credentials:
    """
    Google Calendar API 認證

    優先從環境變量讀取 base64 編碼的 token
    如果環境變量不存在，則從文件讀取

    Args:
        credentials_path: OAuth 2.0 憑證文件路徑
        token_path: Token 儲存路徑
        token_base64_env: Token base64 環境變量名稱

    Returns:
        Credentials: Calendar API 憑證
    """
    creds = None

    # 優先從環境變量讀取 token
    if token_base64_env and os.getenv(token_base64_env):
        try:
            print(f"從環境變量 {token_base64_env} 讀取 Calendar token...")
            token_data = base64.b64decode(os.getenv(token_base64_env))
            creds = pickle.loads(token_data)
            print("✓ Calendar token 從環境變量加載成功")
        except Exception as e:
            print(f"從環境變量讀取 Calendar token 失敗: {e}")
            creds = None
    # 否則從文件讀取
    elif os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        print(f"✓ Calendar token 從文件 {token_path} 加載成功")

    # 如果沒有有效憑證，進行授權流程
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Calendar token 已過期，正在更新...")
            creds.refresh(Request())
        else:
            # 需要重新授權
            print("Calendar 需要重新授權...")
            if os.path.exists(credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("✓ Calendar 授權成功")
            else:
                raise FileNotFoundError(
                    f"找不到憑證檔案: {credentials_path}\n"
                    f"也沒有設置環境變量: {token_base64_env}\n"
                    f"請先運行 init_calendar_auto.py 獲取 Calendar API 授權"
                )

        # 儲存 token 供下次使用（僅當使用文件模式時）
        if not token_base64_env and token_path:
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            print(f"Calendar token 已保存到 {token_path}")

    return creds


def get_calendar_service(
    credentials_path: str = 'credentials/calendar_credentials.json',
    token_path: str = 'credentials/calendar_token.json',
    token_base64_env: str = None
):
    """
    建立 Google Calendar API 服務實例

    Args:
        credentials_path: OAuth 2.0 憑證文件路徑
        token_path: Token 儲存路徑
        token_base64_env: Token base64 環境變量名稱

    Returns:
        Google Calendar API 服務實例
    """
    creds = authenticate_calendar(credentials_path, token_path, token_base64_env)

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'建立 Calendar 服務失敗: {error}')
        raise


def create_calendar_event(event_data: dict) -> str:
    """
    創建 Google Calendar 事件

    Args:
        event_data: {
            'id': str (事件 ID),
            'title': str (事件標題),
            'start_time': datetime (開始時間),
            'end_time': datetime (結束時間),
            'location': str (地點，可選),
            'description': str (描述，可選)
        }

    Returns:
        str: 創建的 Calendar 事件 ID
    """
    # 優先從環境變量讀取 token
    token_base64_env = os.getenv('GOOGLE_CALENDAR_TOKEN_BASE64')
    service = get_calendar_service(
        token_base64_env='GOOGLE_CALENDAR_TOKEN_BASE64' if token_base64_env else None
    )

    # 格式化事件
    event = {
        'summary': event_data.get('title', '未命名事件'),
        'location': event_data.get('location', ''),
        'description': event_data.get('description', ''),
        'start': {
            'dateTime': event_data['start_time'].isoformat() if isinstance(event_data['start_time'], datetime) else event_data['start_time'],
            'timeZone': 'Asia/Taipei',
        },
        'end': {
            'dateTime': event_data['end_time'].isoformat() if isinstance(event_data['end_time'], datetime) else event_data['end_time'],
            'timeZone': 'Asia/Taipei',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # 1天前郵件提醒
                {'method': 'popup', 'minutes': 30},  # 30分鐘前彈窗提醒
            ],
        },
    }

    try:
        # 創建事件
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        print(f"✓ Calendar 事件創建成功: {event_data.get('title')}")
        print(f"  事件 ID: {created_event['id']}")
        print(f"  時間: {event_data['start_time']} - {event_data['end_time']}")

        return created_event['id']

    except HttpError as error:
        print(f'創建 Calendar 事件失敗: {error}')
        raise


def list_upcoming_events(max_results: int = 10) -> list:
    """
    列出即將到來的日曆事件

    Args:
        max_results: 最多返回事件數

    Returns:
        list: 事件列表
    """
    token_base64_env = os.getenv('GOOGLE_CALENDAR_TOKEN_BASE64')
    service = get_calendar_service(
        token_base64_env='GOOGLE_CALENDAR_TOKEN_BASE64' if token_base64_env else None
    )

    try:
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' 表示 UTC 時間
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return events

    except HttpError as error:
        print(f'獲取 Calendar 事件失敗: {error}')
        raise
