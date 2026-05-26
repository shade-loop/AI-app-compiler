"""
Evaluation Framework for AI App Compiler
Run: python evaluate.py
"""
import asyncio
import json
import time
from typing import List, Dict, Any

from stages.stage1_intent import extract_intent
from stages.stage2_architecture import design_architecture
from stages.stage3_schema import generate_schemas
from stages.stage4_validator import validate_and_repair

# 10 Real product prompts
REAL_PROMPTS = [
    "Build a CRM with login, contacts, dashboard, role-based access for admin and sales, deal pipeline, email tracking, and premium plan with Stripe payments.",
    "Build an e-commerce store with product catalog, shopping cart, Stripe checkout, order tracking, admin dashboard, and customer accounts.",
    "Build a project management tool with boards, lists, cards, team collaboration, due dates, file attachments, and role-based access.",
    "Build a healthcare patient portal with appointment booking, medical records, prescription tracking, doctor messaging, and role access for patients/doctors/admin.",
    "Build a learning management system with courses, video lessons, quizzes, progress tracking, certificates, and role access for students, instructors, admin.",
    "Build a real estate listing platform with property listings, search filters, agent profiles, inquiry forms, and admin moderation.",
    "Build a SaaS analytics dashboard with multi-tenant support, data visualization, CSV export, API key management, and billing.",
    "Build a food delivery app with restaurant listings, menu management, cart, order tracking, delivery driver interface, and customer ratings.",
    "Build an HR management system with employee profiles, leave management, payroll, performance reviews, and role access for HR, manager, employee.",
    "Build a social media platform with user profiles, posts, comments, likes, follow system, notifications, and content moderation.",
]

# 10 Edge cases (vague, conflicting, incomplete)
EDGE_PROMPTS = [
    "make an app",  # Extremely vague
    "build something for my business with users",  # Vague
    "I need a website with login and also no login but admin can see everything and users can't see admin but admin can see users and also payments but free",  # Conflicting
    "Build an app with a dashboard",  # Minimal
    "Create a platform for managing things with different access levels",  # Abstract
    "Build a CRM but also an e-commerce but also a social network all in one",  # Overloaded
    "Build an app with 500 user types and every user can do everything except what they can't",  # Contradictory
    "",  # Empty - should handle gracefully... we'll skip this
    "Build a todo app",  # Simple but valid
    "Build an enterprise-grade, HIPAA-compliant, multi-tenant, AI-powered, blockchain-verified, quantum-encrypted patient management system with real-time collaboration",  # Buzzword overload
]


async def evaluate_single(prompt: str, label: str) -> Dict[str, Any]:
    if not prompt.strip():
        return {"label": label, "prompt": prompt, "success": False, "error": "Empty prompt", "latency_ms": 0, "retries": 0}

    start = time.time()
    try:
        intent = await extract_intent(prompt)
        architecture = await design_architecture(intent)
        schemas = await generate_schemas(intent, architecture)
        validated, repair_log, retries = await validate_and_repair(schemas, architecture)

        latency = round((time.time() - start) * 1000)

        # Quality checks
        api_count = len(validated.get("api_schema", []))
        db_count = len(validated.get("db_schema", []))
        ui_count = len(validated.get("ui_schema", []))
        auth_count = len(validated.get("auth_schema", []))

        success = all([
            api_count > 0,
            db_count > 0,
            ui_count > 0,
            auth_count > 0,
            len(intent.get("entities", [])) > 0,
            len(intent.get("roles", [])) > 0,
        ])

        return {
            "label": label,
            "prompt": prompt[:80] + "..." if len(prompt) > 80 else prompt,
            "success": success,
            "latency_ms": latency,
            "retries": retries,
            "repair_log": repair_log,
            "metrics": {
                "api_endpoints": api_count,
                "db_tables": db_count,
                "ui_pages": ui_count,
                "auth_roles": auth_count,
                "entities": len(intent.get("entities", [])),
                "assumptions": len(intent.get("assumptions", [])),
            }
        }
    except Exception as e:
        return {
            "label": label,
            "prompt": prompt[:80],
            "success": False,
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000),
            "retries": 0,
        }


async def run_evaluation(subset: int = 5):
    """Run evaluation on a subset to avoid quota issues"""
    print(f"\n{'='*60}")
    print("AI APP COMPILER — EVALUATION FRAMEWORK")
    print(f"{'='*60}\n")

    results = []

    # Real prompts
    print("📋 Running REAL product prompts...")
    for i, prompt in enumerate(REAL_PROMPTS[:subset]):
        print(f"  [{i+1}/{subset}] Testing: {prompt[:60]}...")
        result = await evaluate_single(prompt, f"real_{i+1}")
        results.append(result)
        status = "✅" if result["success"] else "❌"
        print(f"    {status} {result.get('latency_ms', 0)}ms | retries: {result.get('retries', 0)} | {result.get('error', '')}")
        await asyncio.sleep(2)  # Rate limit protection

    # Edge cases
    print(f"\n⚠️  Running EDGE CASE prompts...")
    for i, prompt in enumerate(EDGE_PROMPTS[:subset]):
        if not prompt.strip():
            continue
        print(f"  [{i+1}/{subset}] Testing: {prompt[:60]}...")
        result = await evaluate_single(prompt, f"edge_{i+1}")
        results.append(result)
        status = "✅" if result["success"] else "❌"
        print(f"    {status} {result.get('latency_ms', 0)}ms | retries: {result.get('retries', 0)} | {result.get('error', '')}")
        await asyncio.sleep(2)

    # Summary
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    avg_latency = sum(r.get("latency_ms", 0) for r in results) / len(results) if results else 0
    total_retries = sum(r.get("retries", 0) for r in results)

    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total tested:    {len(results)}")
    print(f"Success rate:    {len(successful)}/{len(results)} ({100*len(successful)//len(results)}%)")
    print(f"Avg latency:     {avg_latency:.0f}ms")
    print(f"Total retries:   {total_retries}")
    print(f"Repair rate:     {100*total_retries//len(results)}%")

    if failed:
        print(f"\nFailed cases:")
        for r in failed:
            print(f"  - {r['label']}: {r.get('error', 'unknown')}")

    # Save results
    with open("evaluation_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": len(results),
                "success_rate": f"{100*len(successful)//len(results)}%",
                "avg_latency_ms": round(avg_latency),
                "total_retries": total_retries,
            },
            "results": results
        }, f, indent=2)

    print(f"\nFull results saved to evaluation_results.json")
    return results


if __name__ == "__main__":
    asyncio.run(run_evaluation(subset=3))  # Run 3 of each to save quota
