"""
LangChain-based question generation service.

Uses LangChain's prompt templates and chains to generate personalised
interview questions grounded in retrieved knowledge-base chunks.
This replaces raw requests calls with LangChain abstractions, enabling
easy model swapping (OpenAI, Anthropic, HuggingFace, etc.).
"""

import os
import json
from typing import List, Dict

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


DIFFICULTY_HINTS = {
    "beginner": "Ask foundational conceptual questions. Test understanding of core principles.",
    "intermediate": "Mix conceptual and applied questions. Test both theory and practical implementation.",
    "advanced": "Ask deep technical questions requiring expert knowledge. Test architectural decisions and edge cases.",
}

QUESTION_TEMPLATE = PromptTemplate(
    input_variables=["skills", "role", "level_hint", "retrieved_chunks"],
    template="""You are an expert technical interviewer.
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
""",
)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="anthropic/claude-3-haiku",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=1024,
    )


def generate_questions_langchain(
    skills: List[str],
    role: str,
    chunks: List[str],
    experience_level: str = "intermediate",
) -> List[Dict]:
    """
    Generate interview questions using a LangChain LCEL chain:
      PromptTemplate | ChatOpenAI | StrOutputParser
    """
    chunks_text = "\n\n".join(chunks) if chunks else "General ML and backend engineering concepts"
    skills_text = ", ".join(skills)
    level_hint = DIFFICULTY_HINTS.get(experience_level, DIFFICULTY_HINTS["intermediate"])

    llm = _build_llm()
    chain = QUESTION_TEMPLATE | llm | StrOutputParser()

    content = chain.invoke(
        {
            "skills": skills_text,
            "role": role,
            "level_hint": level_hint,
            "retrieved_chunks": chunks_text[:3000],
        }
    ).strip()

    start = content.find("[")
    end = content.rfind("]") + 1
    if start != -1 and end > start:
        content = content[start:end]

    questions = json.loads(content)

    validated: List[Dict] = []
    for i, q in enumerate(questions[:5]):
        validated.append(
            {
                "id": i + 1,
                "question": str(q.get("question", "")),
                "topic": str(q.get("topic", "Technical")),
            }
        )
    return validated
