"""
Google Calendar API 授權腳本（自動版）
直接為帳號 1（個人）授權
"""
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Calendar API 需要的權限範圍
SCOPES = ['https://www.googleapis.com/auth/calendar']

credentials_path = 'credentials/credentials_account1.json'
token_path = 'credentials/calendar_token.json'

print("=" * 60)
print("Google Calendar API 授權工具（帳號 1 - 個人）")
print("=" * 60)

# 確保 credentials 目錄存在
os.makedirs('credentials', exist_ok=True)

# 檢查 credentials 文件是否存在
if not os.path.exists(credentials_path):
    print(f"\n❌ 錯誤: 找不到 credentials 文件: {credentials_path}")
    print("請確保你已經有 Gmail API 的 OAuth 憑證")
    exit(1)

creds = None

# 檢查是否已有 token
if os.path.exists(token_path):
    print(f"\n找到現有的 token: {token_path}")
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)

# 如果沒有有效的憑證，需要進行授權
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        print("\nToken 已過期，正在刷新...")
        creds.refresh(Request())
    else:
        print("\n開始 OAuth 授權流程...")
        print("瀏覽器將會自動打開，請：")
        print("1. 使用你的【個人】Google 帳號登入")
        print("2. 授予 Calendar 權限")
        print("3. 完成後返回此終端\n")

        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path, SCOPES
        )
        creds = flow.run_local_server(port=0)

        print(f"\n✅ 授權成功！Token 已保存到: {token_path}")

    # 保存憑證
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)
else:
    print("\n✅ 憑證有效，無需重新授權")

# 測試 Calendar API
print("\n" + "=" * 60)
print("測試 Calendar API...")
print("=" * 60)

try:
    service = build('calendar', 'v3', credentials=creds)
    calendar = service.calendars().get(calendarId='primary').execute()

    print("\n✅ Calendar API 測試成功！")
    print(f"日曆名稱: {calendar.get('summary')}")
    print(f"時區: {calendar.get('timeZone')}")
except Exception as e:
    print(f"\n❌ Calendar API 測試失敗: {e}")
    exit(1)

# 生成 base64 編碼
print("\n" + "=" * 60)
print("生成 Base64 編碼...")
print("=" * 60)

import base64

with open(token_path, 'rb') as f:
    token_base64 = base64.b64encode(f.read()).decode()

print("\n將以下變量添加到你的 .env 文件：")
print("\n" + "=" * 60)
print(f"GOOGLE_CALENDAR_TOKEN_BASE64={token_base64}")
print("=" * 60)

# 保存到文件
with open('credentials/calendar_token_base64.txt', 'w') as f:
    f.write(token_base64)

print(f"\n✅ Base64 編碼已保存到: credentials/calendar_token_base64.txt")
print("\n完成！你現在可以使用 Calendar API 了。")
