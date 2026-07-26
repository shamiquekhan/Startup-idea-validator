"""Idea completeness checker — evaluates input quality and suggests follow-up questions."""

import json
import re

from app.model_config import get_llm_with_fallback as get_llm

_COMPLETENESS_PROMPT = """You are a startup idea analyst. Evaluate the completeness of this raw idea.

Raw idea: {raw_idea}

For each field below, score whether the idea provides enough information:
- problem: Does it describe a specific problem?
- customer: Does it identify who experiences the problem?
- solution: Does it describe what the startup builds?
- business_model: Does it explain how money is made?
- differentiation: Does it explain what makes it different?
- pricing: Does it mention pricing or willingness to pay?
- go_to_market: Does it describe how customers will be reached?
- technology: Does it describe the technical approach?
- geography: Is there a geographic focus?

Return ONLY valid JSON:
{{
  "completeness_score": 0-100,
  "fields": {{
    "problem": {{"present": true/false, "detail": "what was said or 'Not specified'"}},
    "customer": {{"present": true/false, "detail": "..."}},
    "solution": {{"present": true/false, "detail": "..."}},
    "business_model": {{"present": true/false, "detail": "..."}},
    "differentiation": {{"present": true/false, "detail": "..."}},
    "pricing": {{"present": true/false, "detail": "..."}},
    "go_to_market": {{"present": true/false, "detail": "..."}},
    "technology": {{"present": true/false, "detail": "..."}},
    "geography": {{"present": true/false, "detail": "..."}}
  }},
  "follow_up_questions": ["Specific question 1?", "Specific question 2?", ...],
  "summary": "One-line assessment of input quality"
}}
JSON:"""


async def check_completeness(raw_idea: str) -> dict:
    try:
        llm = get_llm(temperature=0.1, num_predict=1024)
        response = llm.invoke(_COMPLETENESS_PROMPT.format(raw_idea=raw_idea))
        text = response.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        return {
            "completeness_score": data.get("completeness_score", 50),
            "fields": data.get("fields", {}),
            "follow_up_questions": data.get("follow_up_questions", []),
            "summary": data.get("summary", ""),
        }
    except Exception:
        return {"completeness_score": 50, "fields": {}, "follow_up_questions": [], "summary": ""}