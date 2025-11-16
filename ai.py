# app/ai.py
import httpx

OPENAI_BASE = "https://api.openai.com/v1"

class AIClient:
    def __init__(self, api_key: str, chat_model="gpt-4o-mini", image_model="gpt-image-1"):
        self.api_key = api_key
        self.chat_model = chat_model
        self.image_model = image_model
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def chat_reply(self, messages, max_tokens=800, temperature=0.6):
        body = {"model": self.chat_model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{OPENAI_BASE}/chat/completions", headers=self.headers, json=body)
        if resp.status_code >= 300:
            return "AI error. Try later."
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    async def generate_image(self, prompt, n=1, size="1024x1024"):
        body = {"prompt": prompt, "n": n, "size": size}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{OPENAI_BASE}/images/generations", headers=self.headers, json=body)
        if resp.status_code >= 300:
            return None
        data = resp.json()
        try:
            return data["data"][0].get("url")
        except:
            return None