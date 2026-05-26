from stages.gemini_client import call_gemini, extract_json
from typing import Dict, Any

SYSTEM_PROMPT = """You are an expert full-stack developer. Given intent and architecture, generate complete executable schemas.

You MUST return ONLY valid JSON with NO markdown, NO explanation, NO code fences.

Required JSON structure:
{
  "ui_schema": [
    {
      "page": "string - page name",
      "route": "string",
      "layout": "string - e.g. sidebar, topnav, fullscreen",
      "components": [
        {
          "name": "string",
          "type": "table|form|card|chart|modal|list",
          "fields": [{"name": "string", "type": "text|email|password|select|date|number", "required": true, "label": "string"}],
          "actions": [{"label": "string", "type": "submit|navigate|delete|modal", "target": "string"}],
          "data_source": "string - API endpoint that feeds this component"
        }
      ],
      "roles": ["roles that can access"]
    }
  ],
  "api_schema": [
    {
      "path": "string",
      "method": "string",
      "auth_required": true,
      "roles": ["strings"],
      "request_body": {"field_name": "type_string"},
      "response": {"field_name": "type_string"},
      "validation_rules": ["e.g. email must be unique, name min 2 chars"],
      "db_operations": ["e.g. INSERT INTO users, SELECT FROM orders WHERE user_id=:id"]
    }
  ],
  "db_schema": [
    {
      "table": "string",
      "columns": [{"name": "string", "type": "VARCHAR|INT|BOOLEAN|TIMESTAMP|TEXT|UUID", "nullable": false, "default": null, "primary_key": false, "foreign_key": null}],
      "indexes": ["column_name"],
      "constraints": ["e.g. UNIQUE(email), CHECK(age > 0)"]
    }
  ],
  "auth_schema": [
    {
      "role": "string",
      "can_access_pages": ["page routes"],
      "can_call_endpoints": ["METHOD /path"],
      "permissions": ["create:resource", "read:resource", "update:resource", "delete:resource"]
    }
  ]
}

Rules:
- UI fields must match API request_body fields
- API request_body fields must map to DB columns
- Every DB table needs id (UUID), created_at, updated_at
- Auth schema must cover every role from architecture
- NEVER return anything except the JSON object"""

USER_TEMPLATE = """Generate complete executable schemas from this intent and architecture:

INTENT:
{intent}

ARCHITECTURE:
{architecture}

Return ONLY the JSON schema object."""


async def generate_schemas(intent: Dict[str, Any], architecture: Dict[str, Any]) -> Dict[str, Any]:
    import json
    user_prompt = USER_TEMPLATE.format(
        intent=json.dumps(intent, indent=2),
        architecture=json.dumps(architecture, indent=2)
    )
    response = await call_gemini(SYSTEM_PROMPT, user_prompt, temperature=0.1)
    result = extract_json(response)

    required_fields = ["ui_schema", "api_schema", "db_schema", "auth_schema"]
    for field in required_fields:
        if field not in result:
            result[field] = []

    return result
