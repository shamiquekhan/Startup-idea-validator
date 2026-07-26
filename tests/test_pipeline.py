"""Pipeline tests — end-to-end with real search data."""

import asyncio
from app.pipeline import run_pipeline


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
    print(f"Score: {result['evaluation'].overall_score:.0f}/100")
    print(f"Verdict: {result['evaluation'].recommendation.verdict}")
    print(f"Demand: {len(result['demand'].evidence)} ({result['demand'].strength})")
    print(f"Competitors: {len(result['competitors'])}")
    print(f"Kill criteria: {len(result['evaluation'].recommendation.kill_criteria)}")
    print(f"Next steps: {len(result['evaluation'].recommendation.next_steps)}")


if __name__ == "__main__":
    test_pipeline_end_to_end()
    print("\n✅ All checks passed")
