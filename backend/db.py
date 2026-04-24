import firebase_admin
from firebase_admin import credentials, firestore
import os

# Only initialize if not already initialized
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_CRED_PATH", "./firebase-creds.json")
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print("WARNING: Firebase credentials not found. Orders won't be saved.")

def get_db():
    try:
        return firestore.client()
    except:
        return None

async def save_order(order_id: str, order_data: dict) -> str:
    db = get_db()
    if not db:
        print(f"MOCK SAVE: {order_id} -> {order_data}")
        return order_id
    doc_ref = db.collection('orders').document(order_id)
    doc_ref.set({
        **order_data,
        'status': 'confirmed',
        'confirmed_at': firestore.SERVER_TIMESTAMP,
    })
    return order_id

async def get_orders(limit: int = 50) -> list:
    db = get_db()
    if not db:
        return []
    docs = db.collection('orders')\
        .order_by('confirmed_at', direction=firestore.Query.DESCENDING)\
        .limit(limit).stream()
    return [{'id': d.id, **d.to_dict()} for d in docs]
