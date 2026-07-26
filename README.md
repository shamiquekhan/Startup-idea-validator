<div align="center">

# Startup Validation Agent

**Validate startup ideas like a VC.**

Generate structured startup evaluations, business plans, competitive analysis, go-to-market strategy, financial projections, and investor readiness reports using AI + live web evidence.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org)
[![GitHub last commit](https://img.shields.io/github/last-commit/shamiquekhan/Startup-idea-validator)](https://github.com/shamiquekhan/Startup-idea-validator)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen)](CONTRIBUTING.md)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-red)](LICENSE)

</div>

---

## Why This Exists

Asking ChatGPT "is my startup idea good?" gives you generic advice. This agent instead:

- **Searches the live web** for demand signals, competitors, and market data
- **Applies VC-style reasoning** — moat analysis, beachhead strategy, user/buyer/payer segmentation
- **Generates source-cited evidence** — every claim links back to a URL
- **Produces investor-grade output** — scoring breakdown, financial projections, validation roadmap, red-team critique

---

## Features

| Capability | Description |
|---|---|
| **Problem Pain Scoring** | Evaluates urgency, frequency, budget impact, and market trend |
| **Customer Clarity** | Identifies user vs buyer vs payer vs decision maker |
| **Solution Fit** | Assesses technical feasibility and adoption barriers |
| **Competitive Positioning** | Live web search for real competitors, relative weakness + your edge analysis |
| **Moat Analysis** | Evaluates data moat, algorithms, patents, network effects, switching costs |
| **Business Model Engine** | Ranks 4+ business model options by viability |
| **Pricing Strategy** | Generates tiered pricing suggestions (starter/growth/enterprise) |
| **Financial Projections** | Assumption-driven revenue, cost, and ARR projections |
| **Beachhead Analysis** | Identifies first-target customer niche with tiered rollout |
| **Validation Roadmap** | Week-by-week execution plan (interviews → MVP → pilot → paid pilot) |
| **VC Fit Analysis** | Scores fit against YC, a16z, Sequoia, SOSV and more |
| **Investor Readiness** | Answers 5 key investor questions |
| **Red Team Critique** | 5 reasons it fails + 5 reasons it succeeds |
| **Founder Coach** | 5 concrete actions to take tomorrow |
| **Build Decision** | Explicit BUILD / BUILD AFTER VALIDATION / PIVOT / DON'T BUILD |
| **Success Metrics** | Measurable goals with targets and timeframes |
| **Idea Completeness Check** | Pre-validates 9 dimensions before analysis |
| **Source Citations** | Every claim linked to its source URL |

---

## Demo

```text
Input:
An AI platform that helps small law firms automatically review contracts,
detect legal risks, and generate client-ready summaries.

Target customer: Small law firms with 1-10 lawyers
Solution: Browser extension integrating with Clio
```

[See full example report →](docs/example-reports/legal-ai.md)

---

## Architecture

```
User Idea
    │
    ▼
┌─────────────────────────────┐
│  1. Idea Completeness       │  ← 9-field pre-check
│     Checker                 │     (problem, customer, solution, etc.)
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  2. Structured Intake       │  ← Categorizes, extracts fields
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  3. Web Research            │  ← Demand signals, competitors,
│                             │     market sizing (live search)
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  4. Evidence Extraction     │  ← Classifies, deduplicates, enriches
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  5. Reasoning Engine        │  ← Multi-dimension evaluation
│  (Scoring + Decision)       │     with weight-based scoring
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  6. Decision Support        │  ← Moat, beachhead, pricing, roadmap,
│                             │     VC fit, red team, founder coach
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  7. Report Generation       │  ← Markdown renderer with tables
└─────────────────────────────┘
    │
    ▼
      Final Startup Report
```

---

## Scoring System

| Dimension | Weight | What It Measures |
|---|---|---|
| Problem Pain | 15% | Urgency, frequency, budget impact, market trend |
| Customer Clarity | 12% | Specificity of target user, buyer identification |
| Solution Fit | 12% | Technical feasibility, adoption likelihood |
| Competitive Position | 12% | Market density, differentiation potential |
| Technical Feasibility | 12% | AI/ML complexity, engineering requirements |
| Business Model | 12% | Revenue model clarity, pricing strategy |
| Adoption Barriers | 12% | Regulation, switching costs, training needs |
| Team Requirements | 12% | Expertise needed to build and ship |

Final score = weighted sum of dimensions, adjusted for confidence (low-confidence scores show a range).

---

## Benchmarks

| Startup Idea | Verdict | Score |
|---|---|---|
| AI Legal Contract Review for Small Firms | 🟡 BUILD AFTER VALIDATION | 56 |
| AI-Powered Drug Discovery Platform | 🟠 PIVOT | — |
| AI Tutor for High School Students | 🟢 BUILD | — |
| Flying Taxi Service | 🔴 DON'T BUILD | — |
| Lottery Prediction AI | 🔴 DON'T BUILD | — |

---

## Comparison

| Feature | ChatGPT | Startup Validator |
|---|---|---|
| Live web search | ❌ | ✅ (12+ sources per report) |
| VC-style structured scoring | ❌ | ✅ 8 dimension weighted |
| Moat analysis (data/patent/network) | ❌ | ✅ 5-factor evaluation |
| Financial projection with assumptions | ❌ | ✅ Assumption-driven |
| Validation roadmap | ❌ | ✅ Week-by-week |
| User vs Buyer vs Payer | ❌ | ✅ 6 role segmentation |
| Competitor relative positioning | ❌ | ✅ Weakness + your edge |
| Source citations for every claim | ❌ | ✅ |
| Idea completeness pre-check | ❌ | ✅ 9-field scan |
| Red-team analysis | ❌ | ✅ 5 fail + 5 succeed |
| Offline/local (Ollama) | ❌ | ✅ |
| API fallback (Groq / Gemini) | ❌ | ✅ |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) with `qwen3:1.7b` (or any model)
- Optional: Groq API key for faster inference
- Optional: Gemini API key for fallback

### Install

```bash
git clone https://github.com/shamiquekhan/Startup-idea-validator.git
cd Startup-idea-validator
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3:1.7b
cp .env.example .env   # configure your API keys
uvicorn app.main:app --port 8080
```

Open `http://localhost:8080`, paste a startup idea, and get a full validation report in ~60s.

### Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | No | `ollama` | `groq`, `gemini`, or `ollama` |
| `GROQ_API_KEY` | For Groq | — | Groq API key |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` | Groq model name |
| `GEMINI_API_KEY` | For Gemini | — | Google AI API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model name |

Fallback chain: `Groq → Gemini → Ollama` (when `LLM_PROVIDER=groq`)

---

## Project Structure

```
startup-validator/
├── app/
│   ├── agents/          # LangGraph pipeline nodes
│   │   ├── intake.py          # Idea parsing + categorization
│   │   ├── completeness.py    # Pre-validates 9 fields
│   │   ├── demand.py          # Demand signal extraction
│   │   ├── competitor.py      # Competitor discovery + enrichment
│   │   ├── market_sizing.py   # Market estimation
│   │   ├── risks.py           # Risk flagging
│   │   ├── evaluator.py       # Multi-dimension scoring
│   │   ├── aggregator.py      # Score aggregation
│   │   ├── decision_support.py # Strategic + tactical insights
│   │   ├── plan_writer.py     # Business plan draft
│   │   └── search_apify.py    # Apify search integration
│   ├── pipeline.py       # StateGraph orchestration
│   ├── schemas.py        # Pydantic models
│   ├── renderer.py       # Markdown report generation
│   ├── model_config.py   # LLM provider with fallback
│   ├── search.py         # Web search utilities
│   └── main.py           # FastAPI server
├── tests/
├── docs/
├── examples/
├── benchmarks/
├── prompts/
├── scripts/
├── requirements.txt
├── .env.example
├── CHANGELOG.md
├── ROADMAP.md
├── CONTRIBUTING.md
└── README.md
```

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System design and module responsibilities |
| [Scoring System](docs/scoring-system.md) | Dimension weights, confidence, and score computation |
| [Reasoning Engine](docs/reasoning-engine.md) | How the AI evaluates and decides |
| [Prompt Design](docs/prompt-design.md) | Prompt engineering philosophy and templates |
| [API Reference](docs/api.md) | REST API endpoints and usage |
| [Benchmarks](docs/benchmark.md) | Evaluation methodology and expected outputs |
| [FAQ](docs/faq.md) | Frequently asked questions |

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and development priorities.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute, code style, testing, and PR process.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Citation

If you use this project in research, please cite:

```bibtex
@software{startup_validator,
  title = {Startup Validation Agent},
  version = {2.4.0},
  url = {https://github.com/shamiquekhan/Startup-idea-validator}
}
```

---

<div align="center">
  Built for founders, investors, and accelerator programs.
</div>
