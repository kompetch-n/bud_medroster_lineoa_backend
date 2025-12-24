import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

LINE_API_URL = "https://api.line.me/v2/bot/message/push"
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "doctor_roster_system"
COLLECTION_NAME = "doctors"

# -------------------------
# MongoDB
# -------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
doctor_collection = db[COLLECTION_NAME]

# -------------------------
# FastAPI
# -------------------------
app = FastAPI(title="BUD LINE OA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# Webhook
# -------------------------
@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}

    for event in body.get("events", []):
        source = event.get("source", {})
        userid_line = source.get("userId")
        message = event.get("message", {}).get("text", "").strip()

        if not userid_line or not message:
            continue

        # 🔍 ค้นแพทย์ด้วย care_provider_code
        doctor = doctor_collection.find_one({
            "care_provider_code": message
        })

        # ❌ ไม่พบแพทย์
        if not doctor:
            send_line_message(
                to=userid_line,
                message=(
                    "❌ ไม่พบรหัสแพทย์ในระบบ\n\n"
                    "กรุณาตรวจสอบ care_provider_code\n"
                    "หรือ ติดต่อ Admin"
                )
            )
            continue

        # ✅ พบแพทย์ → update line_id
        doctor_collection.update_one(
            {"_id": doctor["_id"]},
            {"$set": {"line_id": userid_line}}
        )

        send_line_message(
            to=userid_line,
            message=(
                "✅ ลงทะเบียน LINE สำเร็จ\n\n"
                f"ชื่อ: {doctor.get('thai_full_name', '-')}\n"
                f"แผนก: {doctor.get('department', '-')}"
            )
        )

    return {"status": "ok"}
