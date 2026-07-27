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
    ("deep-tech", [
        "materials", "discovery", "molecule", "compound", "chemical",
        "scientific", "r&d", "research lab", "dft", "simulation",
        "quantum", "protein folding", "genomics", "drug discovery",
        "battery chemistry", "catalyst", "fusion", "radiation-resistant",
        "solid-state battery", "graph neural network", "active learning",
        "materials screening", "protein-ligand", "binding affinity",
        "semiconductor", "chip layout", "manufacturing yield",
        "orbital", "microgravity", "space manufacturing",
    ]),
    ("sales-tech", [
        "sales", "crm", "outreach", "pipeline", "prospect", "demo",
        "revenue ops", "revops", "sdr", "lead generation", "cold email",
        "sales engagement", "sales copilot", "sales assistant",
        "account executive", "sales rep", "sales team", "recruiting",
        "screen resumes", "coding tests", "employee success",
    ]),
    ("revops", [
        "revenue operations", "rev ops", "revenue intelligence",
        "quote-to-cash", "cpq", "revenue reporting",
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
        "mental health", "therapy", "anxiety", "depression",
        "emotional support", "cbt", "therapy sessions",
        "dental", "dentist", "dental clinic",
    ]),
    ("cleantech", [
        "energy", "carbon", "climate", "solar", "battery storage",
        "decarbon", "sustainable", "renewable", "emissions",
        "carbon emissions", "carbon accounting", "smart city",
        "traffic", "traffic light", "traffic camera", "sensor data",
        "grid", "power grid",
    ]),
    ("marketplace", [
        "marketplace", "platform connecting",
        "two-sided marketplace", "rent", "peer-to-peer", "p2p",
        "freelancer", "connects", "on demand",
        "rent out", "renting", "hourly rental",
    ]),
    ("ecommerce", [
        "shop", "store", "retail", "brand", "product",
        "ecommerce", "d2c", "fashion", "clothing", "wardrobe",
        "outfit", "stylist",
    ]),
    ("biotech", [
        "biotech", "drug", "protein", "genomic", "therapeutic",
        "diagnostic", "assay", "pharmaceutical", "laboratory",
        "clinical trial", "molecular",
    ]),
    ("edtech", [
        "education", "online learning", "e-learning", "course",
        "student", "teacher", "classroom", "training", "lms",
        "tutor", "lesson", "educational",
    ]),
    ("proptech", [
        "real estate", "property", "rental", "mortgage", "tenant",
        "house", "home",
    ]),
    ("insurtech", [
        "insurance", "underwriting", "claim", "policy",
    ]),
    ("agtech", [
        "agriculture", "farm", "crop", "precision agriculture",
        "agtech", "agri", "soil", "irrigation", "fertilizer",
        "disease detection", "satellite imagery",
    ]),
    ("hardware", [
        "hardware", "device", "sensor", "iot", "physical product",
        "drone", "robot", "robotic", "autonomous", "kitchen",
        "factory", "drone delivery", "aerial", "construction",
        "drone and ai", "bim", "building information",
    ]),
    ("developer-tools", [
        "developer", "api", "sdk", "cli", "open source", "devtool",
        "developer experience", "code review", "vulnerability",
        "pull request", "deploy", "ci/cd", "security scan",
        "secure fix", "semiconductor", "chip",
    ]),
    ("enterprise-saas", [
        "enterprise", "b2b", "workflow", "dashboard", "analytics",
        "compliance", "procurement", "saas", "grant",
        "grant proposal", "grant writing", "funding opportunity",
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

    # Pass 1: rule-based classification (fast, deterministic)
    rule_type = _rule_classify(raw_idea)

    # Pass 2: LLM extraction for problem_statement, target_user, etc.
    # Only use LLM for field extraction; startup_type comes from rules
    try:
        llm = get_llm(model=model, temperature=0.1, num_predict=512)
        response = llm.invoke(_INTAKE_PROMPT.format(raw_idea=raw_idea))
        text = response.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)

        return IntakeResult(
            problem_statement=data.get("problem_statement", raw_idea),
            target_user=data.get("target_user", "not specified"),
            proposed_solution=data.get("proposed_solution", raw_idea),
            category=rule_type if rule_type else data.get("category"),
            startup_type=rule_type if rule_type else _validate_type(data.get("startup_type", "other")),
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
