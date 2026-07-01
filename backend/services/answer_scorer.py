import os
import json
import requests
from typing import Dict, Optional


SCORER_PROMPT = """You are a senior technical interviewer evaluating a candidate answer.

Question: {question}
Topic: {topic}
Candidate Answer: {answer}

Evaluate this answer and return ONLY a JSON object:
{{
  "score": <integer 1-10>,
  "feedback": "<one sentence overall feedback>",
  "strength": "<one specific thing done well>",
  "improvement": "<one specific improvement suggestion>"
}}

Scoring guide:
1-3: Incorrect or very incomplete
4-6: Partially correct, missing key concepts
7-8: Good answer with solid understanding
9-10: Excellent, demonstrates deep knowledge

Be specific and reference the actual answer content.
Return ONLY the JSON, no other text."""


def score_answer(question: str, answer: str, topic: str) -> Optional[Dict]:
    try:
        prompt = SCORER_PROMPT.format(
            question=question,
            topic=topic,
            answer=answer[:2000],
        )

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"].strip()

        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            content = content[start:end]

        data = json.loads(content)

        return {
            "score": max(1, min(10, int(data.get("score", 5)))),
            "feedback": str(data.get("feedback", ""))[:500],
            "strength": str(data.get("strength", ""))[:500],
            "improvement": str(data.get("improvement", ""))[:500],
        }
    except Exception:
        return None
