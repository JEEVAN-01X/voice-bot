from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
from twilio_handler import router as twilio_router
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Voice Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(twilio_router, prefix="/twilio")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/make-call")
async def make_call(to: str):
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    call = client.calls.create(
        to=to,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url=f"{os.getenv('BASE_URL')}/twilio/call-start"
    )
    return {"call_sid": call.sid, "status": call.status}

from db import get_orders
from fastapi.responses import FileResponse

@app.get("/orders")
def list_orders():
    return get_orders(limit=50)

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(os.path.dirname(__file__), "dashboard.html"))

import asyncio
from twilio.rest import Client as TwilioClient

@app.post("/make-calls-bulk")
async def make_calls_bulk(numbers: list[str]):
    client = TwilioClient(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    results = []
    for number in numbers:
        try:
            call = client.calls.create(
                to=number,
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                url=f"{os.getenv('BASE_URL')}/twilio/call-start"
            )
            results.append({"number": number, "status": "queued", "sid": call.sid})
            await asyncio.sleep(1)  # 1 sec between calls — avoids Twilio rate limit
        except Exception as e:
            results.append({"number": number, "status": "failed", "error": str(e)})
    return results
