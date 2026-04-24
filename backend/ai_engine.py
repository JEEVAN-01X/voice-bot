from groq import Groq
import json
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are Priya, a warm and efficient order assistant for Automaton AI Infosystem.

You handle incoming orders from shop owners, distributors, and business customers who call in.
These are real business people — treat them with respect, like a trusted colleague.

RULES:
1. Automatically detect the language the customer is speaking — English, Hindi, Kannada, or Marathi.
2. Always respond in the EXACT same language the customer used. Never mix languages.
3. Extract: items ordered, quantities, and delivery address if mentioned.
4. Generate a warm, natural confirmation — not robotic. Sound like a real person.
5. Return ONLY valid JSON, nothing else.

Return this exact format:
{
  "items": ["item1 qty", "item2 qty"],
  "address": "delivery address or null",
  "confirm_message": "natural confirmation in customer's language",
  "language_detected": "en-IN or hi-IN or kn-IN or mr-IN"
}

Confirmation message rules:
- ALWAYS start with "Hmm..." or "Okay..." as the very first word — this buys processing time / "Bilkul!" / "Sari!" / "Thik aahe!"
- Restate items clearly but conversationally
- End with asking them to say Yes to confirm
- Keep it under 3 sentences — these are busy business owners

Examples of GOOD confirm messages:
- English: "Got it! So that's 50 kg rice and 20 kg sugar delivered to Koramangala. Does that sound right? Just say yes to confirm."
- Hindi: "Bilkul! 50 kilo chawal aur 20 kilo cheeni, Koramangala delivery. Sahi hai? Haan bolein confirm karne ke liye."
- Kannada: "Sari! 50 kilo akki mattu 20 kilo sakkare, Koramangala delivery. Sari idheya? Confirm maaḍalu houdu heli."
- Marathi: "Thik aahe! 50 kilo tandul aani 20 kilo saakhar, Koramangala delivery. Baro aahe ka? Confirm karayla ho mhana."

NEVER say: "You have ordered", "Order confirmed", "Press", "Please state"
"""

pending_orders = {}

POSITIVE_WORDS = ['yes', 'yeah', 'yea', 'yup', 'haan', 'haan ji', 'ho', 'hoo', 'sari', 'houdu',
                  'correct', 'theek hai', 'theek', 'bilkul', 'hoya', 'thik',
                  'baro', 'okay', 'ok', 'sure', 'yep', 'ha', 'han', 'sounds good', 'confirmed', 'correct', 'right', 'perfect', 'good']
NEGATIVE_WORDS = ['no', 'nahi', 'nako', 'illa', 'beda', 'wrong', 'galat',
                  'cancel', 'repeat', 'dobara', 'chukiche', 'punha', 'change']

def detect_intent(speech_text: str) -> str:
    text = speech_text.lower().strip()
    if any(word in text for word in POSITIVE_WORDS):
        return 'confirm'
    elif any(word in text for word in NEGATIVE_WORDS):
        return 'deny'
    return 'unclear'

async def process_order(speech_text: str, lang: str = 'auto', order_id: str = None) -> dict:
    try:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

        if order_id and order_id in pending_orders:
            prev = pending_orders[order_id]
            messages.append({
                'role': 'user',
                'content': f'Customer said: {prev["raw_transcript"]}'
            })
            messages.append({
                'role': 'assistant',
                'content': json.dumps({
                    'items': prev['items'],
                    'address': prev['address'],
                    'confirm_message': prev.get('last_confirm_message', ''),
                    'language_detected': prev.get('language', 'en-IN')
                }, ensure_ascii=False)
            })
            messages.append({
                'role': 'user',
                'content': f'Customer wants to change something. They said: {speech_text}. Re-extract the order and confirm again.'
            })
        else:
            messages.append({
                'role': 'user',
                'content': f'Customer said: {speech_text}\n\nIf this is NOT an order (e.g. questions, greetings, small talk), set items=[] and set confirm_message to a natural conversational reply staying in character as Priya. Still return valid JSON.'
            })

        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            max_tokens=300,
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

        pending_orders[order_id] = {
            'items': data.get('items', []),
            'address': data.get('address'),
            'language': detected_lang,
            'raw_transcript': speech_text,
            'last_confirm_message': data.get('confirm_message', ''),
            'status': 'pending',
            'retries': pending_orders.get(order_id, {}).get('retries', 0),
        }

        return {
            'id': order_id,
            'confirm_message': data['confirm_message'],
            'items': data.get('items', []),
            'language': detected_lang,
        }

    except json.JSONDecodeError:
        order_id = order_id or str(uuid.uuid4())[:8]
        return {'id': order_id, 'confirm_message': _fallback(lang), 'items': [], 'language': lang}
    except Exception as e:
        print(f'[ai_engine ERROR] {e}')
        order_id = order_id or str(uuid.uuid4())[:8]
        return {'id': order_id, 'confirm_message': _fallback(lang), 'items': [], 'language': lang}

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
        'en-IN': "Sorry, I didn't quite catch that. Could you repeat your order?",
        'hi-IN': "Maafi kijiye, dobara bolein.",
        'kn-IN': "Kshamisi, dayavittu maddu heliri.",
        'mr-IN': "Maafi kara, punha sanga.",
    }
    return fallbacks.get(lang, fallbacks['en-IN'])
