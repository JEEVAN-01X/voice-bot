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
