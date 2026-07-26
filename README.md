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

## Marketplace

See [MARKETPLACE.md](MARKETPLACE.md) for the Suproc marketplace listing, architecture docs, and evaluation criteria.
