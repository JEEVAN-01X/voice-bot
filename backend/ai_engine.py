from groq import Groq
import json
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are Priya, a warm and smart order assistant for Automaton AI Infosystem.

YOUR JOB:
- Have a natural conversation to collect their order
- Extract items, quantities, and delivery address
- If customer did not mention address, ALWAYS ask for it before setting ready_to_confirm=true
- If they ask questions or want suggestions, answer helpfully then bring them back to ordering
- ONLY set "ready_to_confirm": true when you have at least one clear item WITH quantity AND a delivery address
- If address is missing, ask for it naturally before confirming

RULES:
1. Detect language automatically — English, Hindi, Kannada, or Marathi
2. LANGUAGE LOCK RULE — this is critical:
   - Detect the language from the FIRST message only
   - Once detected, NEVER change the language for the rest of the conversation
   - Hindi and Marathi both use Devanagari script — if customer started in Hindi, stay Hindi
   - Do NOT switch to Marathi just because the address sounds Marathi
   - The language_detected field must stay the same across all turns
3. If items are unclear or missing, ask a specific follow-up question
4. If they want suggestions, give 2-3 options then ask what they want
5. Never confirm an empty order — always ask what they need first
6. Keep responses short — max 2 sentences

Return ONLY valid JSON:
{
  "items": ["item1 qty", "item2 qty"],
  "address": "delivery address or null",
  "confirm_message": "your reply to the customer",
  "language_detected": "en-IN or hi-IN or kn-IN or mr-IN",
  "ready_to_confirm": true or false
}

ready_to_confirm must be TRUE only when items list is non-empty and customer is ready.
ready_to_confirm must be FALSE when items=[], customer is asking questions, or order is unclear.

confirm_message rules:
- If ready_to_confirm=true: restate items clearly, end with "say yes to confirm"
- If ready_to_confirm=false: ask the right follow-up question naturally
- Always start with "Hmm..." or "Okay..." or "Bilkul!" or "Sari!" or "Thik aahe!"
- Max 2 sentences
"""

pending_orders = {}

POSITIVE_WORDS = ['yes', 'yeah', 'yea', 'yup', 'haan', 'haan ji', 'han', 'hann', 'ha', 'ho', 'hoo', 'sari', 'houdu', 'sahi hai', 'sahi', 'theek hai', 'thik hai', 'bilkul sahi', 'correct hai', 'ho jaaye', 'kar do', 'confirm', 'done',
                  'correct', 'theek hai', 'theek', 'bilkul', 'hoya', 'thik',
                  'baro', 'okay', 'ok', 'sure', 'yep', 'ha', 'han', 'sounds good', 'confirmed', 'right', 'perfect', 'good']
NEGATIVE_WORDS = ['no', 'nahi', 'nako', 'illa', 'beda', 'wrong', 'galat',
                  'cancel', 'repeat', 'dobara', 'chukiche', 'punha', 'change']

def detect_intent(speech_text: str) -> str:
    text = speech_text.lower().strip()
    # Check positive words — also check if any word IS a positive word (partial match)
    for word in POSITIVE_WORDS:
        if word in text:
            return 'confirm'
    for word in NEGATIVE_WORDS:
        if word in text:
            return 'deny'
    # Fallback — if short response (1-3 words), treat as confirm
    # People say things like "haan", "ji", "theek", "done", "ho"
    words = text.split()
    if len(words) <= 3:
        return 'confirm'
    return 'unclear'

async def process_order(speech_text: str, lang: str = 'auto', order_id: str = None) -> dict:
    try:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

        if order_id and order_id in pending_orders:
            prev = pending_orders[order_id]
            for turn in prev.get('history', []):
                messages.append(turn)

        messages.append({'role': 'user', 'content': f'Customer said: {speech_text}'})

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            max_tokens=400,
            messages=messages,
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1].lstrip('json').strip()

        data = json.loads(raw)

        if not order_id or order_id not in pending_orders:
            order_id = str(uuid.uuid4())[:8]

        detected_lang = data.get('language_detected', 'en-IN')
        items = data.get('items', [])
        ready = data.get('ready_to_confirm', False) and len(items) > 0

        prev_data = pending_orders.get(order_id, {})
        history = prev_data.get('history', [])
        history.append({'role': 'user', 'content': f'Customer said: {speech_text}'})
        history.append({'role': 'assistant', 'content': json.dumps(data)})

        pending_orders[order_id] = {
            'items': items,
            'address': data.get('address'),
            'language': detected_lang,
            'raw_transcript': speech_text,
            'last_confirm_message': data.get('confirm_message', ''),
            'status': 'pending',
            'retries': prev_data.get('retries', 0),
            'ready_to_confirm': ready,
            'history': history,
            'customer_phone': prev_data.get('customer_phone', 'unknown'),
        }

        return {
            'id': order_id,
            'confirm_message': data['confirm_message'],
            'items': items,
            'language': detected_lang,
            'ready_to_confirm': ready,
        }

    except json.JSONDecodeError:
        order_id = order_id or str(uuid.uuid4())[:8]
        return {'id': order_id, 'confirm_message': _fallback(lang), 'items': [], 'language': lang, 'ready_to_confirm': False}
    except Exception as e:
        print(f'[ai_engine ERROR] {e}')
        order_id = order_id or str(uuid.uuid4())[:8]
        return {'id': order_id, 'confirm_message': _fallback(lang), 'items': [], 'language': lang, 'ready_to_confirm': False}

def increment_retries(order_id: str) -> int:
    if order_id in pending_orders:
        pending_orders[order_id]['retries'] += 1
        return pending_orders[order_id]['retries']
    return 0

def can_retry(order_id: str, max_retries: int = 3) -> bool:
    return pending_orders.get(order_id, {}).get('retries', 999) < max_retries

def confirm_order(order_id: str) -> dict:
    if order_id in pending_orders:
        pending_orders[order_id]['status'] = 'confirmed'
        return pending_orders[order_id]
    return {}

def _fallback(lang: str) -> str:
    fallbacks = {
        'en-IN': "Sorry, I didn't catch that. Could you tell me what you'd like to order?",
        'hi-IN': "Maafi kijiye, dobara bolein aap kya order karna chahte hain?",
        'kn-IN': "Kshamisi, dayavittu nimma order heliri.",
        'mr-IN': "Maafi kara, aapla order punha sanga.",
    }
    return fallbacks.get(lang, fallbacks['en-IN'])
