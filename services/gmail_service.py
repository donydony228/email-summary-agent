"""
Gmail API 服務
處理 Gmail API 連接、郵件獲取等功能
"""

import os
import base64
import pickle
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API 權限範圍
# 如果修改這些範圍，需要刪除 token.json 重新授權
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # 讀取郵件
    # 'https://www.googleapis.com/auth/gmail.send',    # 發送郵件（如果需要）
]


def authenticate(credentials_path: str = 'credentials.json',
                token_path: str = 'token.json') -> Credentials:
    """
    Gmail API 認證

    Args:
        credentials_path: OAuth 2.0 憑證檔案路徑
        token_path: Token 儲存路徑

    Returns:
        Credentials: 認證憑證
    """
    creds = None

    # 檢查是否已有 token
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # 如果沒有有效憑證，進行授權流程
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token 過期但可以更新
            print("Token 已過期，正在更新...")
            creds.refresh(Request())
        else:
            # 需要重新授權
            print("首次使用或 Token 無效，開始授權流程...")
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"找不到憑證檔案: {credentials_path}\n"
                    f"請從 Google Cloud Console 下載 OAuth 2.0 憑證"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # 儲存 token 供下次使用
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
        print("授權成功！")

    return creds


def get_gmail_service(credentials_path: str = 'credentials.json',
                     token_path: str = 'token.json'):
    """
    建立 Gmail API 服務實例

    Args:
        credentials_path: OAuth 2.0 憑證檔案路徑
        token_path: Token 儲存路徑

    Returns:
        Gmail API 服務實例
    """
    creds = authenticate(credentials_path, token_path)

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'建立 Gmail 服務失敗: {error}')
        raise


def parse_time_range(time_range: str) -> datetime:
    """
    解析時間範圍字串，回傳開始時間

    Args:
        time_range: 時間範圍 ("24h", "7d", "30d" 等)

    Returns:
        datetime: 開始時間
    """
    now = datetime.now()

    if time_range.endswith('h'):
        # 小時
        hours = int(time_range[:-1])
        return now - timedelta(hours=hours)
    elif time_range.endswith('d'):
        # 天
        days = int(time_range[:-1])
        return now - timedelta(days=days)
    elif time_range.endswith('w'):
        # 週
        weeks = int(time_range[:-1])
        return now - timedelta(weeks=weeks)
    else:
        # 預設 24 小時
        return now - timedelta(hours=24)


def decode_message_part(part: Dict) -> str:
    """
    解碼郵件內容

    Args:
        part: 郵件部分

    Returns:
        str: 解碼後的內容
    """
    if 'data' in part['body']:
        data = part['body']['data']
        # Base64 解碼
        decoded_bytes = base64.urlsafe_b64decode(data)
        return decoded_bytes.decode('utf-8', errors='ignore')
    return ''


def get_message_body(payload: Dict) -> str:
    """
    提取郵件正文

    Args:
        payload: 郵件 payload

    Returns:
        str: 郵件正文
    """
    body = ''

    if 'parts' in payload:
        # 多部分郵件
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')

            # 優先提取純文字
            if mime_type == 'text/plain':
                body += decode_message_part(part)
            elif mime_type == 'text/html' and not body:
                # 如果沒有純文字，使用 HTML
                body += decode_message_part(part)
            elif 'parts' in part:
                # 遞迴處理嵌套部分
                body += get_message_body(part)
    else:
        # 單一部分郵件
        body = decode_message_part(payload)

    return body.strip()


def get_header_value(headers: List[Dict], name: str) -> str:
    """
    從郵件標頭中提取指定欄位的值

    Args:
        headers: 郵件標頭列表
        name: 欄位名稱

    Returns:
        str: 欄位值
    """
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ''


def fetch_emails(service,
                time_range: str = '24h',
                max_emails: int = 50,
                query: str = '') -> List[Dict]:
    """
    獲取郵件

    Args:
        service: Gmail API 服務實例
        time_range: 時間範圍 ("24h", "7d", "30d" 等)
        max_emails: 最多獲取郵件數
        query: Gmail 搜尋查詢 (例如: "is:unread", "from:example@gmail.com")

    Returns:
        List[Dict]: 郵件列表
    """
    try:
        # 計算時間範圍
        start_time = parse_time_range(time_range)
        after_timestamp = int(start_time.timestamp())

        # 建立搜尋查詢
        search_query = f'after:{after_timestamp}'
        if query:
            search_query += f' {query}'

        print(f"搜尋郵件: {search_query}")

        # 獲取郵件 ID 列表
        results = service.users().messages().list(
            userId='me',
            q=search_query,
            maxResults=max_emails
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            print('沒有找到郵件')
            return []

        print(f'找到 {len(messages)} 封郵件，開始獲取詳細內容...')

        # 獲取每封郵件的詳細內容
        emails = []
        for i, message in enumerate(messages, 1):
            try:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                # 提取郵件資訊
                headers = msg['payload']['headers']

                email_data = {
                    'id': msg['id'],
                    'thread_id': msg['threadId'],
                    'subject': get_header_value(headers, 'Subject'),
                    'from': get_header_value(headers, 'From'),
                    'to': get_header_value(headers, 'To'),
                    'date': get_header_value(headers, 'Date'),
                    'body': get_message_body(msg['payload']),
                    'snippet': msg.get('snippet', ''),
                    'labels': msg.get('labelIds', []),
                }

                emails.append(email_data)

                print(f'[{i}/{len(messages)}] {email_data["subject"][:50]}...')

            except HttpError as error:
                print(f'獲取郵件失敗 {message["id"]}: {error}')
                continue

        print(f'成功獲取 {len(emails)} 封郵件')
        return emails

    except HttpError as error:
        print(f'搜尋郵件失敗: {error}')
        return []


def fetch_emails_from_gmail(time_range: str = '24h',
                            max_emails: int = 50,
                            query: str = '',
                            credentials_path: str = 'credentials.json',
                            token_path: str = 'token.json') -> List[Dict]:
    """
    從 Gmail 獲取郵件（完整流程）

    Args:
        time_range: 時間範圍 ("24h", "7d", "30d" 等)
        max_emails: 最多獲取郵件數
        query: Gmail 搜尋查詢
        credentials_path: OAuth 2.0 憑證檔案路徑
        token_path: Token 儲存路徑

    Returns:
        List[Dict]: 郵件列表
    """
    # 從環境變數讀取路徑（如果有設定）
    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', credentials_path)
    token_path = os.getenv('GMAIL_TOKEN_PATH', token_path)

    # 建立服務
    service = get_gmail_service(credentials_path, token_path)

    # 獲取郵件
    emails = fetch_emails(service, time_range, max_emails, query)

    return emails


# 測試用主程式
if __name__ == '__main__':
    """
    測試 Gmail API

    使用方式:
    python services/gmail_service.py
    """
    print("=" * 60)
    print("Gmail API 測試")
    print("=" * 60)

    # 測試認證
    try:
        emails = fetch_emails_from_gmail(
            time_range='25h',  # 最近 25 小時
            max_emails=100,    # 最多 100 封
            query='',         # 不額外篩選
        )

        print("\n" + "=" * 60)
        print("郵件摘要:")
        print("=" * 60)

        for i, email in enumerate(emails, 1):
            print(f"\n[{i}] {email['subject']}")
            print(f"    寄件者: {email['from']}")
            print(f"    日期: {email['date']}")
            print(f"    預覽: {email['snippet'][:100]}...")

    except Exception as e:
        print(f"測試失敗: {e}")
