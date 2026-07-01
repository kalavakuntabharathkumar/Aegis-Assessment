"""
Round-specific question generators for the 3-round interview structure.

  - generate_aptitude_questions(count)          → pure logical/quantitative reasoning
  - generate_hr_questions(skills, role, count)  → behavioral / culture-fit
  - generate_technical_questions(...)           → RAG-grounded technical (same pattern as
                                                  question_generator.py, but count-parameterised)

LLM path: LangChain primary → direct OpenRouter requests fallback (mirrors question_generator.py).
Every function has a hardcoded fallback list so a session never fails to start due to one round.
"""

import os
import json
import requests
from typing import List, Dict

DIFFICULTY_HINTS = {
    "beginner":     "Ask foundational conceptual questions. Test understanding of core principles.",
    "intermediate": "Mix conceptual and applied questions. Test both theory and practical implementation.",
    "advanced":     "Ask deep technical questions requiring expert knowledge. Test architectural decisions and edge cases.",
}

# ─── LLM helpers (same pattern as question_generator.py) ──────────────────────

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


def _call_llm(prompt_text: str) -> str:
    """LangChain primary, requests fallback — same two-step pattern as question_generator.py."""
    try:
        return _generate_via_langchain(prompt_text)
    except Exception as lc_err:
        print(f"[round_generator] LangChain failed ({lc_err}), falling back to direct API")
        return _generate_via_requests(prompt_text)


def _parse_json_array(content: str, max_count: int, default_topic: str, round_tag: str) -> List[Dict]:
    """Extract, validate, and normalise a JSON array of question dicts from LLM output."""
    start = content.find("[")
    end = content.rfind("]") + 1
    if start != -1 and end > start:
        content = content[start:end]
    raw = json.loads(content)
    result = []
    for i, q in enumerate(raw[:max_count]):
        result.append({
            "id": i + 1,
            "question": str(q.get("question", "")),
            "topic": str(q.get("topic", default_topic)),
            "round": round_tag,
            "source_chunks": [],
        })
    return result


# ─── Aptitude ─────────────────────────────────────────────────────────────────

APTITUDE_PROMPT = """You are a psychometric test designer.
Generate exactly {count} aptitude interview questions covering numerical reasoning, logical puzzles,
and pattern recognition. These questions must NOT be role-specific or resume-specific — they test
general reasoning ability applicable to any technical candidate.

Rules:
- Every question must be self-contained (no external data needed to answer)
- Mix numerical estimation, sequence completion, and logical deduction
- Suitable for a software/data/ML candidate but not tied to any specific technology
- Return ONLY a valid JSON array, no other text:
  [{{"id": 1, "question": "...", "topic": "Numerical Reasoning"}}, ...]
"""

_APTITUDE_FALLBACK = [
    {"question": "A server processes 1,000 requests per second. If traffic doubles every 6 months, how many requests per second will it need to handle in 18 months?", "topic": "Numerical Reasoning"},
    {"question": "In the sequence 2, 6, 12, 20, 30 — what is the next number, and what is the rule?", "topic": "Pattern Recognition"},
    {"question": "You have a 3-litre jug and a 5-litre jug with no markings. How do you measure exactly 4 litres of water?", "topic": "Logical Reasoning"},
]


def generate_aptitude_questions(count: int = 2) -> List[Dict]:
    """
    Generate `count` pure aptitude/reasoning questions.
    Not role- or resume-specific. No RAG retrieval.
    Returns list of dicts with keys: id, question, topic, round, source_chunks.
    """
    prompt = APTITUDE_PROMPT.format(count=count)
    try:
        content = _call_llm(prompt)
        questions = _parse_json_array(content, max_count=count, default_topic="Aptitude", round_tag="aptitude")
        if not questions:
            raise ValueError("Empty question list returned")
        return questions
    except Exception as e:
        print(f"[round_generator] Aptitude generation failed ({e}), using fallback")
        return [
            {**q, "id": i + 1, "round": "aptitude", "source_chunks": []}
            for i, q in enumerate(_APTITUDE_FALLBACK[:count])
        ]


# ─── HR / Behavioral ──────────────────────────────────────────────────────────

HR_PROMPT = """You are an experienced HR interviewer.
Generate exactly {count} behavioral interview questions for a candidate applying for the role of {role}.
The candidate's skills include: {skills}.

Focus on real workplace situations — teamwork, conflict resolution, ownership, communication,
and career motivation. Use STAR-method-appropriate framing (situation/task/action/result).

Rules:
- Tailor questions to the {role} context where possible
- Do NOT ask about specific algorithms or technologies — this is the behavioral round
- Return ONLY a valid JSON array, no other text:
  [{{"id": 1, "question": "...", "topic": "Teamwork"}}, ...]
"""

_HR_FALLBACK = [
    {"question": "Tell me about a time you had to collaborate with a team member whose working style was very different from yours. How did you handle it?", "topic": "Teamwork"},
    {"question": "Describe a situation where you had to meet a tight deadline. What steps did you take and what was the outcome?", "topic": "Time Management"},
    {"question": "Where do you see your career in three years, and how does this role fit into that path?", "topic": "Career Motivation"},
]


def generate_hr_questions(skills: List[str], role: str, count: int = 2) -> List[Dict]:
    """
    Generate `count` behavioral/HR questions tailored to the candidate's skills and role.
    No RAG retrieval needed.
    Returns list of dicts with keys: id, question, topic, round, source_chunks.
    """
    skills_text = ", ".join(skills[:10]) if skills else "software engineering"
    prompt = HR_PROMPT.format(count=count, role=role, skills=skills_text)
    try:
        content = _call_llm(prompt)
        questions = _parse_json_array(content, max_count=count, default_topic="Behavioral", round_tag="hr")
        if not questions:
            raise ValueError("Empty question list returned")
        return questions
    except Exception as e:
        print(f"[round_generator] HR generation failed ({e}), using fallback")
        return [
            {**q, "id": i + 1, "round": "hr", "source_chunks": []}
            for i, q in enumerate(_HR_FALLBACK[:count])
        ]


# ─── Technical (RAG-grounded, count-parameterised) ────────────────────────────

TECHNICAL_PROMPT = """You are an expert technical interviewer.
Based on the following ML/engineering textbook content and candidate resume,
generate exactly {count} technical interview questions.

Candidate Skills: {skills}
Target Role: {role}
Experience Level: {level_hint}
Knowledge Base Context: {retrieved_chunks}

Rules:
- Questions must be specific to the candidate's background
- Questions must be grounded in the retrieved textbook content above
- {level_hint}
- No generic questions like "what is machine learning"
- Return ONLY a valid JSON array, no other text:
  [{{"id": 1, "question": "...", "topic": "..."}}, ...]
"""

_TECHNICAL_FALLBACK = [
    {"question": "Explain the bias-variance tradeoff and describe a concrete situation where you had to balance the two.", "topic": "Model Theory"},
    {"question": "Walk me through how you would design a scalable REST API for a real-time prediction service.", "topic": "System Design"},
    {"question": "What is gradient descent and why do practitioners often prefer mini-batch over full-batch variants?", "topic": "Optimisation"},
    {"question": "How does cross-validation help prevent overfitting, and when might k-fold be a poor choice?", "topic": "Validation"},
    {"question": "Compare SQL and NoSQL databases for storing model training metadata. When would you pick each?", "topic": "Data Storage"},
    {"question": "Describe a production incident you debugged. What was your process for isolating and fixing the root cause?", "topic": "Debugging"},
]


def generate_technical_questions(
    skills: List[str],
    role: str,
    chunks: List[Dict],
    experience_level: str = "intermediate",
    count: int = 6,
) -> List[Dict]:
    """
    Generate `count` RAG-grounded technical questions.
    Uses the same LangChain → requests two-step pattern as question_generator.py,
    but parameterised on count so we can ask for 6 instead of the original 5.

    `chunks` is a list of dicts: {"text": ..., "source": ..., "chunk_index": ...}.
    All questions are stamped with source_chunk metadata for traceability.
    Returns list of dicts with keys: id, question, topic, round, source_chunks.
    """
    # Extract text and metadata from chunks
    texts = [c["text"] if isinstance(c, dict) else str(c) for c in chunks]
    chunks_text = "\n\n".join(texts)[:3000] if texts else "General ML and backend engineering concepts"
    source_metadata = [
        {"source": c.get("source", "unknown"), "chunk_index": c.get("chunk_index", 0)}
        for c in chunks
        if isinstance(c, dict)
    ]

    skills_text = ", ".join(skills)
    level_hint = DIFFICULTY_HINTS.get(experience_level, DIFFICULTY_HINTS["intermediate"])
    prompt = TECHNICAL_PROMPT.format(
        count=count,
        skills=skills_text,
        role=role,
        level_hint=level_hint,
        retrieved_chunks=chunks_text,
    )

    try:
        content = _call_llm(prompt)
        questions = _parse_json_array(content, max_count=count, default_topic="Technical", round_tag="technical")
        if not questions:
            raise ValueError("Empty question list returned")
    except Exception as e:
        print(f"[round_generator] Technical generation failed ({e}), using fallback")
        questions = [
            {**q, "id": i + 1, "round": "technical", "source_chunks": []}
            for i, q in enumerate(_TECHNICAL_FALLBACK[:count])
        ]
        return questions

    # Stamp every question with source chunk metadata (same as question_generator.py)
    for q in questions:
        q["source_chunks"] = source_metadata

    return questions
