import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# -------------------------
# Load environment
# -------------------------
load_dotenv()

LINE_API_URL = "https://api.line.me/v2/bot/message/push"
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

app = FastAPI(title="LINE Messaging API Backend")

# -------------------------
# Pydantic Model
# -------------------------
class LineMessageRequest(BaseModel):
    to: str        # userId หรือ groupId
    message: str   # ข้อความที่ต้องการส่ง

# -------------------------
# LINE Send Function
# -------------------------
def send_line_message(to: str, message: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }

    payload = {
        "to": to,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    response = requests.post(
        LINE_API_URL,
        headers=headers,
        json=payload,
        timeout=10
    )

    return response.json()

# -------------------------
# FastAPI Endpoint
# -------------------------
@app.post("/send-line")
def send_line(data: LineMessageRequest):
    result = send_line_message(
        to=data.to,
        message=data.message
    )

    return {
        "status": "success",
        "line_response": result
    }
