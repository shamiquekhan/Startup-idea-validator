# Changelog

## v2.4.0 (2026-07-27)

### Added
- Decision Support Engine — dual-pass strategic + tactical LLM calls
- Scoring transparency — `ScoreBreakdownItem` starts from BASE 100 with add/subtract
- Moat status system — ✅ Confirmed / 🟡 Likely / ⚪ Unknown / 🔴 Negative Evidence
- Competitor relative positioning — `your_edge` field per competitor
- Beachhead analysis — tiered first-target customer identification
- Pricing strategy — 3-tier suggested pricing table
- Product roadmap — MVP → Beta → Pilot → Paid Pilot → Enterprise → Scale
- Success metrics — measurable goals with targets and timeframes
- Build decision — explicit BUILD / BUILD AFTER VALIDATION / PIVOT / DON'T BUILD
- Idea completeness checker — pre-intake validation across 9 fields
- Gemini LLM provider fallback — Groq → Gemini → Ollama chain
- 15 new renderer sections for decision support output

### Fixed
- Competitor enrichment now generates relative weakness instead of generic criticism
- Moat analysis no longer assigns arbitrary 0 scores to missing information
- Financial projections now state explicit assumptions before numbers
- LLM provider fallback handles Groq rate limits gracefully

## v2.3.0 (2026-07-26)

### Added
- Apify search integration for broader competitor discovery
- Domain-aware category detection (SaaS, DeepTech, Marketplace, etc.)
- Anti-fabrication guards for market sizing and competitor data
- Deep-tech specific risk flags

### Fixed
- Crash on zero-competitor path
- Sources.py syntax error
- Weight normalization to ensure sum = 1.0

## v2.2.0 (2026-07-25)

### Added
- User → Buyer → Payer role segmentation
- Why Now? market timing analysis
- VC fit analysis with firm-specific scoring
- Investor readiness assessment
- Red team critique (5 fail + 5 succeed reasons)
- Founder coach with actionable next steps

### Fixed
- Placeholder text leaked into final reports
- Source count mismatch between header and actual citations

## v2.1.0 (2026-07-24)

### Added
- StartupType verticals for better routing
- Business model option ranking

### Fixed
- Missing StartupType verticals causing routing errors
- Weight sum validation in scoring engine

## v2.0.0 (2026-07-22)

### Added
- LangGraph pipeline with node-based architecture
- Web search for demand signals, competitors, and market sizing
- Multi-dimension weighted scoring (8 dimensions)
- Source citation preservation and validation
- Unsupported claim stripping
- FastAPI server with web UI
