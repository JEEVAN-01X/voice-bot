from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from ai_engine import process_order, detect_intent, increment_retries, can_retry, confirm_order, pending_orders
from db import save_order

router = APIRouter()

THANK_YOU = {
    'en-IN': "Wonderful! Your order is confirmed. We'll get that to you soon. Have a great day!",
    'hi-IN': "Bahut acha! Aapka order confirm ho gaya. Jaldi pahunchenge. Dhanyavaad!",
    'kn-IN': "Thumba chennaagide! Nimma order confirm aagide. Sheegrane kalisutteve. Dhanyavaadagalu!",
    'mr-IN': "Chhan! Aapla order confirm zhala. Lavkar pathavto. Dhanyavaad!",
}

RETRY_PROMPT = {
    'en-IN': "No problem at all! What would you like to change?",
    'hi-IN': "Koi baat nahi! Kya badalna chahte hain?",
    'kn-IN': "Parvaagilla! Enu badalaayisabeku?",
    'mr-IN': "Thik aahe! Kay badlayacha aahe?",
}

MAX_RETRIES_MSG = {
    'en-IN': "I'm sorry, I'm having trouble understanding. Please call us back and we'll help you. Goodbye!",
    'hi-IN': "Maafi kijiye, samajhne mein dikkat ho rahi hai. Dobara call karein. Namaste!",
    'kn-IN': "Kshamisi, arthamaadikollalu kashta aagutide. Dayavittu maddu call madi. Vandanegalu!",
    'mr-IN': "Maafi kara, samajhayala tras hot aahe. Punha call kara. Namaskar!",
}

@router.post('/call-start')
async def call_start():
    resp = VoiceResponse()
    gather = Gather(
        input='speech',
        action='/twilio/process-speech',
        language='en-IN',          # Twilio STT hint — handles all 4 languages fine
        speech_timeout="auto",
        timeout=40,
        enhanced='false',
        profanity_filter='false',
    )
    # Priya introduces herself — warm, human, no menu
    gather.say(
        "Hi! This is Priya from Automaton AI. Please tell me your order.",
        language='en-IN',
        voice='Polly.Aditi',       # Indian English voice — sounds human
    )
    resp.append(gather)
    resp.redirect('/twilio/call-start')  # if nobody speaks, try again
    return Response(content=str(resp), media_type='application/xml')


@router.post('/process-speech')
async def process_speech(
    request: Request,
    lang: str = 'auto',
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
    print(f'[DEBUG] SpeechResult: {SpeechResult}')
    result = await process_order(SpeechResult, lang)
    print(f'[DEBUG] AI result: {result}')
    print(f'[AI] {result}')

    # Use language detected by AI
    detected_lang = result.get('language', 'en-IN')

    # Store caller phone
    form = await request.form()
    caller = form.get('Caller', 'unknown')
    if result['id'] in pending_orders:
        pending_orders[result['id']]['customer_phone'] = caller
        pending_orders[result['id']]['raw_transcript'] = SpeechResult

    gather = Gather(
        input='speech',
        action=f'/twilio/confirm?lang={detected_lang}&order_id={result["id"]}',
        language=detected_lang,
        speech_timeout="auto",
        timeout=40,
        enhanced='false',
    )
    gather.say(result['confirm_message'], language=detected_lang)
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

    if intent == 'confirm':
        order_data = confirm_order(order_id)
        try:
            save_order(order_id, order_data)
            print(f'[DB] ✅ Saved order {order_id}: {order_data.get("items")}')
        except Exception as e:
            print(f'[DB ERROR] {e}')
        resp.say(THANK_YOU.get(lang, THANK_YOU['en-IN']), language=lang)
        resp.hangup()

    elif intent == 'deny':
        increment_retries(order_id)
        if can_retry(order_id):
            resp.say(RETRY_PROMPT.get(lang, RETRY_PROMPT['en-IN']), language=lang)
            gather = Gather(
                input='speech',
                action=f'/twilio/process-speech?lang={lang}',
                language=lang,
                speech_timeout="auto",
                timeout=40,
                enhanced='false',
            )
            resp.append(gather)
        else:
            resp.say(MAX_RETRIES_MSG.get(lang, MAX_RETRIES_MSG['en-IN']), language=lang)
            resp.hangup()

    else:
        # Unclear — ask again gently
        gather = Gather(
            input='speech',
            action=f'/twilio/confirm?lang={lang}&order_id={order_id}',
            language=lang,
            speech_timeout="auto",
            timeout=40,
            enhanced='false',
        )
        gather.say(
            "Sorry, just say yes to confirm or no to change something.",
            language=lang,
        )
        resp.append(gather)

    return Response(content=str(resp), media_type='application/xml')
