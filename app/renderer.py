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


def render_to_markdown(report: ValidationReport) -> str:
    lines = ["# Startup Validation Report\n"]

    if report.evaluation:
        ev = report.evaluation
        verdict_label = _VERDICT_LABELS.get(ev.recommendation.verdict, ev.recommendation.verdict)
        verdict_color = _VERDICT_COLORS.get(ev.recommendation.verdict, "⚪")
        score_range = _score_range(ev)
        lines.append(f"**Overall Score: {ev.overall_score:.0f}/100**{score_range}\n")
        lines.append(f"**Verdict: {verdict_color} {verdict_label}**\n")
        lines.append(f"{ev.reasoning}\n")

        ds = report.decision_support
        if ds and ds.score_breakdown:
            lines.append("\n**Score Breakdown:**\n")
            lines.append("| Action | Points | Reason |\n")
            lines.append("|---|---|---|\n")
            total = 100
            for item in ds.score_breakdown:
                if item.action == "subtract":
                    total -= item.points
                    op = "−"
                else:
                    total += item.points
                    op = "+"
                lines.append(f"| {item.action.title()} | {op}{item.points} | {item.reason} |\n")
            lines.append(f"| **Final** | **{total}** | |\n")

        if ds and ds.why_now:
            lines.append(f"\n**Why Now?** {ds.why_now}\n")

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

        if ds:
            if ds.moat_factors:
                lines.append("\n---\n## Moat Analysis\n")
                lines.append("| Factor | Status | Explanation |\n")
                lines.append("|---|---|---|\n")
                for m in ds.moat_factors:
                    status_icon = {"confirmed": "✅", "likely": "🟡", "unknown": "⚪", "negative_evidence": "🔴"}
                    icon = status_icon.get(m.status, "⚪")
                    lines.append(f"| {m.name.replace('_', ' ').title()} | {icon} {m.status.replace('_', ' ').title()} | {m.explanation[:120]} |\n")

            if ds.differentiation_answer:
                lines.append(f"\n**Why buy from you?** {ds.differentiation_answer}\n")

            if ds.customer_segments:
                lines.append("\n---\n## Customer Segmentation (ranked)\n")
                lines.append("| Rank | Segment | Reasoning |\n")
                lines.append("|---|---|---|\n")
                for s in ds.customer_segments:
                    lines.append(f"| {s.rank} | {s.name} | {s.reasoning[:120]} |\n")

            ubp = ds.user_buyer_payer
            if ubp and any(v for v in [ubp.user, ubp.buyer, ubp.economic_buyer, ubp.decision_maker]):
                lines.append("\n---\n## User → Buyer → Payer\n")
                lines.append("| Role | Who |\n")
                lines.append("|---|---|\n")
                if ubp.user: lines.append(f"| User (uses product) | {ubp.user} |\n")
                if ubp.buyer: lines.append(f"| Buyer (evaluates) | {ubp.buyer} |\n")
                if ubp.economic_buyer: lines.append(f"| Economic Buyer (budget) | {ubp.economic_buyer} |\n")
                if ubp.decision_maker: lines.append(f"| Decision Maker (approves) | {ubp.decision_maker} |\n")
                if ubp.champion: lines.append(f"| Champion (advocate) | {ubp.champion} |\n")
                if ubp.influencer: lines.append(f"| Influencer (advisor) | {ubp.influencer} |\n")

            if ds.business_models:
                lines.append("\n---\n## Business Model Options (ranked)\n")
                lines.append("| Option | Viability | Reasoning |\n")
                lines.append("|---|---|---|\n")
                for b in ds.business_models:
                    lines.append(f"| {b.name} | {b.viability}/100 | {b.reasoning[:120]} |\n")

            if ds.funding_recommendation:
                lines.append(f"\n**Funding Path:** {ds.funding_recommendation}\n")

            if ds.vc_fit:
                lines.append("\n---\n## VC Fit Analysis\n")
                lines.append("| Firm | Fit (1-5) | Reasoning |\n")
                lines.append("|---|---|---|\n")
                for v in ds.vc_fit:
                    stars = "⭐" * v.score
                    lines.append(f"| {v.firm} | {stars} | {v.reasoning[:120]} |\n")

            if ds.investor_readiness:
                lines.append("\n---\n## Investor Readiness\n")
                lines.append("| Question | Assessment |\n")
                lines.append("|---|---|\n")
                for r in ds.investor_readiness:
                    lines.append(f"| {r.question} | {r.assessment[:120]} |\n")

            if ds.financial_projection:
                lines.append("\n---\n## Financial Projection\n")
                lines.append(f"{ds.financial_projection}\n")

            if ds.validation_roadmap:
                lines.append("\n---\n## Validation Roadmap\n")
                for step in ds.validation_roadmap:
                    lines.append(f"- {step}\n")

            if ds.investor_questions:
                lines.append("\n---\n## Questions an Investor Will Ask\n")
                for q in ds.investor_questions:
                    lines.append(f"- {q}\n")

            if ds.red_team_fail or ds.red_team_succeed:
                lines.append("\n---\n## Red Team Analysis\n")
                if ds.red_team_fail:
                    lines.append("\n**Reasons this startup could fail:**\n")
                    for r in ds.red_team_fail:
                        lines.append(f"- {r}\n")
                if ds.red_team_succeed:
                    lines.append("\n**Reasons this startup could succeed:**\n")
                    for r in ds.red_team_succeed:
                        lines.append(f"- {r}\n")

            if ds.founder_coach:
                lines.append("\n---\n## Founder Coach — Top 5 Actions\n")
                for a in ds.founder_coach:
                    lines.append(f"- {a}\n")

            if ds.beachhead:
                lines.append("\n---\n## Beachhead Analysis\n")
                lines.append("| Step | Target | Reasoning |\n")
                lines.append("|---|---|---|\n")
                for i, b in enumerate(ds.beachhead, 1):
                    lines.append(f"| {i} | {b.segment} | {b.reasoning[:120]} |\n")

            if ds.pricing:
                lines.append("\n---\n## Suggested Pricing\n")
                lines.append("| Tier | Price | Target | Reasoning |\n")
                lines.append("|---|---|---|---|\n")
                for p in ds.pricing:
                    lines.append(f"| {p.name} | {p.price} | {p.target} | {p.reasoning[:120]} |\n")

            if ds.product_roadmap:
                lines.append("\n---\n## Product Roadmap\n")
                lines.append("| Phase | Description |\n")
                lines.append("|---|---|\n")
                for p in ds.product_roadmap:
                    lines.append(f"| {p.phase} | {p.description[:120]} |\n")

            if ds.success_metrics:
                lines.append("\n---\n## Success Metrics\n")
                lines.append("| Metric | Target | Timeframe |\n")
                lines.append("|---|---|---|\n")
                for m in ds.success_metrics:
                    lines.append(f"| {m.metric} | {m.target} | {m.timeframe} |\n")

            if ds.build_decision:
                decision_icon = {"BUILD": "✅", "BUILD_AFTER_VALIDATION": "🟡", "PIVOT": "🟠", "DONT_BUILD": "🔴"}
                icon = decision_icon.get(ds.build_decision, "⚪")
                lines.append(f"\n---\n## Build Recommendation: {icon} {ds.build_decision.replace('_', ' ').title()}\n")
                if ds.build_reasoning:
                    lines.append(f"{ds.build_reasoning}\n")

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

    if report.completeness:
        comp = report.completeness
        lines.append(f"\n**Idea Completeness:** {comp.completeness_score:.0f}/100\n")
        if comp.fields:
            for field_name, field_data in comp.fields.items():
                if isinstance(field_data, dict):
                    present = field_data.get("present", False)
                    mark = "\u2705" if present else "\u274c"
                    lines.append(f"- {mark} {field_name.replace('_', ' ').title()}: {field_data.get('detail', '')[:120]}\n")
        if comp.follow_up_questions:
            lines.append("\n**Follow-up questions to strengthen this idea:**\n")
            for q in comp.follow_up_questions:
                lines.append(f"- {q}\n")
        if comp.summary:
            lines.append(f"\n*{comp.summary}*\n")

    lines.extend([
        "\n---\n## 2. Demand Signal Check\n",
        f"**Strength:** {report.demand.strength} ({len(report.demand.evidence)} sources)\n",
    ])
    for i, claim in enumerate(report.demand.evidence[:8], 1):
        lines.append(f"{i}. {claim.text[:200]} [[source]({claim.source_url})]\n")
    if len(report.demand.evidence) > 8:
        lines.append(f"... and {len(report.demand.evidence) - 8} more\n")

    lines.extend(["\n---\n## 3. Competitor Landscape\n"])
    verified = [c for c in report.competitors if c.is_verified_competitor]
    unverified = [c for c in report.competitors if not c.is_verified_competitor]

    if verified:
        has_details = any(c.focus_area or c.target_customer or c.weakness for c in verified)
        if has_details:
            comp_has_edge = any(c.your_edge for c in verified)
            if comp_has_edge:
                lines.append(f"**Competitor comparison ({len(verified)}):**\n")
                lines.append("| Company | Funding | Focus | Customer | Weakness | Your Edge |\n")
                lines.append("|---|---|---|---|---|---|\n")
                for c in verified:
                    lines.append(
                        f"| {c.name} | {c.funding_signal or 'Unknown'} | "
                        f"{c.focus_area or '—'} | {c.target_customer or '—'} | "
                        f"{c.weakness or '—'} | {c.your_edge or '—'} |\n"
                    )
            else:
                lines.append(f"**Competitor comparison ({len(verified)}):**\n")
                lines.append("| Company | Funding | Focus | Customer | Weakness |\n")
                lines.append("|---|---|---|---|---|\n")
                for c in verified:
                    lines.append(
                        f"| {c.name} | {c.funding_signal or 'Unknown'} | "
                        f"{c.focus_area or '—'} | {c.target_customer or '—'} | "
                        f"{c.weakness or '—'} |\n"
                    )
        else:
            lines.append(f"**Verified competitors ({len(verified)}):**\n")
            for c in verified:
                funding = f" ({c.funding_signal})" if c.funding_signal else ""
                lines.append(f"- {c.name}{funding} [[source]({c.source_url})]\n")
    if unverified:
        lines.append(f"\n*{len(unverified)} other references found (media, directories, etc.)*\n")
    if not report.competitors:
        lines.append("*No direct competitors identified from web search.*\n")

    lines.extend([
        "\n---\n## 4. Market Sizing (Directional)\n",
        f"{report.market_sizing.estimate_summary}\n",
        f"**Confidence:** {report.market_sizing.confidence}\n",
        f"**Sources:** {len(report.market_sizing.basis)}\n",
    ])

    lines.extend(["\n---\n## 5. Risk Flags\n"])
    for r in report.risks:
        lines.append(f"- {r}\n")
    if not report.risks:
        lines.append("*No significant risks flagged.*\n")

    lines.extend(["\n---\n## 6. Business Plan Draft\n", report.business_plan_draft, "\n"])

    if report.unresolved_claims_stripped > 0:
        lines.extend([
            "\n---\n## Validation Note\n",
            f"{report.unresolved_claims_stripped} unsupported claim(s) were "
            "removed by the automated validator.\n",
        ])

    return "".join(lines)