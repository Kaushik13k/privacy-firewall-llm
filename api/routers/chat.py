import os
from google import genai
from fastapi import APIRouter
from pydantic import BaseModel
from ..rate_limiter import limiter
from fastapi import APIRouter, Request
from firewall.session_memory import MemoryStore
from firewall.abuse_detector import AbuseDetector


router = APIRouter()
abuse_detector = AbuseDetector()

memory_store = MemoryStore(max_tokens_per_session=1000)


class Prompt(BaseModel):
    message: str
    _meta: dict = {}


@router.post("/ask", tags=["ASK"], responses={404: {"description": "Not found"}})
@limiter.limit("10/minute")
async def ask(prompt: Prompt, request: Request):
    body = await request.json()
    meta = body.get("_meta", {})
    session_id = meta.get("session_id")
    if abuse_detector.is_abusive(session_id):
        return {"error": "Too many suspicious attempts. Try later."}

    if "injection" in prompt.message.lower():
        abuse_detector.record_failure(session_id)

    memory_store.add_message(session_id, role="user", content=prompt.message)
    context = memory_store.get_context(session_id)
    messages = context + [{"role": "user", "content": prompt.message}]
    contents = [{"role": msg["role"], "parts": [msg["content"]]}
                for msg in messages]

    client = genai.Client(api_key=os.getenv(
        "GENAI_API_KEY", "abc"))
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt.message,
    )

    ai_response = response.text
    memory_store.add_message(session_id, role="assistant", content=ai_response)
    return {
        "response": response.text,
        "redacted_prompt": prompt.message,
        **meta
    }
