# Slack 通知服務
# 處理 Slack Webhook 通知發送
import os
import requests
from typing import Optional


def _convert_markdown_to_slack(markdown_text: str) -> str:
    """將標準 Markdown 轉換為 Slack mrkdwn 格式

    Args:
        markdown_text: 標準 Markdown 文字

    Returns:
        str: Slack mrkdwn 格式的文字
    """
    # Slack mrkdwn 格式規則：
    # - 標題 # 改為 *粗體*
    # - **粗體** 改為 *粗體*
    # - 列表保持不變

    lines = markdown_text.split('\n')
    converted_lines = []

    for line in lines:
        # 處理一級標題 (# )
        if line.startswith('# '):
            converted_lines.append(f"*{line[2:]}*")
        # 處理二級標題 (## )
        elif line.startswith('## '):
            converted_lines.append(f"*{line[3:]}*")
        # 處理三級標題 (### )
        elif line.startswith('### '):
            converted_lines.append(f"*{line[4:]}*")
        else:
            # 處理行內 **粗體** 轉換為 *粗體*
            converted_line = line.replace('**', '*')
            converted_lines.append(converted_line)

    return '\n'.join(converted_lines)

def send_slack_notification(report: str) -> bool:
    """發送 Slack 通知

    Args:
        report: Markdown 格式的報告內容

    Returns:
        bool: 發送成功返回 True，失敗返回 False
    """
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        return False

    # 將 Markdown 轉換為 Slack mrkdwn 格式
    slack_text = _convert_markdown_to_slack(report)

    # 構建 Slack 訊息
    payload = {
        "text": slack_text
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )

        # Slack Webhook 成功時返回 200
        return response.status_code == 200

    except requests.exceptions.RequestException:
        return False

def send_event_confirmation_request(events: list[dict]) -> str:
    """發送事件確認請求（Slack 互動訊息）"""
    from slack_sdk import WebClient

    client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
    channel_id = os.getenv('SLACK_CHANNEL_ID')

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "檢測到行程/事件，請確認是否加入日曆"
            }
        },
        {"type": "divider"}
    ]

    for event in events:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{event['title']}*\n時間: {event['start_time']} - {event['end_time']}\n地點: {event.get('location', '無')}"
                }
            },
            {
                "type": "actions",
                "block_id": f"event_{event['id']}",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "確認加入"},
                        "style": "primary",
                        "value": event['id'],
                        "action_id": "confirm_event"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "跳過"},
                        "style": "danger",
                        "value": event['id'],
                        "action_id": "skip_event"
                    }
                ]
            }
        ])

    response = client.chat_postMessage(
        channel=channel_id,
        blocks=blocks
    )

    return response['ts']  # message timestamp