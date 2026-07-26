"""Idea parser — classifies startup type using rule-based + LLM two-pass."""

import json
import re
from app.model_config import get_llm_with_fallback as get_llm
from app.schemas import IntakeResult, StartupType

# Rule-based classification: ordered by specificity (first match wins).
# Each entry has a list of keyword patterns and the startup_type to assign.
# "sales-tech" comes before "enterprise-saas" because sales-tech is a specific
# subdomain that would otherwise match enterprise-saas broadly.
_RULES: list[tuple[StartupType, list[str]]] = [
    ("sales-tech", [
        "sales", "crm", "outreach", "pipeline", "prospect", "demo",
        "revenue ops", "revops", "sdr", "lead generation", "cold email",
        "sales engagement", "sales copilot", "sales assistant",
        "account executive", "sales rep", "sales team",
    ]),
    ("revops", [
        "revenue operations", "rev ops", "revenue intelligence",
        "quote-to-cash", "cpq", "revenue reporting",
    ]),
    ("deep-tech", [
        "materials", "discovery", "molecule", "compound", "chemical",
        "scientific", "r&d", "research lab", "dft", "simulation",
        "quantum", "protein folding", "genomics", "drug discovery",
        "battery chemistry", "catalyst",
    ]),
    ("legaltech", [
        "legal", "lawyer", "attorney", "court", "compliance",
        "contract review", "legal document", "case management",
        "law firm", "legal research",
    ]),
    ("fintech", [
        "fintech", "bank", "payment", "invoice", "expense",
        "crypto", "blockchain", "insurtech", "lending", "credit",
    ]),
    ("healthtech", [
        "health", "medical", "clinical", "wellness", "patient",
        "healthcare", "hospital", "telemedic", "ehr", "hipaa",
    ]),
    ("cleantech", [
        "energy", "carbon", "climate", "solar", "battery storage",
        "decarbon", "sustainable", "renewable", "emissions",
    ]),
    ("biotech", [
        "biotech", "drug", "protein", "genomic", "therapeutic",
        "diagnostic", "lab", "assay",
    ]),
    ("edtech", [
        "education", "learning", "course", "student", "teacher",
        "classroom", "training", "lms",
    ]),
    ("insurtech", [
        "insurance", "underwriting", "claim", "policy",
    ]),
    ("proptech", [
        "real estate", "property", "rental", "mortgage", "tenant",
    ]),
    ("agtech", [
        "agriculture", "farm", "crop", "precision agriculture",
        "agtech", "agri", "soil",
    ]),
    ("hardware", [
        "hardware", "device", "sensor", "iot", "physical product",
    ]),
    ("developer-tools", [
        "developer", "api", "sdk", "cli", "open source", "devtool",
        "developer experience",
    ]),
    ("marketplace", [
        "marketplace", "platform connecting", "find", "match",
        "network", "two-sided",
    ]),
    ("ecommerce", [
        "shop", "store", "retail", "brand", "product",
        "ecommerce", "d2c",
    ]),
    ("consumer-app", [
        "social", "connect", "share", "fun", "entertainment",
        "consumer app", "mobile app",
    ]),
    ("enterprise-saas", [
        "enterprise", "b2b", "workflow", "dashboard", "analytics",
        "compliance", "procurement", "saas",
    ]),
    ("smb-saas", [
        "freelancer", "small business", "micro", "solo",
        "independent", "smb",
    ]),
]


def _rule_classify(text: str) -> StartupType | None:
    lower = text.lower()
    for startup_type, keywords in _RULES:
        for kw in keywords:
            if kw in lower:
                return startup_type
    return None


_INTAKE_PROMPT = """You are a startup idea analyst. Extract structured fields from a raw idea description.

Return ONLY valid JSON with these keys:
- problem_statement: the core problem being solved (1 sentence)
- target_user: who experiences this problem ("not specified" if unclear)
- proposed_solution: what the idea builds (1 sentence)
- category: best-fit industry category. Use typical industry names (e.g. "sales-tech", "legaltech", "fintech", "deeptech", "healthtech", "saas", "cleantech", "biotech", "edtech", "ecommerce", "marketplace", "consumer", "developer-tools", etc.)
- input_quality: "good" if the idea describes customer + problem + solution, "fair" if two of three, "poor" if fewer
- missing_fields: list of what's missing from ["customer", "problem", "solution", "differentiation", "business-model"]

Raw idea: {raw_idea}
JSON:"""


def parse_intake(raw_idea: str, model: str = "qwen3:1.7b") -> IntakeResult:
    if not raw_idea or len(raw_idea.strip()) < 15:
        return _build_poor_input(raw_idea)

    # Pass 1: rule-based classification
    rule_type = _rule_classify(raw_idea)

    try:
        llm = get_llm(model=model, temperature=0.1, num_predict=512)
        response = llm.invoke(_INTAKE_PROMPT.format(raw_idea=raw_idea))
        text = response.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)

        category = data.get("category")
        llm_type = _validate_type(data.get("startup_type", "other"))

        # Prefer rule-based type over LLM type (rules are more precise)
        startup_type = rule_type if rule_type else llm_type

        return IntakeResult(
            problem_statement=data.get("problem_statement", raw_idea),
            target_user=data.get("target_user", "not specified"),
            proposed_solution=data.get("proposed_solution", raw_idea),
            category=category,
            startup_type=startup_type,
            raw_idea=raw_idea,
            input_quality=data.get("input_quality", "fair"),
            missing_fields=data.get("missing_fields", []),
        )
    except Exception:
        return _keyword_fallback(raw_idea, rule_type)


def _validate_type(t: str) -> StartupType:
    valid = {
        "deep-tech", "enterprise-saas", "smb-saas", "marketplace",
        "ecommerce", "consumer-app", "hardware", "biotech",
        "fintech", "cleantech", "healthtech",
        "legaltech", "edtech", "insurtech", "proptech", "agtech",
        "developer-tools", "sales-tech", "revops", "other",
    }
    if t in valid:
        return t
    if t in ("deeptech",):
        return "deep-tech"
    if t in ("sales tech", "salestech", "sales"):
        return "sales-tech"
    return "other"


def _build_poor_input(raw: str) -> IntakeResult:
    return IntakeResult(
        problem_statement=raw if raw else "not enough detail provided",
        target_user="not specified",
        proposed_solution=raw if raw else "not specified",
        category=None,
        startup_type="other",
        raw_idea=raw,
        input_quality="poor",
        missing_fields=["customer", "problem", "solution", "differentiation"],
    )


def _keyword_fallback(raw_idea: str, rule_type: StartupType | None = None) -> IntakeResult:
    lower = raw_idea.lower()
    startup_type = rule_type if rule_type else _rule_classify(raw_idea) or "other"

    problem = raw_idea
    target = "not specified"
    solution = raw_idea
    missing = ["customer", "differentiation", "business-model"]

    if " for " in lower:
        parts = raw_idea.split(" for ", 1)
        solution = parts[0].strip()
        target = parts[1].strip().rstrip(".")
        if target and target != "not specified":
            if "customer" in missing:
                missing.remove("customer")
    if " that " in lower:
        if "problem" in missing:
            missing.remove("problem")

    category = startup_type if startup_type != "other" else None

    return IntakeResult(
        problem_statement=problem,
        target_user=target,
        proposed_solution=solution,
        category=category,
        startup_type=startup_type,
        raw_idea=raw_idea,
        input_quality="poor" if len(missing) > 2 else "fair",
        missing_fields=missing,
    )
