# Contributing

We welcome contributions from the community. This guide explains how to contribute effectively.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/Startup-idea-validator.git`
3. Create a virtual environment: `python3 -m venv venv && source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install Ollama and pull a model: `ollama pull qwen3:1.7b`
6. Run tests: `pytest tests/`

## Development Workflow

1. Create a branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `pytest tests/`
4. Run the pipeline with a test idea to verify no regressions
5. Commit with a descriptive message
6. Push and open a PR

## Code Style

- Follow PEP 8
- Use type hints for all functions
- Keep functions focused and single-purpose
- Write docstrings for public functions
- Use `pathlib.Path` for file paths

## Adding a New Agent

1. Create `app/agents/your_agent.py`
2. Define a function that accepts and returns `PipelineState`
3. Add the node to `app/pipeline.py`
4. Add any new schemas to `app/schemas.py`
5. Write tests in `tests/test_pipeline.py`

## Adding a New LLM Provider

1. Add the provider function in `app/model_config.py`
2. Add the provider to `get_llm_with_fallback()` fallback chain
3. Document the env vars in `.env.example` and `README.md`

## Testing

- Run `pytest tests/` to verify existing tests pass
- Add new tests for new functionality
- Test edge cases (empty input, missing fields, rate limits)

## Pull Request Guidelines

- One feature per PR
- Include tests
- Update docs (README, CHANGELOG) as needed
- Ensure all existing tests pass
- Link any related issues

## Questions?

Open a [GitHub Discussion](https://github.com/shamiquekhan/Startup-idea-validator/discussions) for questions, ideas, or feedback.
