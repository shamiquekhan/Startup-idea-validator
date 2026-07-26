# Startup Idea Validation & Business Plan Generator — Build Guide

**Owner:** Shamique · **For:** Suproc Marketplace proof-of-work
**Status:** Draft v1 — for internal review before build starts

---

## 1. Market Landscape (why this, and how to differentiate)

A number of tools already do some version of this, so the guide starts here to avoid rebuilding something generic.

**What exists today:**
- General-purpose AI business-plan generators (e.g. Venturekit-style tools) — these structure and format a plan from user input, but don't do original market research. They're glorified writing assistants.
- Idea validators (free web tools, NxCode-style) — quick SWOT + market-size calculators, shallow, no sourcing.
- All-in-one suites (IdeaProof, WorthBuild-style platforms) — validation + business plan + branding + ad creatives bundled, credit-based pricing, broad but often generic on the validation step itself.
- Evidence-first validators (DimeADozen.AI, Preuve AI–style) — the more credible end of the market. Their pitch is that every claim in the output is source-linked (market size, competitors, pricing, demand signals), not just generated from the model's training data. Preuve-style tools explicitly score pain signals + market size + competitors + pricing + demand into a single viability score.
- Pain-focused tools (PainMap-style) — mine forums/review sites purely for evidence that a problem exists, without going further into full viability.

**The clear gap and the differentiator to build toward:**
The tools that get criticized are the ones that let an LLM invent competitors, market sizes, and pricing from training data with false confidence. The tools that get praised are the ones where every claim traces back to a real, fetched source. **This agent should be built evidence-first from day one** — every output claim (market size, competitor, pricing, demand signal) must carry a source URL. That's the credibility hook for a Marketplace listing: "not just another AI opinion generator."

---

## 2. What the Agent Does (v1 scope)

**Input:** A startup idea in plain text (problem, proposed solution, target user/market — a few sentences is enough).

**Output:** A structured, source-cited report containing:
1. Problem framing — restated problem + who feels it
2. Market signal check — evidence the problem is real (forum/community discussion, search interest)
3. Competitor landscape — existing players solving this or adjacent problems, with links
4. Market sizing — rough TAM/SAM signal from available public data, clearly labeled as an estimate
5. Differentiation & risk flags — saturation, regulatory concerns, obvious gaps
6. Viability score (0–100) — transparent, weighted from the above, not a black box
7. One-page business plan draft — problem, solution, market, GTM suggestion, risks

Every factual claim in sections 2–5 links to its source. The model may synthesize and reason, but may not assert unsourced facts.

---

## 3. Architecture — reuse what you've already built

You already have **ARAMS** (LangGraph 8-agent research pipeline, running on Groq/Ollama/DuckDuckGo/ChromaDB). That's structurally the same shape as this agent needs: a multi-agent research pipeline with retrieval + synthesis + a validation/QA step. Treat this build as a **specialized fork of ARAMS**, not a from-scratch system — reuse the orchestration pattern, swap in domain-specific sub-agents and data sources.

**Proposed agent graph (LangGraph nodes):**

| Node | Job | Data source |
|---|---|---|
| Intake Agent | Parses raw idea text into structured fields (problem, solution, target market, category) | LLM only |
| Demand Signal Agent | Searches forums/communities/search trends for evidence the pain point is real | Apify: Google Search Results Scraper, Reddit Scraper |
| Competitor Agent | Finds existing companies solving this/adjacent problems | Apify: Crunchbase Scraper, Google Search Results Scraper |
| Market Sizing Agent | Pulls funding/scale signals for the category to approximate market size | Apify: Crunchbase Scraper, Company Research & Analysis Agent |
| Review/Sentiment Agent (optional v1.1) | Pulls G2/review data on closest existing competitors for positioning gaps | Apify: G2 Reviews Scraper |
| Scoring Agent | Combines all signals into a transparent, weighted 0–100 viability score | Deterministic logic, not just LLM judgment |
| Plan Writer Agent | Drafts the one-page business plan from validated findings only | LLM, source-constrained |
| Validator/QA Agent | Checks every claim in the final output has a linked source; strips or flags anything that doesn't (mirrors the human-approval-gating pattern from your Suproc work) | Deterministic validator |

This keeps the same "deterministic validator with gating" discipline you already used at Suproc — good consistency across your portfolio, and it's the exact feature that differentiates this from the sloppier tools in the market scan above.

---

## 4. Tech Stack

- **Orchestration:** LangGraph (reuse from ARAMS)
- **LLM:** Groq (fast inference) or Ollama/Qwen3 locally for dev — match what you already have working
- **Data sourcing:** Apify actors (free tier / pay-per-result, no infra to stand up)
  - Google Search Results Scraper — SERP data for demand signals & competitor discovery
  - Crunchbase Scraper — funding, competitor scale, market signals
  - G2 Reviews Scraper — competitor positioning/sentiment (v1.1, optional)
  - Reddit/forum scraper — organic pain-point evidence
- **Storage:** SQLite or ChromaDB (reuse ARAMS pattern) for caching sources per run
- **Schema/validation:** Pydantic v2 — define strict output schema so every claim has a `source_url` field; nothing ships without one
- **Output format:** Structured JSON → rendered to Markdown/PDF report

---

## 5. Phase-Wise Build Plan

### Phase 0 — Setup & Scoping (0.5–1 day)
- Confirm final scope with Suproc PM (this doc)
- Set up Apify account, test free-tier credits on the 2–3 actors above with a sample idea
- Confirm ARAMS repo structure is reusable as a starting fork

### Phase 1 — Core Pipeline Skeleton (2–3 days)
- Fork ARAMS LangGraph structure
- Build Intake Agent (idea text → structured fields)
- Build Plan Writer Agent stub (structured fields → placeholder plan, no research yet)
- Get a dumb end-to-end run working: text in → draft plan out, no sourcing yet

### Phase 2 — Data Sourcing Agents (3–4 days)
- Wire in Demand Signal Agent (search + forum scraping via Apify)
- Wire in Competitor Agent (Crunchbase + search scraping)
- Wire in Market Sizing Agent
- Each agent returns structured findings **with source URLs attached**, cached to SQLite/ChromaDB

### Phase 3 — Scoring & Validation (2 days)
- Build the deterministic Scoring Agent (weighted formula across demand/competition/market size/risk — keep the weighting transparent and documented, not a black box)
- Build the Validator/QA Agent that checks every claim has a source before it reaches the final report; strip/flag unsourced claims

### Phase 4 — Report Generation (1–2 days)
- Plan Writer Agent assembles final structured output from validated findings only
- Render to clean Markdown/PDF report with inline source links

### Phase 5 — Demo & Marketplace Packaging (2 days)
- Build a minimal interface (simple form or chat input) to run the agent end-to-end for demo purposes
- Run 3–5 sample startup ideas through it (mix of good/weak ideas) to show the output range
- Write the Marketplace listing copy: what it does, what makes it different (source-cited, not opinion), sample output
- Package pricing/usage model if Suproc requires one for the listing

**Estimated total: ~10–13 working days** for a solid v1, assuming part-time alongside your other Suproc work.

---

## 6. Open Questions for Suproc Review

- Should the Marketplace listing be usage-based (pay per validation run) or a flat demo/showcase with no billing yet?
- Any preferred LLM provider/budget constraint for the hosted version, or is Groq/Ollama fine to ship with?
- Should review-sentiment (G2 scraper) be in v1 scope, or held for v1.1 to keep the first build tighter?

---

## 7. Risks / Things to Flag Early

- **Apify scraper reliability:** Crunchbase/G2 scraping is against sites that actively fight scraping — actors can break. Build with graceful fallback (skip a signal rather than fail the whole run) rather than hard-depending on any single source.
- **Cost creep on Apify pay-per-result actors** if demo usage scales — worth capping run frequency during the showcase phase.
- **Scope discipline:** the competitive landscape shows how easy it is to sprawl into branding/logos/ad-copy generation. Stay narrow — validation + plan only — for a demoable, defensible v1.
