from stages.gemini_client import call_gemini, extract_json
from typing import Dict, Any

SYSTEM_PROMPT = """You are an expert software architect. Given a structured intent, design the complete application architecture.

You MUST return ONLY valid JSON with NO markdown, NO explanation, NO code fences.

Required JSON structure:
{
  "pages": [
    {
      "name": "string",
      "route": "string - e.g. /dashboard",
      "roles": ["roles that can access this page"],
      "components": ["list of UI components on this page"]
    }
  ],
  "api_endpoints": [
    {
      "path": "string - e.g. /api/users",
      "method": "GET|POST|PUT|DELETE",
      "description": "string",
      "auth_required": true,
      "roles": ["roles that can call this endpoint"],
      "request_fields": ["field names for request body"],
      "response_fields": ["field names in response"]
    }
  ],
  "db_tables": [
    {
      "name": "string - table name",
      "fields": [{"name": "string", "type": "string", "required": true}],
      "relations": ["e.g. belongs_to:users, has_many:orders"]
    }
  ],
  "auth_config": {
    "type": "JWT|session|oauth",
    "roles": ["list of roles"],
    "permissions": {"role_name": ["list of permissions"]}
  },
  "business_logic": ["list of business rules as strings"]
}

Rules:
- Every entity from intent must become a DB table
- Every feature must map to at least one API endpoint
- Every role must have defined permissions
- Pages must match routes with role-based access
- NEVER return anything except the JSON object"""

USER_TEMPLATE = """Design the architecture for this application intent:

{intent}

Return ONLY the JSON architecture object."""


async def design_architecture(intent: Dict[str, Any]) -> Dict[str, Any]:
    import json
    user_prompt = USER_TEMPLATE.format(intent=json.dumps(intent, indent=2))
    response = await call_gemini(SYSTEM_PROMPT, user_prompt, temperature=0.1)
    result = extract_json(response)

    # Ensure required fields exist
    required_fields = ["pages", "api_endpoints", "db_tables", "auth_config", "business_logic"]
    for field in required_fields:
        if field not in result:
            if field == "auth_config":
                result[field] = {"type": "JWT", "roles": [], "permissions": {}}
            elif field == "business_logic":
                result[field] = []
            else:
                result[field] = []

    return result
