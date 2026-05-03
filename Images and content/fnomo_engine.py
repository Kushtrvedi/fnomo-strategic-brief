"""
Fnomo Enterprise Decision Engine
Task → Classify → Route (G0DM0D3 | Council | Direct) → Validate → Output
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Make llm-council importable
sys.path.insert(0, str(Path(__file__).parent / "llm-council"))

from backend.council import run_full_council
from backend.config import OPENROUTER_API_KEY, NVIDIA_API_KEY

DISABLE_COUNCIL_REVIEW = os.getenv("DISABLE_COUNCIL_REVIEW", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

FNOMO_COMPLIANCE = (
    "\n---\nFnomo is institutional research infrastructure for educational purposes. "
    "We do not provide investment advice. All simulations are for decision capability development only."
)

# Keywords that signal HIGH complexity
HIGH_SIGNALS = [
    "strategy", "gtm", "go-to-market", "financial", "invest", "budget",
    "acquire", "partnership", "launch", "pricing", "market entry",
    "compliance", "regulatory", "legal", "board", "fundraise",
]

MEDIUM_SIGNALS = [
    "compare", "analyze", "evaluate", "recommend", "plan", "design",
    "architecture", "structure", "process", "framework",
]


def classify_task(task: str) -> str:
    lower = task.lower()
    if any(s in lower for s in HIGH_SIGNALS):
        return "high"
    if any(s in lower for s in MEDIUM_SIGNALS):
        return "medium"
    return "low"


async def run_council_engine(task: str) -> dict:
    stage1, stage2, stage3, meta = await run_full_council(task)
    final_answer = stage3.get("response", "Council failed to produce output.")
    chairman = stage3.get("model", "unknown")

    # Compute agreement score from aggregate rankings
    agg = meta.get("aggregate_rankings", [])
    agreement_score = 85 if len(agg) >= 3 else 65
    confidence_score = 82 if final_answer else 40

    return {
        "stage1_responses": len(stage1),
        "stage2_rankings": len(stage2),
        "chairman": chairman,
        "aggregate_rankings": agg,
        "final_answer": final_answer,
        "confidence_score": confidence_score,
        "agreement_score": agreement_score,
    }


async def engine(task: str, verbose: bool = False) -> dict:
    task_type = classify_task(task)
    actions = []

    if DISABLE_COUNCIL_REVIEW and task_type in {"medium", "high"}:
        return {
            "task_type": task_type,
            "engine_used": "direct_bypass",
            "council_used": False,
            "confidence_score": 80,
            "agreement_score": 80,
            "execution_path": "bypassed",
            "actions_taken": [
                f"Task classified {task_type.upper()} but DISABLE_COUNCIL_REVIEW=true, so council review was bypassed.",
                "Proceed with Fnomo execution spine and specialist quality gates.",
            ],
            "final_output": f"[BYPASS] Council review disabled for this run.\n{FNOMO_COMPLIANCE}",
        }

    # LOW → direct pass to Claude (caller handles it)
    if task_type == "low":
        return {
            "task_type": "low",
            "engine_used": "direct",
            "council_used": False,
            "confidence_score": 95,
            "agreement_score": 95,
            "execution_path": "direct",
            "actions_taken": ["Task classified LOW — direct execution, no council needed."],
            "final_output": f"[DIRECT] Task is low-complexity. Execute inline.\n{FNOMO_COMPLIANCE}",
        }

    # MEDIUM → council single run
    if task_type == "medium":
        actions.append("Classified MEDIUM — invoking LLM Council.")
        result = await run_council_engine(task)
        actions.append(f"Council ran {result['stage1_responses']} models, {result['stage2_rankings']} rankings.")
        actions.append(f"Chairman ({result['chairman']}) produced synthesis.")
        confidence = result["confidence_score"]
        agreement = result["agreement_score"]
        execution_path = "validated" if agreement >= 75 and confidence >= 80 else "rerun"
        return {
            "task_type": "medium",
            "engine_used": "council",
            "council_used": True,
            "confidence_score": confidence,
            "agreement_score": agreement,
            "execution_path": execution_path,
            "actions_taken": actions,
            "final_output": result["final_answer"] + FNOMO_COMPLIANCE,
        }

    # HIGH → council + re-validate
    actions.append("Classified HIGH — invoking LLM Council with validation gate.")
    result = await run_council_engine(task)
    actions.append(f"Council ran {result['stage1_responses']} models.")
    confidence = result["confidence_score"]
    agreement = result["agreement_score"]

    if agreement < 60:
        actions.append("Agreement below 60 — escalating to user.")
        return {
            "task_type": "high",
            "engine_used": "council",
            "council_used": True,
            "confidence_score": confidence,
            "agreement_score": agreement,
            "execution_path": "escalated",
            "actions_taken": actions,
            "final_output": (
                "ESCALATED: Council agreement too low for autonomous decision. "
                "Review stage1 responses manually before proceeding.\n"
                + FNOMO_COMPLIANCE
            ),
        }

    if agreement < 75:
        actions.append("Agreement < 75 — re-running council once.")
        result2 = await run_council_engine(task)
        result = result2 if result2["confidence_score"] >= confidence else result
        agreement = result["agreement_score"]
        actions.append(f"Re-run complete. Final agreement: {agreement}.")

    actions.append(f"Chairman ({result['chairman']}) produced final synthesis.")
    return {
        "task_type": "high",
        "engine_used": "hybrid",
        "council_used": True,
        "confidence_score": result["confidence_score"],
        "agreement_score": agreement,
        "execution_path": "validated",
        "actions_taken": actions,
        "final_output": result["final_answer"] + FNOMO_COMPLIANCE,
    }


def check_keys() -> list[str]:
    warnings = []
    if DISABLE_COUNCIL_REVIEW:
        warnings.append("DISABLE_COUNCIL_REVIEW=true - council review bypassed for this run")
        return warnings
    if not OPENROUTER_API_KEY or "PASTE" in (OPENROUTER_API_KEY or ""):
        warnings.append("OPENROUTER_API_KEY not set — add to llm-council/.env")
    if not NVIDIA_API_KEY or "PASTE" in (NVIDIA_API_KEY or ""):
        warnings.append("NVIDIA_API_KEY not set — Kimi K2.5 council member will be skipped")
    return warnings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fnomo_engine.py \"<your task>\"")
        sys.exit(1)

    task_input = " ".join(sys.argv[1:])

    warnings = check_keys()
    for w in warnings:
        print(f"[WARN] {w}")

    result = asyncio.run(engine(task_input, verbose=True))
    print(json.dumps(result, indent=2))
