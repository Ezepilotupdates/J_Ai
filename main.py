# app/main.py
import os
import json
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from ai import AIClient
from telegram import TgClient
from memory import Memory
from utils import extract_text_from_pdf_bytes, send_health_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
OWNER_ID = os.getenv("OWNER_ID")

# Initialize
app = FastAPI()
tg = TgClient(TELEGRAM_TOKEN)
ai = AIClient(api_key=OPENAI_API_KEY)
memory = Memory(REDIS_URL)

@app.on_event("startup")
async def startup():
    await memory.connect()
    logger.info("Bot started.")

@app.on_event("shutdown")
async def shutdown():
    await memory.close()
    logger.info("Bot stopped.")

@app.post("/webhook")
async def webhook(request: Request, background: BackgroundTasks):
    update = await request.json()
    if "message" in update:
        background.add_task(handle_message, update["message"])
    elif "callback_query" in update:
        background.add_task(handle_callback, update["callback_query"])
    return {"ok": True}

@app.get("/health")
def health():
    return send_health_check()

async def handle_message(message: dict):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "")

    # Commands
    if text.startswith("/"):
        await handle_command(chat_id, user_id, text)
        return

    # Quick buttons
    if text == "🖼 Generate Image":
        tg.send_message(chat_id, "Send a description for the image or use /image <prompt>")
        return
    if text == "🧠 Clear Memory":
        await memory.clear_chat(chat_id)
        tg.send_message(chat_id, "Memory cleared.")
        return

    # Normal chat
    await memory.append_message(chat_id, "user", text)
    history = await memory.get_history(chat_id)
    reply = await ai.chat_reply(history + [{"role": "user", "content": text}])
    await memory.append_message(chat_id, "assistant", reply)
    tg.send_message(chat_id, reply, reply_markup=tg.quick_reply_markup())

async def handle_command(chat_id: int, user_id: int, text: str):
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/start":
        tg.send_message(chat_id, "Welcome! Use buttons or type a message.")
        tg.send_message(chat_id, "Commands: /image <prompt>, /reset", reply_markup=tg.keyboard_markup())
        return

    if cmd == "/reset":
        await memory.clear_chat(chat_id)
        tg.send_message(chat_id, "Conversation reset.")
        return

    if cmd == "/image":
        if not arg:
            tg.send_message(chat_id, "Usage: /image <prompt>")
            return
        tg.send_message(chat_id, "Generating image...")
        img_url = await ai.generate_image(arg)
        if img_url:
            tg.send_photo(chat_id, img_url)
        else:
            tg.send_message(chat_id, "Image generation failed.")

    # Admin commands
    if str(user_id) == str(OWNER_ID):
        if cmd == "/broadcast" and arg:
            users = await memory.get_all_users()
            tg.send_message(chat_id, f"Broadcasting to {len(users)} users...")
            for u in users:
                tg.send_message(u["id"], arg)
            tg.send_message(chat_id, "Broadcast finished.")