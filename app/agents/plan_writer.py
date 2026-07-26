import json
import re
from langchain_ollama import ChatOllama
from app.schemas import ValidationReport

_PLAN_WRITER_PROMPT = """You are a business plan writer. Draft a concise one-page business plan based ONLY on the validated evidence below.

CRITICAL RULES:
1. You may NOT introduce any new facts, numbers, competitors, or claims not present in the evidence. If the evidence is thin, say so rather than inventing.
2. If the target user is "not specified" or "unknown", write "Customer not specified" in the Target section — do NOT guess or fabricate customer types.
3. Do NOT reference unrelated industries. If the evidence is about materials discovery, do not mention utilities or grid operators.
4. The go-to-market suggestion must only reference customer types found in the evidence. If none are known, write "Not enough information to identify first customers."

Validated Evidence (JSON):
{evidence_json}

Write the plan with these sections:
1. Problem & Target User
2. Solution
3. Market & Competitive Position
4. Go-to-Market Suggestion
5. Key Risks
6. Next Validation Steps

Format in clean Markdown."""


async def draft_business_plan(report: ValidationReport, model: str = "qwen3:1.7b") -> str:
    evidence = _build_evidence_dict(report)
    evidence_json = json.dumps(evidence, indent=2, default=str)

    try:
        llm = ChatOllama(model=model, temperature=0.3, num_predict=2048)
        response = llm.invoke(_PLAN_WRITER_PROMPT.format(evidence_json=evidence_json))
        text = response.content.strip()
        text = re.sub(r"^```(?:markdown)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text
    except Exception:
        return _fallback_plan(report)


def _build_evidence_dict(report: ValidationReport) -> dict:
    return {
        "problem": report.intake.problem_statement,
        "target_user": report.intake.target_user,
        "solution": report.intake.proposed_solution,
        "category": report.intake.category,
        "missing_fields": report.intake.missing_fields,
        "demand_strength": report.demand.strength,
        "demand_evidence_count": len(report.demand.evidence),
        "competitors": [
            {"name": c.name, "description": c.description}
            for c in report.competitors
        ],
        "market_sizing": report.market_sizing.estimate_summary,
        "risks": report.risks,
        "viability_score": report.viability.score,
    }


def _fallback_plan(report: ValidationReport) -> str:
    comps = "\n".join(f"- {c.name}: {c.description}" for c in report.competitors[:3])
    risks = "\n".join(f"- {r}" for r in report.risks)

    target = report.intake.target_user
    if target in ("not specified", "unknown", ""):
        target = "**Not specified** — customer discovery needed before targeting can begin"

    target_line = f"**Target:** {target}"
    gtm = ("**Go-to-Market:** Not enough information to identify first customers. "
           "Customer interviews are the next step.") if "not specified" in str(target).lower() else (
        f"Likely first customers include {target} directly. "
        f"Consider starting with a niche vertical to prove traction before expanding."
    )

    return (
        f"## Problem & Target User\n{report.intake.problem_statement}\n"
        f"{target_line}\n\n"
        f"## Solution\n{report.intake.proposed_solution}\n\n"
        f"## Market & Competitive Position\n"
        f"Demand signal: {report.demand.strength} "
        f"({len(report.demand.evidence)} sources found).\n"
        f"Competitors:\n{comps}\n\n"
        f"Market sizing: {report.market_sizing.estimate_summary}\n\n"
        f"## Go-to-Market Suggestion\n{gtm}\n\n"
        f"## Key Risks\n{risks}\n\n"
        f"## Next Validation Steps\n"
        f"1. Interview potential customers to validate the problem\n"
        f"2. Run a landing page test to gauge interest\n"
        f"3. Build an MVP and test with early users"
    )
