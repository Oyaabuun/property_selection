import os
import json
from typing import List, Literal
import google.generativeai as genai
from pydantic import BaseModel, ValidationError

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3-flash-preview")


# ---------------------------
# Pydantic schema (CRITICAL)
# ---------------------------
class LLMDecision(BaseModel):
    decision: Literal["BUY", "CAUTION", "AVOID"]
    confidence: float  # 0–1
    primary_risks: List[str]
    recommendation: str


async def reason_with_llm(context: dict, numeric_score: float) -> dict:
    prompt = f"""
You are a conservative property decision analyst in India.

You MUST return STRICT JSON only.
No markdown. No explanation outside JSON.

INPUT:
{json.dumps(context, indent=2)}

NUMERIC_SCORE (0–1): {numeric_score}

RULES:
- Be conservative
- Avoid irreversible mistakes
- Confidence must align with numeric_score
- Decision must be BUY, CAUTION, or AVOID

JSON FORMAT:
{{
  "decision": "BUY|CAUTION|AVOID",
  "confidence": 0.0,
  "primary_risks": [],
  "recommendation": ""
}}
"""

    with open("prompt_log.txt", "w") as f:
        f.write(prompt)

    response = model.generate_content(prompt)
    raw = response.text.strip()

    try:
        parsed = json.loads(raw)
        validated = LLMDecision(**parsed)
        return validated.dict()
    except (json.JSONDecodeError, ValidationError) as e:
        # SAFE fallback — this is VERY important
        return {
            "decision": "CAUTION",
            "confidence": round(numeric_score, 2),
            "primary_risks": ["LLM output validation failed"],
            "recommendation": "Manual review recommended"
        }
