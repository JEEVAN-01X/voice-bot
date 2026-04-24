from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from ai_engine import process_order, detect_intent, increment_retries, can_retry, confirm_order
from db import save_order

router = APIRouter()

LANG_CONFIG = {
    'en-IN': {'order_prompt': 'Please tell me your order.', 'not_heard': 'Sorry, I did not catch that. Please try again.', 'thank_you': 'Thank you! Your order has been confirmed. Goodbye!', 'retry': 'No problem. Please tell me your order again.'},
    'hi-IN': {'order_prompt': 'Apna order batayein.', 'not_heard': 'Maafi kijiye, mujhe suna nahi. Dobara bolein.', 'thank_you': 'Shukriya! Aapka order confirm ho gaya. Namaste!', 'retry': 'Koi baat nahi. Apna order dobara batayein.'},
    'kn-IN': {'order_prompt': 'Nimma order heliri.', 'not_heard': 'Kshamisi, nange keLisalilla. Dayavittu maddu helirii.', 'thank_you': 'Dhanyavadagalu! Nimma order drudheegondide.', 'retry': 'Parvaagilla. Nimma order maddu helirii.'},
    'mr-IN': {'order_prompt': 'Aapla order sanga.', 'not_heard': 'Maafi kara, mala aaikale nahi. Punha sanga.', 'thank_you': 'Dhanyavad! Aapla order confirm zhala.', 'retry': 'Thik aahe. Aapla order punha sanga.'},
}

@router.post('/call-start')
async def call_start():
    resp = VoiceResponse()
    gather = Gather(num_digits=1, action='/twilio/language-selected')
    gather.say('Press 1 for English. 2 ke liye Hindi. 3 for Kannada. 4 for Marathi.')
    resp.append(gather)
    return Response(content=str(resp), media_type='application/xml')

@router.post('/language-selected')
async def language_selected(Digits: str = Form(...)):
    lang_map = {'1': 'en-IN', '2': 'hi-IN', '3': 'kn-IN', '4': 'mr-IN'}
    lang = lang_map.get(Digits, 'en-IN')
    cfg = LANG_CONFIG[lang]
    resp = VoiceResponse()
    gather = Gather(input='speech', action=f'/twilio/process-speech?lang={lang}',
                    language=lang, speech_timeout=3)
    gather.say(cfg['order_prompt'])
    resp.append(gather)
    return Response(content=str(resp), media_type='application/xml')

@router.post('/process-speech')
async def process_speech(request: Request, lang: str = 'en-IN', SpeechResult: str = Form(default='')):
    cfg = LANG_CONFIG[lang]
    resp = VoiceResponse()

    if not SpeechResult:
        resp.say(cfg['not_heard'], language=lang)
        resp.redirect('/twilio/language-selected')
        return Response(content=str(resp), media_type='application/xml')

    # ✅ NOW calling ai_engine
    result = await process_order(SpeechResult, lang)

    if not result['id'] or not result['items']:
        # AI couldn't extract anything meaningful
        resp.say(cfg['not_heard'], language=lang)
        resp.redirect(f'/twilio/language-selected')
        return Response(content=str(resp), media_type='application/xml')

    gather = Gather(
        input='speech',
        action=f'/twilio/confirm?lang={lang}&order_id={result["id"]}',
        language=lang,
        speech_timeout=3
    )
    gather.say(result['confirm_message'], language=lang)
    resp.append(gather)
    return Response(content=str(resp), media_type='application/xml')

@router.post('/confirm')
async def confirm(lang: str = 'en-IN', order_id: str = '', SpeechResult: str = Form(default='')):
    cfg = LANG_CONFIG[lang]
    resp = VoiceResponse()

    intent = detect_intent(SpeechResult)

    if intent == 'confirm':
        # Save to Firebase
        order_data = confirm_order(order_id)
        await save_order(order_id, order_data)
        resp.say(cfg['thank_you'], language=lang)
        resp.hangup()

    elif intent == 'deny' or intent == 'unclear':
        increment_retries(order_id)
        if can_retry(order_id):
            # Retry with context — pass order_id so ai_engine remembers
            result = await process_order(SpeechResult, lang, order_id=order_id)
            gather = Gather(
                input='speech',
                action=f'/twilio/confirm?lang={lang}&order_id={result["id"]}',
                language=lang,
                speech_timeout=3
            )
            gather.say(result['confirm_message'], language=lang)
            resp.append(gather)
        else:
            # Max retries hit — graceful exit
            endings = {
                'en-IN': 'Sorry, we could not process your order. Please call again. Goodbye!',
                'hi-IN': 'Maafi kijiye, aapka order process nahi ho saka. Dobara call karein. Namaste!',
                'kn-IN': 'Kshamisi, nimma order process aagalilla. Dayavittu maddu call madi.',
                'mr-IN': 'Maafi kara, aapla order process zhaala nahi. Punha call kara.',
            }
            resp.say(endings.get(lang, endings['en-IN']), language=lang)
            resp.hangup()

    else:
        resp.say(cfg['not_heard'], language=lang)
        resp.redirect(f'/twilio/language-selected')

    return Response(content=str(resp), media_type='application/xml')
