from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from ai_engine import process_order, detect_intent, increment_retries, can_retry, confirm_order, pending_orders
from db import save_order

router = APIRouter()

VOICES = {
    'en-IN': 'Polly.Aditi',
    'hi-IN': 'Google.hi-IN-Wavenet-A',
    'kn-IN': 'Google.kn-IN-Wavenet-A',
    'mr-IN': 'Google.mr-IN-Wavenet-A',
}

THANK_YOU = {
    'en-IN': "Wonderful! Your order is confirmed. We'll get that to you soon. Have a great day!",
    'hi-IN': "Bahut acha! Aapka order confirm ho gaya. Jaldi pahunchenge. Dhanyavaad!",
    'kn-IN': "Thumba chennaagide! Nimma order confirm aagide. Sheegrane kalisutteve. Dhanyavaadagalu!",
    'mr-IN': "Chhan! Aapla order confirm zhala. Lavkar pathavto. Dhanyavaad!",
}

RETRY_PROMPT = {
    'en-IN': "No problem! What would you like to change?",
    'hi-IN': "Koi baat nahi! Kya badalna chahte hain?",
    'kn-IN': "Parvaagilla! Enu badalaayisabeku?",
    'mr-IN': "Thik aahe! Kay badlayacha aahe?",
}

MAX_RETRIES_MSG = {
    'en-IN': "I'm sorry, I'm having trouble understanding. Please call us back. Goodbye!",
    'hi-IN': "Maafi kijiye, samajhne mein dikkat ho rahi hai. Dobara call karein. Namaste!",
    'kn-IN': "Kshamisi, arthamaadikollalu kashta aagutide. Maddu call madi. Vandanegalu!",
    'mr-IN': "Maafi kara, samajhayala tras hot aahe. Punha call kara. Namaskar!",
}

def get_voice(lang):
    return VOICES.get(lang, 'Polly.Aditi')

@router.post('/call-start')
async def call_start():
    resp = VoiceResponse()
    gather = Gather(
        input='speech',
        action='/twilio/process-speech',
        language='en-IN',
        speech_timeout="auto",
        timeout=40,
        enhanced='false',
        profanity_filter='false',
    )
    gather.say(
        "Hi! This is Priya from Automaton AI Infosystem. Please tell me what you'd like to order.",
        language='en-IN',
        voice='Polly.Aditi',
    )
    resp.append(gather)
    resp.redirect('/twilio/call-start')
    return Response(content=str(resp), media_type='application/xml')


@router.post('/process-speech')
async def process_speech(
    request: Request,
    lang: str = 'auto',
    order_id: str = '',
    SpeechResult: str = Form(default=''),
):
    resp = VoiceResponse()

    if not SpeechResult.strip():
        gather = Gather(
            input='speech',
            action='/twilio/process-speech',
            language='en-IN',
            speech_timeout="auto",
            timeout=40,
            enhanced='false',
        )
        gather.say("Sorry, I didn't catch that. Please tell me your order.", language='en-IN', voice='Polly.Aditi')
        resp.append(gather)
        return Response(content=str(resp), media_type='application/xml')

    print(f'[STT] {SpeechResult}')
    result = await process_order(SpeechResult, lang, order_id or None)
    print(f'[AI] {result}')

    detected_lang = lang if lang not in ('auto', 'en-IN', '') else result.get('language', 'en-IN')
    ready = result.get('ready_to_confirm', False)
    voice = get_voice(detected_lang)

    form = await request.form()
    caller = form.get('Caller', 'unknown')
    if result['id'] in pending_orders:
        pending_orders[result['id']]['customer_phone'] = caller

    if ready:
        gather = Gather(
            input='speech',
            action=f'/twilio/confirm?lang={detected_lang}&order_id={result["id"]}',
            language=detected_lang,
            speech_timeout="auto",
            timeout=40,
            enhanced='false',
        )
        gather.say(result['confirm_message'], language=detected_lang, voice=voice)
        resp.append(gather)
    else:
        gather = Gather(
            input='speech',
            action=f'/twilio/process-speech?lang={detected_lang}&order_id={result["id"]}',
            language=detected_lang,
            speech_timeout="auto",
            timeout=40,
            enhanced='false',
        )
        gather.say(result['confirm_message'], language=detected_lang, voice=voice)
        resp.append(gather)

    return Response(content=str(resp), media_type='application/xml')


@router.post('/confirm')
async def confirm(
    lang: str = 'en-IN',
    order_id: str = '',
    SpeechResult: str = Form(default=''),
):
    resp = VoiceResponse()
    intent = detect_intent(SpeechResult)
    voice = get_voice(lang)

    if intent == 'confirm':
        order_data = confirm_order(order_id)
        try:
            save_order(order_id, order_data)
            print(f'[DB] Saved order {order_id}: {order_data.get("items")}')
        except Exception as e:
            print(f'[DB ERROR] {e}')
        resp.say(THANK_YOU.get(lang, THANK_YOU['en-IN']), language=lang, voice=voice)
        resp.hangup()

    elif intent == 'deny':
        increment_retries(order_id)
        if can_retry(order_id):
            gather = Gather(
                input='speech',
                action=f'/twilio/process-speech?lang={lang}&order_id={order_id}',
                language=lang,
                speech_timeout="auto",
                timeout=40,
                enhanced='false',
            )
            gather.say(RETRY_PROMPT.get(lang, RETRY_PROMPT['en-IN']), language=lang, voice=voice)
            resp.append(gather)
        else:
            resp.say(MAX_RETRIES_MSG.get(lang, MAX_RETRIES_MSG['en-IN']), language=lang, voice=voice)
            resp.hangup()

    else:
        gather = Gather(
            input='speech',
            action=f'/twilio/confirm?lang={lang}&order_id={order_id}',
            language=lang,
            speech_timeout="auto",
            timeout=40,
            enhanced='false',
        )
        gather.say(RETRY_PROMPT.get(lang, RETRY_PROMPT['en-IN']), language=lang, voice=voice)
        resp.append(gather)

    return Response(content=str(resp), media_type='application/xml')
