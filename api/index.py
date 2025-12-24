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
        userid_line = event.get("source", {}).get("userId")
        message = event.get("message", {}).get("text", "").strip().lower()

        if not userid_line or not message:
            continue

        # -------------------------
        # CANCEL
        # -------------------------
        if message == "cancel":
            doctor_collection.update_many(
                {"pending_line_id": userid_line},
                {"$unset": {"pending_line_id": "", "pending_at": ""}}
            )

            send_line_message(
                userid_line,
                "🛑 ยกเลิกการลงทะเบียนแล้ว\nสามารถกรอกรหัสแพทย์ใหม่ได้"
            )
            continue

        # -------------------------
        # CONFIRM
        # -------------------------
        if message == "confirm":
            doctor = doctor_collection.find_one({
                "pending_line_id": userid_line
            })

            if not doctor:
                send_line_message(
                    userid_line,
                    "⚠️ ไม่พบรายการที่ต้องยืนยัน\nกรุณากรอกรหัสแพทย์ใหม่"
                )
                continue

            # ผูก LINE จริง
            doctor_collection.update_one(
                {"_id": doctor["_id"]},
                {
                    "$set": {"line_id": userid_line},
                    "$unset": {"pending_line_id": "", "pending_at": ""}
                }
            )

            send_line_message(
                userid_line,
                (
                    "✅ ลงทะเบียน LINE สำเร็จ\n\n"
                    f"ชื่อ: {doctor.get('thai_full_name','-')}\n"
                    f"แผนก: {doctor.get('department','-')}"
                )
            )
            continue

            # -------------------------
            # ถ้า LINE นี้อยู่ระหว่าง pending
            # -------------------------
            pending = doctor_collection.find_one({
                "pending_line_id": userid_line
            })
            if pending:
                send_line_message(
                    userid_line,
                    "ℹ️ กรุณายืนยันข้อมูลก่อน\nพิมพ์ confirm หรือ cancel"
                )
                continue

            # -------------------------
            # ถ้าผูกเสร็จแล้วจริง ๆ
            # -------------------------
            already = doctor_collection.find_one({
                "line_id": userid_line
            })
            if already:
                send_line_message(
                    userid_line,
                    "⚠️ LINE นี้ถูกผูกกับแพทย์แล้ว\nพิมพ์ cancel หากต้องการแก้ไข"
                )
                continue

        # -------------------------
        # STEP 1: กรอก care_provider_code
        # -------------------------
        doctor = doctor_collection.find_one({
            "care_provider_code": message
        })

        if not doctor:
            send_line_message(
                userid_line,
                "❌ ไม่พบรหัสแพทย์\nกรุณากรอกใหม่ หรือพิมพ์ cancel"
            )
            continue

        # บันทึก pending
        doctor_collection.update_one(
            {"_id": doctor["_id"]},
            {
                "$set": {
                    "pending_line_id": userid_line
                }
            }
        )

        send_line_message(
            userid_line,
            (
                "🔍 กรุณายืนยันตัวตน\n\n"
                f"ชื่อ: {doctor.get('thai_full_name','-')}\n"
                f"แผนก: {doctor.get('department','-')}\n\n"
                "พิมพ์ confirm เพื่อยืนยัน\n"
                "หรือพิมพ์ cancel เพื่อยกเลิก"
            )
        )

    return {"status": "ok"}
