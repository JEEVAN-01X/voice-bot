from typing import Dict
from order_processor import Order
import uuid

# In-memory call state store
active_calls: Dict[str, dict] = {}
pending_orders: Dict[str, dict] = {}

def create_call_state(call_sid: str, phone: str, lang: str):
    active_calls[call_sid] = {
        'phone': phone,
        'lang': lang,
        'retries': 0,
        'status': 'greeting'
    }

def get_call_state(call_sid: str) -> dict:
    return active_calls.get(call_sid, {})

def increment_retry(call_sid: str):
    if call_sid in active_calls:
        active_calls[call_sid]['retries'] += 1

def end_call(call_sid: str):
    if call_sid in active_calls:
        del active_calls[call_sid]

def store_pending_order(order_data: dict) -> str:
    order_id = str(uuid.uuid4())[:8]
    pending_orders[order_id] = order_data
    return order_id

def get_pending_order(order_id: str) -> dict:
    return pending_orders.get(order_id, {})

def confirm_order(order_id: str):
    if order_id in pending_orders:
        order = pending_orders.pop(order_id)
        return order
    return None
