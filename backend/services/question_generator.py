"""
Question generation service — uses LangChain LCEL as the primary path,
with a direct-requests fallback for environments where LangChain is unavailable.

Each returned question dict now includes a `source_chunks` key containing
the metadata of every RAG chunk that was used during generation, enabling
full traceability from question back to knowledge-base source.
"""

import os
import json
import requests
from typing import List, Dict

DIFFICULTY_HINTS = {
    "beginner": "Ask foundational conceptual questions. Test understanding of core principles.",
    "intermediate": "Mix conceptual and applied questions. Test both theory and practical implementation.",
    "advanced": "Ask deep technical questions requiring expert knowledge. Test architectural decisions and edge cases.",
}

QUESTION_PROMPT_TEMPLATE = """You are an expert technical interviewer.
Based on the following ML textbook content and candidate resume,
generate exactly 5 technical interview questions.

Candidate Skills: {skills}
Target Role: {role}
Experience Level: {level_hint}
Knowledge Base Context: {retrieved_chunks}

Rules:
- Questions must be specific to candidate background
- Questions must be grounded in retrieved textbook content
- {level_hint}
- No generic questions like "what is machine learning"
- Return ONLY a valid JSON array, no other text: [{{"id": 1, "question": "...", "topic": "..."}}, ...]
"""


def _extract_chunk_texts(chunks: List[Dict]) -> str:
    """Pull just the text out of chunk dicts for the LLM prompt."""
    texts = [c["text"] if isinstance(c, dict) else str(c) for c in chunks]
    return "\n\n".join(texts) if texts else "General ML and backend engineering concepts"


def _build_source_chunks_metadata(chunks: List[Dict]) -> List[Dict]:
    """Return only the traceable metadata fields (no full text) for each chunk."""
    result = []
    for c in chunks:
        if isinstance(c, dict):
            result.append({
                "source": c.get("source", "unknown"),
                "chunk_index": c.get("chunk_index", 0),
            })
    return result


def _parse_questions(content: str) -> List[Dict]:
    start = content.find("[")
    end = content.rfind("]") + 1
    if start != -1 and end > start:
        content = content[start:end]
    questions = json.loads(content)
    validated = []
    for i, q in enumerate(questions[:5]):
        validated.append({
            "id": i + 1,
            "question": str(q.get("question", "")),
            "topic": str(q.get("topic", "Technical")),
        })
    return validated


def _generate_via_langchain(prompt_text: str) -> str:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    llm = ChatOpenAI(
        model="anthropic/claude-3-haiku",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=1024,
    )
    response = llm.invoke([HumanMessage(content=prompt_text)])
    return response.content.strip()


def _generate_via_requests(prompt_text: str) -> str:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
        json={
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": prompt_text}],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def generate_questions(
    skills: List[str],
    role: str,
    chunks: List[Dict],
    experience_level: str = "intermediate",
) -> List[Dict]:
    """
    Generate 5 tailored interview questions.

    `chunks` is now a list of dicts: {"text": ..., "source": ..., "chunk_index": ...}.
    All 5 questions share the same retrieved chunk set, so each question is stamped
    with the same `source_chunks` metadata list for full traceability.

    Primary LLM path: LangChain (ChatOpenAI via OpenRouter)
    Fallback: Direct requests to OpenRouter API
    """
    chunks_text = _extract_chunk_texts(chunks)[:3000]
    source_metadata = _build_source_chunks_metadata(chunks)
    skills_text = ", ".join(skills)
    level_hint = DIFFICULTY_HINTS.get(experience_level, DIFFICULTY_HINTS["intermediate"])

    prompt_text = QUESTION_PROMPT_TEMPLATE.format(
        skills=skills_text,
        role=role,
        level_hint=level_hint,
        retrieved_chunks=chunks_text,
    )

    try:
        content = _generate_via_langchain(prompt_text)
    except Exception as lc_err:
        print(f"LangChain generation failed ({lc_err}), falling back to direct API")
        content = _generate_via_requests(prompt_text)

    questions = _parse_questions(content)

    # Stamp every question with the full set of source chunk metadata
    for q in questions:
        q["source_chunks"] = source_metadata

    return questions
