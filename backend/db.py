import json
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def _get_db():
    if not firebase_admin._apps:
        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if cred_json:
            import tempfile
            cred_dict = json.loads(cred_json)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(cred_dict, f)
                tmp_path = f.name
            cred = credentials.Certificate(tmp_path)
        else:
            cred = credentials.Certificate("firebase-creds.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

def init_db():
    pass  # Firestore creates collections automatically

def save_order(order_id: str, order_data: dict):
    db = _get_db()
    db.collection("orders").document(order_id).set({
        "id": order_id,
        "customer_phone": order_data.get("customer_phone", "unknown"),
        "language": order_data.get("language", "en-IN"),
        "items": order_data.get("items", []),
        "address": order_data.get("address", ""),
        "status": "confirmed",
        "raw_transcript": order_data.get("raw_transcript", ""),
        "confirmed_at": datetime.utcnow().isoformat()
    })

def get_orders(limit=50):
    db = _get_db()
    docs = db.collection("orders").order_by(
        "confirmed_at", direction=firestore.Query.DESCENDING
    ).limit(limit).stream()
    return [doc.to_dict() for doc in docs]
