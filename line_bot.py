import os
import sys
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Adjust the path to import core_logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
import core_logic

app = FastAPI()

# LINE Bot API settings
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("LINE_CHANNEL_ACCESS_TOKEN environment variable not set.")
if not LINE_CHANNEL_SECRET:
    raise ValueError("LINE_CHANNEL_SECRET environment variable not set.")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.post("/line_webhook")
async def handle_line_webhook(request: Request):
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body = await request.body()
    body_str = body.decode('utf-8')

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text

    # Process message using core_logic
    response_text = core_logic.process_message(
        user_identifier=user_id,
        message_text=user_message,
        platform='line'
    )

    if response_text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

@app.get("/")
async def root():
    return {"message": "LINE Bot is running!"}

# To run this file:
# uvicorn line_bot:app --reload --port 8000
