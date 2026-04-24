from dotenv import load_dotenv
import os

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
