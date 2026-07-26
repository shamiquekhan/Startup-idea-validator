"""Pipeline tests — end-to-end with real search data."""

import asyncio
import re
from app.pipeline import run_pipeline


_PLACEHOLDER_RE = re.compile(r"^(condition|step|criteria|example)\s*\d+$", re.I)


def test_pipeline_end_to_end():
    result = asyncio.run(
        run_pipeline(
            "Small businesses struggle to track expenses across multiple bank accounts. "
            "Building an expense tracker that auto-categorizes transactions. "
            "Target: freelancers and micro-businesses."
        )
    )
    assert result["intake"] is not None
    assert result["demand"] is not None
    assert result["competitors"] is not None
    assert result["market_sizing"] is not None
    assert result["evaluation"] is not None
    assert result["report"] is not None
    assert result["markdown"] is not None
    assert len(result["markdown"]) > 500
    assert 0 <= result["evaluation"].overall_score <= 100
    assert result["intake"].problem_statement
    assert result["intake"].target_user
    assert result["intake"].proposed_solution
    assert result["evaluation"].recommendation.verdict in (
        "build", "narrow", "pivot", "abandon", "insufficient-info"
    )

    # Invariant: dimension weights should sum to ~1.0
    weight_sum = sum(d.weight for d in result["evaluation"].dimensions)
    assert abs(weight_sum - 1.0) < 0.06, f"Weights sum to {weight_sum:.3f}"

    # Invariant: no placeholder text leaking through
    ev = result["evaluation"]
    for item in ev.recommendation.kill_criteria + ev.recommendation.next_steps:
        assert not _PLACEHOLDER_RE.match(item.strip()), f"Placeholder found: {item!r}"
    for item in ev.recommendation.kill_criteria + ev.recommendation.next_steps:
        assert len(item) > 10, f"Criterion/step too short: {item!r}"

    # Invariant: market sizing source count matches stored basis length
    ms = result["market_sizing"]
    basis_count = len(ms.basis)
    assert str(basis_count) in ms.estimate_summary, (
        f"Source count mismatch: summary says ~{basis_count}, basis has {basis_count}"
    )

    print(f"Score: {result['evaluation'].overall_score:.0f}/100")
    print(f"Verdict: {result['evaluation'].recommendation.verdict}")
    print(f"Demand: {len(result['demand'].evidence)} ({result['demand'].strength})")
    print(f"Competitors: {len(result['competitors'])}")
    print(f"Kill criteria: {len(result['evaluation'].recommendation.kill_criteria)}")
    print(f"Next steps: {len(result['evaluation'].recommendation.next_steps)}")


if __name__ == "__main__":
    test_pipeline_end_to_end()
    print("\n✅ All checks passed")
