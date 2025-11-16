# app/telegram.py
import requests
import json
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"
FILE_BASE = f"https://api.telegram.org/file/bot{TOKEN}"

class TgClient:
    def __init__(self, token: str):
        self.token = token
        self.base = f"https://api.telegram.org/bot{token}"

    def send_message(self, chat_id, text, reply_markup=None):
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        requests.post(f"{self.base}/sendMessage", json=payload)

    def send_photo(self, chat_id, photo_url, caption=None):
        payload = {"chat_id": chat_id, "photo": photo_url}
        if caption:
            payload["caption"] = caption
        requests.post(f"{self.base}/sendPhoto", json=payload)

    def keyboard_markup(self):
        return {"keyboard": [[{"text": "🖼 Generate Image"}, {"text": "🧠 Clear Memory"}]], "resize_keyboard": True}

    def quick_reply_markup(self):
        return {"inline_keyboard": [[{"text": "Summarize file", "callback_data": "action:summary"}]]]}

    def get_file_path(self, file_id):
        resp = requests.get(f"{self.base}/getFile", params={"file_id": file_id})
        return resp.json().get("result", {}).get("file_path")

    def file_url(self, file_path):
        return f"{FILE_BASE}/{file_path}"