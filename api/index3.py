import os
import requests
from fastapi import FastAPI
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
    allow_origins=["*"],   # ปรับเป็น domain จริงตอน production
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

    response = requests.post(
        LINE_API_URL,
        headers=headers,
        json=payload,
        timeout=10
    )

    return response.json()

# -------------------------
# Endpoint
# -------------------------
@app.post("/send-line")
def send_line(data: LineMessageRequest):
    result = send_line_message(data.to, data.message)
    return {"status": "success", "line_response": result}
