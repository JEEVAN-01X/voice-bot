from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from twilio_handler import router as twilio_router

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
