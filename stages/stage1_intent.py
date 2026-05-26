from stages.gemini_client import call_gemini, extract_json
from typing import Dict, Any

SYSTEM_PROMPT = """You are an expert software architect. Your job is to parse a user's natural language app description into a structured intent object.

You MUST return ONLY valid JSON with NO markdown, NO explanation, NO code fences.

Required JSON structure:
{
  "app_name": "string - inferred name",
  "app_type": "string - e.g. CRM, E-commerce, SaaS, Dashboard, Social",
  "entities": ["list of main data entities like User, Product, Order"],
  "roles": ["list of user roles like admin, user, manager"],
  "features": ["list of features like login, dashboard, payments"],
  "constraints": ["list of explicit constraints mentioned"],
  "assumptions": ["list of reasonable assumptions you made for unspecified things"]
}

Rules:
- If the prompt is vague, make reasonable assumptions and document them
- If the prompt has conflicting requirements, note them in constraints
- Always include at least 3 entities, 2 roles, 5 features
- Never return anything except the JSON object"""

USER_TEMPLATE = """Parse this app description into structured intent:

"{prompt}"

Return ONLY the JSON object."""


async def extract_intent(prompt: str) -> Dict[str, Any]:
    user_prompt = USER_TEMPLATE.format(prompt=prompt)
    response = await call_gemini(SYSTEM_PROMPT, user_prompt, temperature=0.1)
    result = extract_json(response)

    # Ensure required fields exist
    required_fields = ["app_name", "app_type", "entities", "roles", "features", "constraints", "assumptions"]
    for field in required_fields:
        if field not in result:
            if field in ["entities", "roles", "features", "constraints", "assumptions"]:
                result[field] = []
            else:
                result[field] = "unknown"

    return result
