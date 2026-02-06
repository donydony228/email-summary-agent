"""
FastAPI 服務器 - 處理 Slack 互動回調
優化用於 Render 免費方案（處理 cold start）
"""
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import hmac
import hashlib
import json
from urllib.parse import parse_qs

# ⚠️ 重要：在導入 graph 之前先初始化 credentials
from init_credentials import init_credentials
init_credentials()

from agent.graph import graph  # 導入 compiled graph

app = FastAPI()

# Slack 簽名驗證
def verify_slack_signature(timestamp: str, body: str, signature: str) -> bool:
    """驗證請求來自 Slack"""
    signing_secret = os.getenv('SLACK_SIGNING_SECRET')
    if not signing_secret:
        print("警告: SLACK_SIGNING_SECRET 未設定，跳過驗證")
        return True

    signing_secret = signing_secret.encode()
    sig_basestring = f'v0:{timestamp}:{body}'.encode()
    expected_signature = 'v0=' + hmac.new(
        signing_secret, sig_basestring, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def process_slack_interaction_background(action_id: str, event_id: str):
    """後台處理 Slack 互動（避免超時）"""
    try:
        thread_id = {"configurable": {"thread_id": "email-summary-run"}}

        if action_id == "confirm_event":
            # 用戶確認，更新狀態並恢復工作流
            print(f"用戶確認事件: {event_id}")
            graph.update_state(
                thread_id,
                {"confirmed_events": [event_id]},
                as_node="request_confirmation"
            )
        else:
            # 用戶跳過
            print(f"用戶跳過事件: {event_id}")
            graph.update_state(
                thread_id,
                {"confirmed_events": []},
                as_node="request_confirmation"
            )

        # 恢復執行工作流
        for event in graph.stream(None, thread_id, stream_mode="values"):
            print(f"工作流執行中: {list(event.keys())}")

        print("工作流恢復完成")
    except Exception as e:
        print(f"處理 Slack 互動時出錯: {e}")
        import traceback
        traceback.print_exc()

@app.post("/slack/interactive")
async def handle_slack_interaction(request: Request, background_tasks: BackgroundTasks):
    """
    處理 Slack 按鈕點擊回調

    重要：立即回應 200 避免 Slack 超時（3秒限制）
    實際處理放到後台執行
    """
    # 讀取 request body
    body = await request.body()
    body_str = body.decode()
    headers = request.headers

    # 處理 Slack URL 驗證（首次設置 Interactivity URL 時）
    try:
        data = json.loads(body_str)
        if data.get('type') == 'url_verification':
            return JSONResponse({"challenge": data.get('challenge')})
    except:
        pass  # 不是 JSON 格式，繼續處理 form-encoded payload

    # 驗證簽名
    if not verify_slack_signature(
        headers.get('x-slack-request-timestamp', ''),
        body_str,
        headers.get('x-slack-signature', '')
    ):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)

    # 解析 payload
    try:
        payload = json.loads(parse_qs(body_str)['payload'][0])
    except Exception as e:
        return JSONResponse({"error": f"Invalid payload: {e}"}, status_code=400)

    action = payload['actions'][0]
    action_id = action['action_id']  # "confirm_event" 或 "skip_event"
    event_id = action['value']  # event ID

    # **立即回應** Slack（避免超時）
    response_text = f"收到！正在{'確認' if action_id == 'confirm_event' else '跳過'}事件..."

    # 將實際處理放到後台
    background_tasks.add_task(
        process_slack_interaction_background,
        action_id,
        event_id
    )

    # 3 秒內回應 Slack
    return JSONResponse({
        "response_type": "in_channel",
        "text": response_text,
        "replace_original": False  # 保留原訊息
    })

@app.post("/webhook/email-summary")
async def trigger_email_summary(background_tasks: BackgroundTasks):
    """
    觸發 Email Summary 工作流
    用於 GitHub Actions 或其他定時任務調用
    """
    thread_id = {"configurable": {"thread_id": "email-summary-run"}}

    def run_workflow():
        try:
            # 執行完整工作流
            for event in graph.stream(
                {"time_range": "24h", "max_emails": 20},
                thread_id,
                stream_mode="values"
            ):
                print(f"工作流執行中: {list(event.keys())}")
            print("Email Summary 完成")
        except Exception as e:
            print(f"執行工作流時出錯: {e}")
            import traceback
            traceback.print_exc()

    # 放到後台執行
    background_tasks.add_task(run_workflow)

    return {"status": "triggered", "message": "Email summary workflow started"}


@app.get("/")
async def root():
    """健康檢查端點"""
    return {
        "status": "ok",
        "service": "Email Summary Agent API",
        "version": "1.0"
    }


@app.get("/health")
async def health():
    """Render 健康檢查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
