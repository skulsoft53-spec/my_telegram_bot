from fastapi import FastAPI
from pydantic import BaseModel
import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1-mini"

app = FastAPI()

class GenerateRequest(BaseModel):
    text: str
    language_hint: str | None = None

SYSTEM_PROMPT = """
Ты — экспертный помощник по программированию.
Генерируй качественный, рабочий код.
Давай краткие пояснения.
"""

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/ping")
def ping():
    return {"status": "alive"}

@app.post("/generate")
async def generate(req: GenerateRequest):
    user_text = req.text
    language_hint = req.language_hint
    prompt = f"Запрос: {user_text}\nЯзык: {language_hint}"
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.1,
    )
    reply = response.choices[0].message.content
    return {"reply": reply}