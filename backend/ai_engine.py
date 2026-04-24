from groq import Groq
import json
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are a friendly multilingual order confirmation bot for Automaton AI Infosystem.

Your job:
1. Extract order details from what the customer said.
2. Generate a natural confirmation message in the SAME language the customer used.
3. Return ONLY valid JSON — no extra text, no markdown, no explanation.

Return this exact format:
{
  "items": ["item1 qty", "item2 qty"],
  "address": "delivery address or null",
  "confirm_message": "Full confirmation text in customer language",
  "language_detected": "en-IN or hi-IN or kn-IN or mr-IN"
}

Confirmation message rules:
- Restate the items and quantities clearly
- Ask the customer to say Yes to confirm
- Keep tone warm and professional
- Match the language of the customer exactly
- If this is a retry (previous attempt failed), acknowledge it warmly
"""

pending_orders = {}

POSITIVE_WORDS = ['yes', 'haan', 'haan ji', 'ho', 'hoo', 'sari', 'houdu',
                  'correct', 'theek hai', 'theek', 'bilkul', 'hoya', 'thik', 'baro']
NEGATIVE_WORDS = ['no', 'nahi', 'nako', 'illa', 'beda', 'wrong', 'galat',
                  'cancel', 'repeat', 'dobara', 'chukiche', 'punha']

def detect_intent(speech_text: str) -> str:
    text = speech_text.lower().strip()
    if any(word in text for word in POSITIVE_WORDS):
        return 'confirm'
    elif any(word in text for word in NEGATIVE_WORDS):
        return 'deny'
    return 'unclear'

async def process_order(speech_text: str, lang: str, order_id: str = None) -> dict:
    """
    Process an order from speech text.
    Pass order_id on retries to maintain conversation context.
    """
    try:
        # Build conversation history for multi-turn context
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

        # If this is a retry, include previous attempt in context
        if order_id and order_id in pending_orders:
            prev = pending_orders[order_id]
            retry_count = prev.get('retries', 0)
            messages.append({
                'role': 'user',
                'content': f'Language hint: {lang}\nCustomer said: {prev["raw_transcript"]}'
            })
            messages.append({
                'role': 'assistant',
                'content': json.dumps({
                    'items': prev['items'],
                    'address': prev['address'],
                    'confirm_message': prev.get('last_confirm_message', ''),
                    'language_detected': lang
                }, ensure_ascii=False)
            })
            messages.append({
                'role': 'user',
                'content': f'Customer did not confirm (retry {retry_count}). They said: {speech_text}\nPlease re-extract and confirm again in {lang}.'
            })
        else:
            messages.append({
                'role': 'user',
                'content': f'Language hint: {lang}\nCustomer said: {speech_text}'
            })

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            max_tokens=500,
            messages=messages
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1].lstrip('json').strip()

        data = json.loads(raw)

        # Reuse order_id on retries, create new one otherwise
        if not order_id or order_id not in pending_orders:
            order_id = str(uuid.uuid4())[:8]

        pending_orders[order_id] = {
            'items': data.get('items', []),
            'address': data.get('address'),
            'language': lang,
            'raw_transcript': speech_text,
            'last_confirm_message': data.get('confirm_message', ''),
            'status': 'pending',
            'retries': pending_orders.get(order_id, {}).get('retries', 0),
        }
        return {
            'id': order_id,
            'confirm_message': data['confirm_message'],
            'items': data.get('items', []),
        }
    except json.JSONDecodeError:
        return {'id': order_id, 'confirm_message': _fallback_message(lang), 'items': []}
    except Exception as e:
        print(f'[ai_engine] Error: {e}')
        return {'id': order_id, 'confirm_message': _fallback_message(lang), 'items': []}

def increment_retries(order_id: str) -> int:
    if order_id in pending_orders:
        pending_orders[order_id]['retries'] += 1
        return pending_orders[order_id]['retries']
    return 0

def can_retry(order_id: str, max_retries: int = 3) -> bool:
    return pending_orders.get(order_id, {}).get('retries', 999) < max_retries

def get_pending_order(order_id: str) -> dict:
    return pending_orders.get(order_id)

def confirm_order(order_id: str) -> dict:
    if order_id in pending_orders:
        pending_orders[order_id]['status'] = 'confirmed'
        return pending_orders[order_id]
    return {}

def _fallback_message(lang: str) -> str:
    fallbacks = {
        'en-IN': "Sorry, I didn't understand your order. Could you please repeat?",
        'hi-IN': "Maafi kijiye, mujhe aapka order samajh nahi aaya. Kya aap dobara bol sakte hain?",
        'kn-IN': "Kshamisi, ninage order artha aagalilla. Dayavittu maddu heliri.",
        'mr-IN': "Maafi kara, mala order samajla nahi. Aapla order punha saanga.",
    }
    return fallbacks.get(lang, fallbacks['en-IN'])

if __name__ == '__main__':
    import asyncio

    async def test():
        print("=== Testing all 4 languages ===\n")

        tests = [
            ("mujhe 2 kg aloo aur 1 kg pyaaz chahiye, sector 14 mein deliver karo", "hi-IN", "Hindi"),
            ("I want 3 kg tomatoes and 2 kg onions delivered to MG Road", "en-IN", "English"),
            ("nanage 1 kg tomato mattu 2 kg eerulli beku, koramangala ge deliver madi", "kn-IN", "Kannada"),
            ("mala 2 kg bataate aani 1 kg kanda pahije, Pune la deliver kara", "mr-IN", "Marathi"),
        ]

        for speech, lang, label in tests:
            print(f"Testing {label}...")
            result = await process_order(speech, lang)
            print(f"Items: {result['items']}")
            print(f"Confirm msg: {result['confirm_message']}")
            print()

        print("=== Testing multi-turn retry ===")
        r1 = await process_order("aloo chahiye", "hi-IN")
        oid = r1['id']
        print(f"Round 1 (vague): {r1['confirm_message']}")
        increment_retries(oid)
        r2 = await process_order("2 kg aloo, sector 5 mein", "hi-IN", order_id=oid)
        print(f"Round 2 (retry with context): {r2['confirm_message']}")
        print()

        print("=== Intent detection ===")
        for phrase in ["haan ji theek hai", "nahi galat hai", "umm okay", "houdu sari", "nako chukiche"]:
            print(f"  '{phrase}' → {detect_intent(phrase)}")

    asyncio.run(test())
