import os
import json
import re
import httpx
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


async def call_gemini(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 8000}
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


def extract_json(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty response from LLM")
    text = text.strip()
    fenced = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    obj_start = text.find('{')
    arr_start = text.find('[')
    if obj_start == -1 and arr_start == -1:
        raise ValueError(f"No JSON found: {text[:200]}")
    if obj_start == -1:
        start = arr_start
    elif arr_start == -1:
        start = obj_start
    else:
        start = min(obj_start, arr_start)
    text = text[start:]
    try:
        result = json.loads(text)
        if isinstance(result, (dict, list)):
            return result
    except json.JSONDecodeError:
        pass
    open_braces = text.count('{') - text.count('}')
    open_brackets = text.count('[') - text.count(']')
    fixed = text + (']' * max(0, open_brackets)) + ('}' * max(0, open_braces))
    try:
        result = json.loads(fixed)
        if isinstance(result, (dict, list)):
            return result
    except json.JSONDecodeError:
        pass
    for end in range(len(text), 0, -1):
        try:
            result = json.loads(text[:end])
            if isinstance(result, (dict, list)):
                return result
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Could not parse JSON: {text[:200]}")