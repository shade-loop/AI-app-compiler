import os
import json
import re
from groq import Groq
from typing import Any, Dict

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)


async def call_gemini(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
    response = client.chat.completions.create(
    model=GROQ_MODEL,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=temperature,
    max_tokens=8000,  # Change from 4096 to 8000
)
    return response.choices[0].message.content


def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Remove markdown code fences
    fenced = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    
    # Find start of JSON
    for start_char in ['{', '[']:
        idx = text.find(start_char)
        if idx != -1:
            text = text[idx:]
            break
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try fixing truncated JSON by finding last complete object
    # Add missing closing braces/brackets
    open_braces = text.count('{') - text.count('}')
    open_brackets = text.count('[') - text.count(']')
    
    fixed = text
    fixed += ']' * open_brackets
    fixed += '}' * open_braces
    
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    # Last resort - truncate to last valid }
    for end in range(len(text), 0, -1):
        try:
            return json.loads(text[:end])
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"Could not parse JSON from: {text[:200]}")