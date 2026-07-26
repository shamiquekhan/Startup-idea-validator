from app.schemas import ValidationReport

_VERDICT_LABELS = {
    "build": "Build — clear opportunity, manageable risk",
    "narrow": "Narrow — promising but needs focus on a specific vertical",
    "pivot": "Pivot — problem may exist but approach needs rethinking",
    "abandon": "Abandon — too many red flags",
    "insufficient-info": "Insufficient Info — provide more details before committing",
}

_VERDICT_COLORS = {
    "build": "🟢",
    "narrow": "🟡",
    "pivot": "🟠",
    "abandon": "🔴",
    "insufficient-info": "⚪",
}


def _score_range(ev) -> str:
    scores = [d.score for d in ev.dimensions]
    if not scores:
        return ""
    low_conf = all(d.confidence == "low" for d in ev.dimensions)
    if low_conf:
        return f" (low confidence — true range may be **{min(scores) - 15}–{max(scores) + 15}**)"

    any_low = any(d.confidence == "low" for d in ev.dimensions)
    if any_low:
        return f" (some dimensions low confidence — range **{min(scores) - 10}–{max(scores) + 10}**)"

    return ""


def _dimension_explanation(d) -> str:
    if d.explanation and len(d.explanation) > 5:
        return f" — {d.explanation[:120]}"
    return ""


def render_to_markdown(report: ValidationReport) -> str:
    lines = [
        "# Startup Validation Report\n",
    ]

    if report.evaluation:
        ev = report.evaluation
        verdict_label = _VERDICT_LABELS.get(
            ev.recommendation.verdict,
            ev.recommendation.verdict,
        )
        verdict_color = _VERDICT_COLORS.get(ev.recommendation.verdict, "⚪")
        score_range = _score_range(ev)
        lines.append(f"**Overall Score: {ev.overall_score:.0f}/100**{score_range}\n")
        lines.append(f"**Verdict: {verdict_color} {verdict_label}**\n")
        lines.append(f"{ev.reasoning}\n")
        lines.append("---\n## Evaluation Dimensions\n")
        lines.append("| Dimension | Score | Weight | Confidence | Explanation |\n")
        lines.append("|---|---|---|---|---|\n")
        for d in ev.dimensions:
            lines.append(
                f"| {d.name.replace('_', ' ').title()} | "
                f"{d.score}/100 | {d.weight*100:.0f}% | "
                f"{d.confidence} | {d.explanation[:120]} |\n"
            )

        if ev.recommendation.kill_criteria:
            lines.append("\n**Kill Criteria — conditions that would invalidate this idea:**\n")
            for k in ev.recommendation.kill_criteria:
                lines.append(f"- {k}\n")

        if ev.recommendation.next_steps:
            lines.append("\n**Recommended Next Steps:**\n")
            for i, step in enumerate(ev.recommendation.next_steps, 1):
                lines.append(f"{i}. {step}\n")

        lines.append("---\n")

    lines.extend([
        "## 1. Input Summary\n",
        f"**Problem:** {report.intake.problem_statement}\n",
        f"**Target User:** {report.intake.target_user}\n",
        f"**Proposed Solution:** {report.intake.proposed_solution}\n",
        f"**Category:** {report.intake.category or 'Not specified'}\n",
        f"**Startup Type:** {report.intake.startup_type or 'Not specified'}\n",
        f"**Input Quality:** {report.intake.input_quality}\n",
    ])
    if report.intake.missing_fields:
        lines.append("**Missing from input:** " + ", ".join(report.intake.missing_fields) + "\n")

    if report.intake.target_user in ("not specified", "unknown", ""):
        lines.append("> ⚠ **Customer not specified** — the analysis below cannot evaluate product-market fit without knowing who the customer is.\n\n")

    lines.extend([
        "\n---\n",
        "## 2. Demand Signal Check\n",
        f"**Strength:** {report.demand.strength} ({len(report.demand.evidence)} sources)\n",
    ])
    for i, claim in enumerate(report.demand.evidence[:8], 1):
        lines.append(
            f"{i}. {claim.text[:200]} "
            f"[[source]({claim.source_url})]\n"
        )
    if len(report.demand.evidence) > 8:
        lines.append(f"... and {len(report.demand.evidence) - 8} more\n")

    lines.extend([
        "\n---\n",
        "## 3. Competitor Landscape\n",
    ])
    verified = [c for c in report.competitors if c.is_verified_competitor]
    unverified = [c for c in report.competitors if not c.is_verified_competitor]
    if verified:
        lines.append(f"**Verified competitors ({len(verified)}):**\n")
        for c in verified:
            funding = f" ({c.funding_signal})" if c.funding_signal else ""
            lines.append(f"- {c.name}{funding} [[source]({c.source_url})]\n")
    if unverified:
        lines.append(f"\n*{len(unverified)} other references found (media, directories, etc.)*\n")
    if not report.competitors:
        lines.append("*No direct competitors identified from web search.*\n")

    lines.extend([
        "\n---\n",
        "## 4. Market Sizing (Directional)\n",
        f"{report.market_sizing.estimate_summary}\n",
        f"**Confidence:** {report.market_sizing.confidence}\n",
        f"**Sources:** {len(report.market_sizing.basis)}\n",
    ])

    lines.extend([
        "\n---\n",
        "## 5. Risk Flags\n",
    ])
    for r in report.risks:
        lines.append(f"- {r}\n")
    if not report.risks:
        lines.append("*No significant risks flagged.*\n")

    lines.extend([
        "\n---\n",
        "## 6. Business Plan Draft\n",
        report.business_plan_draft,
        "\n",
    ])

    if report.unresolved_claims_stripped > 0:
        lines.extend([
            "\n---\n",
            "## Validation Note\n",
            f"{report.unresolved_claims_stripped} unsupported claim(s) were "
            "removed by the automated validator.\n",
        ])

    return "".join(lines)
