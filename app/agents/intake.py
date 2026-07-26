import json
import re
from app.model_config import get_llm_with_fallback as get_llm
from app.schemas import IntakeResult, StartupType

_INTAKE_PROMPT = """You are a startup idea analyst. Extract structured fields from a raw idea description.

Return ONLY valid JSON with these keys:
- problem_statement: the core problem being solved (1 sentence)
- target_user: who experiences this problem ("not specified" if unclear)
- proposed_solution: what the idea builds (1 sentence)
- category: best-fit industry category. Use "deeptech" for scientific/technical R&D (materials, chemistry, physics, biology R&D tools). Use "cleantech" for energy generation, storage, or grid software. Use "fintech", "healthtech", "saas", "biotech", "edtech", "ecommerce" etc. as appropriate.
- startup_type: one of ["deep-tech", "enterprise-saas", "smb-saas", "marketplace", "ecommerce", "consumer-app", "hardware", "biotech", "fintech", "cleantech", "healthtech", "legaltech", "edtech", "insurtech", "proptech", "agtech", "developer-tools", "other"]
- input_quality: "good" if the idea describes customer + problem + solution, "fair" if two of three, "poor" if fewer
- missing_fields: list of what's missing from ["customer", "problem", "solution", "differentiation", "business-model"]

Raw idea: {raw_idea}
JSON:"""


def parse_intake(raw_idea: str, model: str = "qwen3:1.7b") -> IntakeResult:
    if not raw_idea or len(raw_idea.strip()) < 15:
        return _build_poor_input(raw_idea)

    try:
        llm = get_llm(model=model, temperature=0.1, num_predict=512)
        response = llm.invoke(_INTAKE_PROMPT.format(raw_idea=raw_idea))
        text = response.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)

        category = data.get("category")
        startup_type = _validate_type(data.get("startup_type", "other"))

        lower = raw_idea.lower()
        deep_tech_keywords = {"material", "discovery", "molecule", "compound", "chemical", "scientific", "r&d", "research",
                               "discovering", "formula", "alloy", "polymer", "catalyst", "prote in", "genom", "drug"}
        if any(kw in lower for kw in deep_tech_keywords):
            if category in ("cleantech", "energy", "saas"):
                category = "deeptech"
            startup_type = "deep-tech"

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
        return _keyword_fallback(raw_idea)


def _validate_type(t: str) -> StartupType:
    valid = {
        "deep-tech", "enterprise-saas", "smb-saas", "marketplace",
        "ecommerce", "consumer-app", "hardware", "biotech",
        "fintech", "cleantech", "healthtech",
        "legaltech", "edtech", "insurtech", "proptech", "agtech",
        "developer-tools", "other",
    }
    if t in valid:
        return t
    if t in ("deeptech",):
        return "deep-tech"
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


_TYPE_KEYWORDS: dict[StartupType, list[str]] = {
    "deep-tech": ["material", "discovery", "quantum", "robot", "scientific", "r&d", "research lab", "dft", "simulation"],
    "enterprise-saas": ["enterprise", "b2b", "workflow", "dashboard", "analytics", "compliance", "procurement"],
    "smb-saas": ["freelancer", "small business", "micro", "solo", "independent"],
    "marketplace": ["marketplace", "platform connecting", "find", "match", "network"],
    "fintech": ["fintech", "bank", "payment", "invoice", "expense", "crypto", "blockchain", "insurtech"],
    "healthtech": ["health", "medical", "clinical", "wellness", "patient", "healthcare"],
    "legaltech": ["legal", "lawyer", "attorney", "court", "compliance", "contract", "regulatory"],
    "edtech": ["education", "learning", "course", "student", "teacher", "classroom", "training"],
    "insurtech": ["insurance", "underwriting", "claim", "policy"],
    "proptech": ["real estate", "property", "rental", "mortgage", "tenant"],
    "agtech": ["agriculture", "farm", "crop", "precision agriculture", "agtech", "agri", "drone farming", "soil"],
    "cleantech": ["energy", "carbon", "climate", "solar", "battery", "decarbon", "sustainable", "renewable"],
    "biotech": ["biotech", "drug", "protein", "genomic", "therapeutic", "diagnostic"],
    "hardware": ["hardware", "device", "sensor", "iot", "physical"],
    "consumer-app": ["social", "connect", "share", "fun", "entertainment"],
    "ecommerce": ["shop", "store", "retail", "brand", "product"],
    "developer-tools": ["developer", "api", "sdk", "cli", "open source", "devtool"],
}


def _keyword_fallback(raw_idea: str) -> IntakeResult:
    lower = raw_idea.lower()
    startup_type: StartupType = "other"
    for st, keywords in _TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            startup_type = st
            break

    problem = raw_idea
    target = "not specified"
    solution = raw_idea
    missing = ["customer", "differentiation", "business-model"]

    if " for " in lower:
        parts = raw_idea.split(" for ", 1)
        solution = parts[0].strip()
        target = parts[1].strip().rstrip(".")
        if target and target != "not specified":
            missing.remove("customer") if "customer" in missing else None
    if " that " in lower:
        missing.remove("problem") if "problem" in missing else None

    return IntakeResult(
        problem_statement=problem,
        target_user=target,
        proposed_solution=solution,
        category=startup_type if startup_type != "other" else None,
        startup_type=startup_type,
        raw_idea=raw_idea,
        input_quality="poor" if len(missing) > 2 else "fair",
        missing_fields=missing,
    )
