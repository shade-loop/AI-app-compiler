from stages.gemini_client import call_gemini, extract_json
from typing import Dict, Any, List, Tuple
import json


def check_api_db_consistency(schemas: Dict[str, Any]) -> List[str]:
    """Check that API fields match DB columns"""
    issues = []
    db_tables = {t.get("table", "").lower(): t for t in schemas.get("db_schema", [])}

    for endpoint in schemas.get("api_schema", []):
        req_body = endpoint.get("request_body", {})
        db_ops = endpoint.get("db_operations", [])

        for op in db_ops:
            for table_name, table in db_tables.items():
                if table_name in op.lower():
                    db_cols = {c["name"].lower() for c in table.get("columns", [])}
                    for field in req_body.keys():
                        if field.lower() not in db_cols and field not in ["id", "created_at", "updated_at"]:
                            issues.append(f"API field '{field}' in {endpoint['path']} not found in DB table '{table_name}'")
    return issues


def check_ui_api_consistency(schemas: Dict[str, Any]) -> List[str]:
    """Check that UI components reference valid API endpoints"""
    issues = []
    api_paths = {f"{e['method']} {e['path']}" for e in schemas.get("api_schema", [])}
    api_paths_simple = {e["path"] for e in schemas.get("api_schema", [])}

    for page in schemas.get("ui_schema", []):
        for component in page.get("components", []):
            data_source = component.get("data_source", "")
            if data_source and data_source not in api_paths_simple and data_source not in api_paths:
                issues.append(f"UI component '{component['name']}' references non-existent endpoint: {data_source}")
    return issues


def check_auth_consistency(schemas: Dict[str, Any]) -> List[str]:
    """Check that all roles are defined in auth schema"""
    issues = []
    auth_roles = {r["role"] for r in schemas.get("auth_schema", [])}

    for endpoint in schemas.get("api_schema", []):
        for role in endpoint.get("roles", []):
            if role not in auth_roles:
                issues.append(f"Role '{role}' in endpoint {endpoint['path']} not defined in auth schema")

    for page in schemas.get("ui_schema", []):
        for role in page.get("roles", []):
            if role not in auth_roles:
                issues.append(f"Role '{role}' in page {page['route']} not defined in auth schema")
    return issues


def check_required_fields(schemas: Dict[str, Any]) -> List[str]:
    """Check required fields exist in all schema objects"""
    issues = []

    for i, table in enumerate(schemas.get("db_schema", [])):
        if "table" not in table:
            issues.append(f"DB schema item {i} missing 'table' field")
        cols = [c.get("name", "") for c in table.get("columns", [])]
        if "id" not in cols:
            issues.append(f"DB table '{table.get('table', i)}' missing 'id' column")

    for i, endpoint in enumerate(schemas.get("api_schema", [])):
        if "path" not in endpoint:
            issues.append(f"API schema item {i} missing 'path' field")
        if "method" not in endpoint:
            issues.append(f"API schema item {i} missing 'method' field")

    return issues


REPAIR_PROMPT = """You are a JSON schema repair engine. You have a schema with consistency issues.

Fix ONLY the listed issues. Return the complete corrected schema as valid JSON only.
Do NOT add markdown, explanations, or code fences.

CURRENT SCHEMA:
{schema}

ISSUES TO FIX:
{issues}

ARCHITECTURE REFERENCE:
{architecture}

Return ONLY the corrected complete JSON schema."""


async def validate_and_repair(
    schemas: Dict[str, Any],
    architecture: Dict[str, Any],
    max_retries: int = 2
) -> Tuple[Dict[str, Any], List[str], int]:
    repair_log = []
    retries = 0
    current_schemas = schemas.copy()

    for attempt in range(max_retries + 1):
        issues = []
        issues.extend(check_required_fields(current_schemas))
        issues.extend(check_api_db_consistency(current_schemas))
        issues.extend(check_ui_api_consistency(current_schemas))
        issues.extend(check_auth_consistency(current_schemas))

        if not issues:
            repair_log.append(f"✅ Validation passed on attempt {attempt + 1}")
            break

        repair_log.append(f"⚠️ Attempt {attempt + 1}: Found {len(issues)} issues: {'; '.join(issues[:3])}")

        if attempt < max_retries:
            retries += 1
            try:
                repair_response = await call_gemini(
                    "You are a JSON repair engine. Fix the schema issues. Return ONLY valid JSON.",
                    REPAIR_PROMPT.format(
                        schema=json.dumps(current_schemas, indent=2)[:3000],
                        issues="\n".join(f"- {i}" for i in issues),
                        architecture=json.dumps(architecture, indent=2)[:2000]
                    ),
                    temperature=0.05
                )
                repaired = extract_json(repair_response)
                current_schemas = repaired
                repair_log.append(f"🔧 Repair attempt {retries} applied")
            except Exception as e:
                repair_log.append(f"❌ Repair attempt {retries} failed: {str(e)}")
                break
        else:
            repair_log.append(f"⚠️ Max retries reached. {len(issues)} issues remain (non-blocking)")

    return current_schemas, repair_log, retries
