# AI App Compiler

A multi-stage pipeline that compiles natural language app descriptions into structured, validated, executable schemas.

## Architecture

```
User Prompt
    ↓
Stage 1: Intent Extractor
    → entities, roles, features, constraints, assumptions
    ↓
Stage 2: Architecture Designer  
    → pages, API endpoints, DB tables, auth config, business logic
    ↓
Stage 3: Schema Generator
    → UI schema, API schema, DB schema, Auth schema
    ↓
Stage 4: Validator + Repair Engine
    → consistency checks, auto-repair, repair log
    ↓
Validated Executable Schema
```

## Why Multi-Stage?

Single prompt = immediate rejection (per spec). Each stage has a specific job:
- **Stage 1** narrows the problem space (intent)
- **Stage 2** designs the solution (architecture)  
- **Stage 3** generates the implementation (schemas)
- **Stage 4** guarantees correctness (validation + repair)

This mirrors how a compiler works: lexing → parsing → semantic analysis → code generation.

## Validation Engine

The validator checks:
1. **Required fields** — every DB table has `id`, every API has `path` and `method`
2. **API↔DB consistency** — API request fields must map to DB columns
3. **UI↔API consistency** — UI data sources must reference real endpoints
4. **Auth consistency** — all roles used in endpoints/pages must be defined

On failure, it calls Gemini to repair only the broken parts (not full retry).

## Setup

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000

## Evaluation

```bash
python evaluate.py
```

Runs 20 test cases (10 real, 10 edge) and outputs metrics to `evaluation_results.json`.

## Cost vs Quality Tradeoffs

| Setting | Latency | Quality | Cost |
|---------|---------|---------|------|
| temperature=0.0 | Fastest | Deterministic but rigid | Lowest |
| temperature=0.1 | Balanced | Consistent, slight variation | Low |
| temperature=0.3 | Slower | More creative schemas | Medium |

The pipeline uses `temperature=0.1` by default — deterministic enough for consistency, flexible enough to handle diverse prompts.

## Failure Handling

- **Vague prompts**: Stage 1 makes reasonable assumptions and documents them in `assumptions[]`
- **Conflicting requirements**: Stage 1 notes conflicts in `constraints[]`  
- **Invalid JSON**: `extract_json()` has multi-strategy parsing (fenced, raw, partial)
- **Schema mismatches**: Stage 4 detects and repairs up to 2 times before returning with warnings
