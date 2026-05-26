from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PipelineRequest(BaseModel):
    prompt: str = Field(..., description="Natural language app description")


class IntentResult(BaseModel):
    app_name: str
    app_type: str
    entities: List[str]
    roles: List[str]
    features: List[str]
    constraints: List[str]
    assumptions: List[str]


class ArchitectureResult(BaseModel):
    pages: List[Dict[str, Any]]
    api_endpoints: List[Dict[str, Any]]
    db_tables: List[Dict[str, Any]]
    auth_config: Dict[str, Any]
    business_logic: List[str]


class UIComponent(BaseModel):
    name: str
    type: str
    fields: List[str]
    actions: List[str]


class APIEndpoint(BaseModel):
    path: str
    method: str
    auth_required: bool
    roles: List[str]
    request_body: Optional[Dict[str, Any]]
    response: Dict[str, Any]


class DBTable(BaseModel):
    name: str
    fields: List[Dict[str, str]]
    relations: List[str]


class AuthRule(BaseModel):
    role: str
    permissions: List[str]


class SchemaResult(BaseModel):
    ui_schema: List[Dict[str, Any]]
    api_schema: List[Dict[str, Any]]
    db_schema: List[Dict[str, Any]]
    auth_schema: List[Dict[str, Any]]


class PipelineResult(BaseModel):
    success: bool
    prompt: str
    stages: Dict[str, Any]
    final_schema: Optional[Dict[str, Any]]
    total_latency_ms: int
    retries: int
    repair_log: List[str]
