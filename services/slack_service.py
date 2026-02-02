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
