from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import time
import json

from stages.stage1_intent import extract_intent
from stages.stage2_architecture import design_architecture
from stages.stage3_schema import generate_schemas
from stages.stage4_validator import validate_and_repair
from models.schemas import PipelineResult, PipelineRequest

app = FastAPI(title="AI App Compiler", description="Natural language to app schema compiler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    import os
    path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(path, encoding="utf-8") as f:
        return f.read()

@app.post("/compile", response_model=PipelineResult)
async def compile_app(request: PipelineRequest):
    start_time = time.time()
    stages = {}
    retries = 0

    try:
        # Stage 1: Intent Extraction
        t1 = time.time()
        intent = await extract_intent(request.prompt)
        stages["stage1_intent"] = {
            "result": intent,
            "latency_ms": round((time.time() - t1) * 1000)
        }

        # Stage 2: Architecture Design
        t2 = time.time()
        architecture = await design_architecture(intent)
        stages["stage2_architecture"] = {
            "result": architecture,
            "latency_ms": round((time.time() - t2) * 1000)
        }

        # Stage 3: Schema Generation
        t3 = time.time()
        schemas = await generate_schemas(intent, architecture)
        stages["stage3_schemas"] = {
            "result": schemas,
            "latency_ms": round((time.time() - t3) * 1000)
        }

        # Stage 4: Validation + Repair
        t4 = time.time()
        validated, repair_log, stage_retries = await validate_and_repair(schemas, architecture)
        retries += stage_retries
        stages["stage4_validated"] = {
            "result": validated,
            "repair_log": repair_log,
            "latency_ms": round((time.time() - t4) * 1000)
        }

        total_latency = round((time.time() - start_time) * 1000)

        return PipelineResult(
            success=True,
            prompt=request.prompt,
            stages=stages,
            final_schema=validated,
            total_latency_ms=total_latency,
            retries=retries,
            repair_log=repair_log
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "service": "AI App Compiler"}

app.mount("/static", StaticFiles(directory="static"), name="static")
