import re
from urllib.parse import urlparse

from app.schemas import ValidationReport, SourcedClaim

_URL_RE = re.compile(r"https?://[^\s)]+")


def validate_report(report: ValidationReport) -> tuple[ValidationReport, int]:
    stripped = 0

    demand_ok = []
    for claim in report.demand.evidence:
        if _is_valid_source(claim.source_url):
            demand_ok.append(claim)
        else:
            stripped += 1
    report.demand.evidence = demand_ok

    comp_ok = []
    for comp in report.competitors:
        if _is_valid_source(comp.source_url):
            comp_ok.append(comp)
        else:
            stripped += 1
    report.competitors = comp_ok

    basis_ok = []
    for claim in report.market_sizing.basis:
        if _is_valid_source(claim.source_url):
            basis_ok.append(claim)
        else:
            stripped += 1
    report.market_sizing.basis = basis_ok

    plan_issues = _scan_plan_claims(report.business_plan_draft)
    stripped += plan_issues

    report.unresolved_claims_stripped = stripped
    return report, stripped


def _is_valid_source(url: str) -> bool:
    if not _URL_RE.match(url) or len(url) < 12:
        return False
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False
        if parsed.netloc in ("example.com", "placeholder.com", "localhost"):
            return False
        return True
    except Exception:
        return False


def _scan_plan_claims(plan: str) -> int:
    if not plan:
        return 0
    issues = 0
    dollar_amounts = re.findall(r"\$\d[\d,]*[kbm]?", plan, re.I)
    for amount in dollar_amounts:
        if not _has_nearby_source(plan, amount):
            issues += 1
    return issues


def _has_nearby_source(text: str, anchor: str) -> bool:
    idx = text.find(anchor)
    if idx < 0:
        return True
    window = text[max(0, idx - 200): idx + 200].lower()
    return bool(re.search(r"(source|according to|per |data from|reported by)", window))
