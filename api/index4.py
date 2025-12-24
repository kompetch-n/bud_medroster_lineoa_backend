import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

LINE_API_URL = "https://api.line.me/v2/bot/message/push"
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

app = FastAPI(title="LINE Messaging API Backend")

# -------------------------
# CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Model
# -------------------------
class LineMessageRequest(BaseModel):
    to: str
    message: str

# -------------------------
# Send LINE
# -------------------------
def send_line_message(to: str, message: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }

    payload = {
        "to": to,
        "messages": [{"type": "text", "text": message}]
    }

    requests.post(LINE_API_URL, headers=headers, json=payload, timeout=10)

# -------------------------
# Webhook (รองรับ Verify + รับข้อความจริง)
# -------------------------
@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        # 👉 LINE Verify จะเข้ามาตรงนี้
        return {"status": "ok"}

    for event in body.get("events", []):
        source = event.get("source", {})
        userid_line = source.get("userId")
        message = event.get("message", {}).get("text", "")

        if userid_line:
            print("📌 userid_line:", userid_line)
            print("💬 message:", message)

            send_line_message(
                to=userid_line,
                message=f"รับ userId แล้ว ✅\n{userid_line}"
            )

    return {"status": "ok"}

# -------------------------
# Manual send
# -------------------------
@app.post("/send-line")
def send_line(data: LineMessageRequest):
    send_line_message(data.to, data.message)
    return {"status": "success"}
