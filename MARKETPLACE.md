# Startup Validation Agent — Marketplace Listing

## One-liner
**Evidence-first startup idea validator** — drop in an idea, get back a source-cited validation report with demand signal, competitor landscape, market sizing, risk flags, and a one-page business plan. Every claim links to a real source.

## What it does
Most idea validators just prompt an LLM and let it invent competitors and market sizes from training data. This agent doesn't. It runs a multi-stage research pipeline that searches the web for real evidence, then assembles a structured 7-section report:

| Section | What you get |
|---|---|
| 1. Problem Framing | Restated problem + target user, extracted by AI |
| 2. Demand Signal | Real forum/community/search evidence with source links |
| 3. Competitor Landscape | Companies solving adjacent problems, with URLs |
| 4. Market Sizing | Directional estimate from public data, labeled with confidence |
| 5. Risk Flags | Derived from evidence (not hardcoded) |
| 6. Viability Score | 0–100, transparent weighted formula, not a black box |
| 7. Business Plan Draft | One-page plan using only validated evidence |

## How it's different
- **Every claim is sourced** — the automated validator strips any output that lacks a `source_url`. The report shows exactly how many claims were caught and removed.
- **No hallucinated competitors** — the Plan Writer is explicitly forbidden from introducing new facts. It can only phrase what the validator has already approved.
- **Transparent scoring** — the weighting formula (demand 30%, competition 25%, market size 25%, risk 20%) is shown in every report, not hidden.

## Sample output
> **Viability Score: 76/100**
> **Demand signal:** strong (12 evidence sources)
> **Competitors:** 2 identified
> **Risks:** Regulatory considerations for fintech sector
> *(full report: ~9,000 chars with inline citations)*

## How to use
```bash
# Start the server
PYTHONPATH="." uvicorn app.main:app --port 8765

# Open http://localhost:8765 in a browser
# Paste your idea and click Validate

# Or use the API directly
curl -X POST http://localhost:8765/validate \
  -H "Content-Type: application/json" \
  -d '{"idea": "Your startup idea here..."}'
```

## Input
2–3 sentences describing the problem, proposed solution, and target user.

## Output
JSON with `markdown` (full report), `score` (0–100), `unresolved_claims_stripped`.

## Run time
~30–90 seconds per idea (search queries are the bottleneck).

## Tech stack
LangGraph · FastAPI · Qwen3 (Ollama) · DuckDuckGo Search · Pydantic v2 · SQLite

## Pricing model
*Open question for Suproc — see below.*

## Open questions for Suproc
1. Usage-based (per validation run) or flat demo with no billing?
2. Preferred LLM provider for hosted version (current: Ollama Qwen3 local)?
3. Should G2 review scraping be added for v1.1?
4. Any brand/format requirements for the PDF report output?
