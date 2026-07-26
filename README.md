# Startup Validation Agent

An AI-powered pipeline that evaluates startup ideas using structured multi-agent research — demand signal, competitor landscape, market sizing, risk analysis, and a scored evaluation with kill criteria.

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Requires Ollama with qwen3:1.7b
ollama pull qwen3:1.7b
uvicorn app.main:app --reload --port 8080
```

Open http://localhost:8080, paste an idea, and see a full validation report in ~60s.

## How It Works

```
raw_idea → intake → research (demand + competitors + market) → evaluate → aggregate → validate → plan_writer → render
```

Each node is a LangGraph step. Every claim in the output is linked to a source URL. The validator strips unsupported claims automatically.

## Data sourcing

The pipeline searches the web via **DuckDuckGo** for demand signals, competitors, and market-sizing data. There is no Crunchbase, G2, or Apify integration in this build — all competitor and funding data comes from public web search results, not structured databases. Source URLs are preserved for every claim so you can verify the evidence yourself.

## Production readiness

The current build runs **Ollama + Qwen3 1.7b locally**. It is not configured for hosted/public inference:
- Model inference requires a running Ollama instance on the host
- No Groq / OpenAI / Anthropic fallback is wired yet
- A larger model (8b+) is recommended for deployment to improve classification accuracy

## Marketplace

See [MARKETPLACE.md](MARKETPLACE.md) for the Suproc marketplace listing, architecture docs, and evaluation criteria.
