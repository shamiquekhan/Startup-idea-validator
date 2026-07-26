# Startup Idea Validation & Business Plan Generator — Detailed Build Guide

**Owner:** Shamique · **For:** Suproc Marketplace proof-of-work
**Status:** Draft v2 — standalone project, detailed build guide

---

## 1. Executive Summary

An AI agent that takes a raw startup idea (a few sentences of text) and produces a structured, **source-cited** validation report plus a one-page business plan draft — covering demand evidence, competitor landscape, rough market sizing, risk flags, a transparent viability score, and a GTM sketch. Every factual claim in the output links back to a real, fetched source rather than being generated from the model's training memory. This is the core differentiator versus most tools currently on the market.

Built as a standalone multi-agent pipeline, using free/low-cost data sourcing via Apify actors, packaged as a demoable service for the Suproc Marketplace.

---

## 2. Market Landscape (why this, and how to differentiate)

**What exists today:**

- General-purpose AI business-plan generators (e.g. Venturekit-style tools) — structure and format a plan from user input, but don't do original market research. Essentially writing assistants.
- Free idea validators (e.g. NxCode-style tools) — quick SWOT + market-size calculators, shallow, no real sourcing, often just prompt-and-guess.
- All-in-one suites (IdeaProof, WorthBuild-style platforms) — validation + business plan + branding + ad creatives bundled, credit-based pricing (roughly €0.20–0.50 per validation run in credits). Broad scope, but the validation step itself is often generic and not well-sourced.
- Evidence-first validators (DimeADozen.AI, Preuve AI–style tools) — the more credible end of the market. Every claim in the output links to a real source; they score pain signals + market size + competitors + pricing + demand into a single viability rating.
- Pain-focused tools (PainMap-style) — mine forums/review sites purely for evidence that a problem exists, without going further into full viability.
- Guided platforms (Startup Ignition–style) — credit-based, bootcamp-backed methodology, broader than a single tool (interview question generation, business-model stress testing).

**The gap:** the tools that get criticized in reviews are the ones where the LLM invents competitor names, market sizes, and pricing with false confidence, purely from training data. The tools that get praised are the ones where every claim is traceable to a fetched source. That's the wedge for this build: **evidence-first by construction**, not bolted on as a disclaimer.

---

## 3. Product Scope (v1)

**Input:** Free-text startup idea — problem statement, proposed solution, target user/market. Minimum viable input: 2–3 sentences. No signup friction for the demo.

**Output — a structured report with 7 sections:**

1. **Problem framing** — restated problem in clear terms + who specifically feels it
2. **Demand signal check** — evidence the problem is real: forum/community discussion volume, search interest trends, direct quotes/paraphrases of people describing the pain (with source links)
3. **Competitor landscape** — existing companies solving this or an adjacent problem, each with: name, what they do, funding/scale signal if available, source link
4. **Market sizing (directional)** — rough TAM/SAM signal built from available public data (funding totals in the category, adjacent market reports), explicitly labeled as an estimate, not a hard number
5. **Differentiation & risk flags** — market saturation level, regulatory concerns if any, obvious execution gaps
6. **Viability score (0–100)** — transparent, weighted formula across the above signals, with the weighting shown to the user (not a black box)
7. **One-page business plan draft** — problem, solution, target market, competitive positioning, GTM suggestion, key risks, next validation steps

**Explicit non-goals for v1** (to keep scope tight and demoable):

- No branding, logo, or ad-creative generation
- No financial projections/spreadsheet modeling
- No customer interview simulation
- No multi-idea comparison (single idea per run only)

---

## 4. System Architecture

A multi-stage agent pipeline, each stage with a single clear responsibility, output validated before passing to the next stage.

```
User Input (raw idea text)
        │
        ▼
[1] Intake Agent  ──────────────► structured idea object
        │
        ▼
[2] Research Orchestrator ─────► fans out to:
        ├── Demand Signal Agent
        ├── Competitor Agent
        └── Market Sizing Agent
        │
        ▼
[3] Evidence Aggregator ───────► merges all findings, deduplicates sources
        │
        ▼
[4] Scoring Agent ─────────────► deterministic 0–100 viability score
        │
        ▼
[5] Validator / QA Agent ──────► checks every claim has a source_url; strips/flags any that don't
        │
        ▼
[6] Plan Writer Agent ──────────► drafts the business plan from validated findings only
        │
        ▼
[7] Report Renderer ───────────► structured JSON → Markdown/PDF report with inline citations
```

**Design principle:** stages 2–4 (research) are strictly separated from stage 6 (writing). The writer agent is never allowed to introduce a new fact — it may only phrase and organize what stage 5 has already validated. This is the mechanism that prevents hallucinated competitors/numbers from reaching the final report.

**Orchestration pattern:** a directed graph (not a single long prompt chain) so each stage can be tested, retried, and swapped independently. Each agent is a discrete function/service with a strict input/output schema — not a loose prompt with free-text output.

---

## 5. Tech Stack

| Layer                         | Choice                                                           | Notes                                                                                                         |
| ----------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Orchestration                 | LangGraph                                                        | Graph-based multi-agent orchestration; each node above is a graph node with defined state passed between them |
| LLM (dev/local)               | Ollama running Qwen3                                             | Free, local, good for iterating without burning API credits                                                   |
| LLM (production/demo)         | Groq-hosted model                                                | Fast inference for a responsive live demo                                                                     |
| Data sourcing                 | Apify actors (pay-per-result, free tier available)               | See Section 6 for full actor list                                                                             |
| Structured validation         | Pydantic v2                                                      | Every agent's output is a strict schema — see Section 7                                                      |
| Storage / caching             | SQLite                                                           | Cache raw scraped sources per run so repeated runs on similar ideas don't re-scrape unnecessarily             |
| Vector store (optional, v1.1) | ChromaDB                                                         | If you want semantic dedup/similarity across competitor mentions later                                        |
| Backend/API                   | FastAPI (Python)                                                 | Wraps the pipeline as a callable service — needed either way for a Marketplace listing                       |
| Demo frontend                 | Simple form (single text box) → rendered report page            | Keep minimal — a clean input/output demo, not a full product UI                                              |
| Report output                 | Markdown → rendered to PDF (e.g. via a markdown-to-pdf library) | So the deliverable is a shareable file, not just a webpage                                                    |

---

## 6. Data Sourcing — Apify Actors

| Actor                             | Purpose                                                                                  | Notes                                                              |
| --------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Google Search Results Scraper     | SERP data for demand signals, competitor discovery, general topic research               | Cheap, fast, good default first call for almost every idea         |
| Crunchbase Scraper                | Company profiles, funding rounds, founders, investors for competitor + market sizing     | Pay-per-result; useful for funded-startup competitors specifically |
| Company Research & Analysis Agent | Aggregated company intelligence (LinkedIn, PitchBook, Crunchbase) for a given competitor | Use selectively — richer but more expensive per call              |
| G2 Reviews Scraper                | Product reviews, pricing, competitor mentions for SaaS-category ideas                    | Optional for v1, useful mainly when the idea is software/SaaS      |
| Reddit/forum scraper              | Organic pain-point discussion for demand signal evidence                                 | Good source of real, unfiltered user language about the problem    |

**Sequencing per run:** Search scraper runs first (cheap, broad) to identify candidate competitors and discussion threads → Crunchbase/company scrapers run only on the specific candidates identified, to avoid wasting pay-per-result credits on a broad blind search.

**Fallback behavior:** if any single actor fails or returns nothing, that section of the report is marked "insufficient public data" rather than failing the whole run. No single data source should be a hard dependency.

---

## 7. Data Model (Pydantic schema sketch)

```python
class SourcedClaim(BaseModel):
    text: str
    source_url: str
    source_name: str

class CompetitorEntry(BaseModel):
    name: str
    description: str
    funding_signal: str | None
    source_url: str

class DemandSignal(BaseModel):
    evidence: list[SourcedClaim]
    strength: Literal["weak", "moderate", "strong"]

class MarketSizing(BaseModel):
    estimate_summary: str
    basis: list[SourcedClaim]
    confidence: Literal["low", "medium"]  # never "high" — always directional

class ViabilityScore(BaseModel):
    score: int  # 0-100
    breakdown: dict[str, int]  # e.g. {"demand": 20, "competition": 15, "market_size": 18, "risk": 12}
    weighting_explanation: str

class ValidationReport(BaseModel):
    problem_statement: str
    target_user: str
    demand: DemandSignal
    competitors: list[CompetitorEntry]
    market_sizing: MarketSizing
    risks: list[str]
    viability: ViabilityScore
    business_plan_draft: str
    unresolved_claims_stripped: int  # count of anything the validator removed for lacking a source
```

The `unresolved_claims_stripped` field matters — it's a transparency signal you can literally show in the demo ("N unsupported claims were caught and removed"), which doubles as proof the validator is actually doing something.

---

## 8. Phase-Wise Build Plan

### Phase 0 — Setup & Scoping (0.5–1 day)

- Finalize scope against this doc with Suproc PM
- Set up Apify account, test free-tier credits on Google Search Results Scraper and Crunchbase Scraper with 2–3 sample ideas, sanity-check output quality
- Set up local dev environment: Python, LangGraph, Ollama + Qwen3 pulled locally
- Set up SQLite schema for run caching

**Deliverable:** working dev environment, confirmed Apify actor outputs look usable

### Phase 1 — Core Pipeline Skeleton (2–3 days)

- Define all Pydantic schemas (Section 7)
- Build Intake Agent: raw text → structured idea object (problem, solution, target market, category)
- Build Report Renderer: structured JSON → Markdown output (build this early so you can visually inspect progress at every later phase)
- Wire a dumb end-to-end pass: intake → placeholder empty research → plan writer → rendered report, with no real data yet

**Deliverable:** a runnable pipeline that produces a (currently fake) report end-to-end. This proves the plumbing works before adding real research.

### Phase 2 — Demand Signal Agent (1–2 days)

- Build the search query generation logic (idea → 3–5 targeted search/forum queries)
- Wire Google Search Results Scraper + Reddit scraper
- Parse results into `SourcedClaim` objects
- Build the "strength" classifier (weak/moderate/strong) based on volume/relevance of evidence found

**Deliverable:** given a test idea, agent returns real demand evidence with working source links

### Phase 3 — Competitor Agent (2 days)

- Build competitor discovery query logic
- Wire Google Search Results Scraper for broad discovery, then Crunchbase Scraper for the top candidates identified
- Deduplicate competitors found across both sources
- Populate `CompetitorEntry` objects with funding signal where available

**Deliverable:** given a test idea, agent returns a real competitor list with sources, no duplicates

### Phase 4 — Market Sizing Agent (1–2 days)

- Build logic to aggregate funding totals/category scale signals from the competitor data already gathered (reuse Phase 3 output rather than a fully separate scrape)
- Produce a clearly-labeled directional estimate, never a confident hard number
- Write the `basis` claims with sources

**Deliverable:** market sizing section that's honest about its own uncertainty

### Phase 5 — Evidence Aggregator + Validator/QA Agent (2 days)

- Build the aggregator that merges outputs from Phases 2–4 into one evidence set
- Build the Validator: walks every claim in the aggregated evidence, confirms a `source_url` is present and well-formed (syntactic URL check), strips anything that fails
- Track and expose `unresolved_claims_stripped` count

**Deliverable:** a hardened evidence set — nothing enters the next phase without a source

### Phase 6 — Scoring Agent (1 day)

- Design the weighting formula across demand strength, competitor density/saturation, market sizing signal, and risk flags
- Keep it as simple arithmetic over the classified signals, not another LLM call — this keeps the score explainable and reproducible
- Write the `weighting_explanation` string generation

**Deliverable:** a viability score that's consistent (same inputs → same score) and explainable

### Phase 7 — Plan Writer Agent (1–2 days)

- Prompt the writer agent to draft the one-page business plan using ONLY the validated `ValidationReport` object as context — explicitly instruct it not to introduce new facts
- Test with a few ideas to confirm it isn't smuggling in unsourced claims (spot-check against the aggregated evidence)

**Deliverable:** a coherent, well-written plan draft that traces cleanly back to validated evidence

### Phase 8 — API Wrapper & Demo Frontend (2 days)

- Wrap the full pipeline in a FastAPI endpoint: idea text in → `ValidationReport` JSON out
- Build a minimal frontend: single text input → runs the pipeline → renders the Markdown/PDF report
- Add basic loading states (this pipeline will take 30–90 seconds per run given multiple scraper calls — set expectations in the UI)

**Deliverable:** a working, demoable end-to-end product, not just a script

### Phase 9 — Testing & Sample Runs (1–2 days)

- Run 5–8 sample startup ideas through the full pipeline, deliberately mixing strong ideas, weak/saturated ideas, and vague ideas, to show the range of outputs
- Manually verify every source link in at least 2 full reports actually supports the claim it's attached to
- Fix any prompt/logic issues surfaced

**Deliverable:** a small library of sample reports you can show in the Marketplace listing

### Phase 10 — Marketplace Packaging (1 day)

- Write the listing copy: what it does, what makes it different (source-cited, not opinion-based), 1–2 sample report excerpts
- Decide and document the usage/pricing model (see open questions)
- Final pass on report formatting/branding for presentability

**Deliverable:** a live, presentable Marketplace listing

**Estimated total: ~14–18 working days** for a solid, demoable v1, assuming part-time work alongside other responsibilities. Compresses to ~10 days if Phases 4 and 9 are trimmed.

---

## 9. Testing & Quality Checks (ongoing, not just Phase 9)

- **Source integrity check:** every claim in a final report must have a resolvable URL — build this as an automated check, not just a manual spot-check, so it can run on every future update to the pipeline
- **Consistency check:** running the same idea twice should produce a similar (not wildly different) viability score — flag if scoring is too volatile
- **Failure handling:** confirm the pipeline degrades gracefully (missing data sections marked "insufficient data") rather than crashing when an Apify actor returns nothing
- **Latency check:** track total run time; if it regularly exceeds ~2 minutes, consider parallelizing the Phase 2–4 agents (they're independent and don't need to run sequentially)

---

## 10. Cost Considerations

- Apify: pay-per-result on Crunchbase/G2-style actors, free tier covers early development and demo runs; monitor spend once the Marketplace listing is live and usage isn't just you testing it
- LLM: Ollama/Qwen3 local is free for development; Groq for the live demo has its own usage cost — worth capping demo run frequency (e.g. rate-limit public demo runs) until there's a defined pricing model
- No other infra cost required for v1 — FastAPI + SQLite can run on minimal hosting

---

## 11. Risks & Mitigations

| Risk                                                                       | Mitigation                                                                                                            |
| -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Crunchbase/G2 scraping breaks (sites actively resist scraping)             | Build with graceful fallback per data source; never hard-fail the whole run on one source                             |
| Apify costs creep with public demo usage                                   | Rate-limit demo runs; cache repeated/similar queries                                                                  |
| Scope creep toward branding/ads/financial modeling (common in this market) | Hold the line at the 7-section report defined in Section 3; anything else goes in a v1.1 backlog                      |
| LLM writer smuggling in unsourced claims despite instructions              | Automated source-integrity check (Section 9) catches this regardless of prompt reliability                            |
| Report feels generic if evidence is thin for an obscure idea               | Explicitly show "insufficient public data" rather than papering over gaps — honesty is part of the credibility pitch |

---

## 12. Open Questions for Suproc

- Should the Marketplace listing be usage-based (pay per validation run) or a flat demo/showcase with no billing yet?
- Any preferred LLM provider/budget constraint for the hosted demo version, or is Groq/Ollama fine to ship with?
- Should the G2 review-sentiment source be in v1 scope, or held back for v1.1 to keep the first build tighter?
- Any brand/format requirements for how the final PDF report should look, given it'll represent Suproc's Marketplace quality bar?
