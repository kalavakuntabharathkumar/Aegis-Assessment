import os
import uuid
import json
import requests
from typing import List, Dict, Optional

import aiosqlite


DIFFICULTY_HINTS = {
    "beginner": "Ask foundational questions. Test understanding of core principles.",
    "intermediate": "Mix conceptual and applied questions.",
    "advanced": "Ask deep technical questions requiring expert knowledge.",
}

APTITUDE_PROMPT = """You are an expert technical interviewer.
Generate exactly {count} aptitude and logical reasoning interview questions for a {role} candidate.
Candidate skills: {skills}
Difficulty: {level_hint}

Focus on: logical reasoning, algorithmic thinking, estimation, pattern recognition relevant to {role}.
Return ONLY a valid JSON array, no other text:
[{{"id": 1, "question": "...", "topic": "Logical Reasoning"}}, ...]
"""

HR_PROMPT = """You are an expert HR interviewer.
Generate exactly {count} behavioral interview questions for a {role} candidate at {level} level.

Focus on: teamwork, conflict resolution, motivation, growth mindset, communication.
Use STAR-method appropriate situations.
Return ONLY a valid JSON array, no other text:
[{{"id": 1, "question": "...", "topic": "Behavioral"}}, ...]
"""


def _call_openrouter(prompt: str, timeout: int = 30) -> str:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
        json={
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _parse_question_json(content: str) -> List[Dict]:
    start = content.find("[")
    end = content.rfind("]") + 1
    if start != -1 and end > start:
        content = content[start:end]
    return json.loads(content)


def _generate_aptitude_questions(
    skills: List[str], role: str, experience_level: str, count: int = 2
) -> List[Dict]:
    level_hint = DIFFICULTY_HINTS.get(experience_level, DIFFICULTY_HINTS["intermediate"])
    prompt = APTITUDE_PROMPT.format(
        count=count,
        role=role,
        skills=", ".join(skills[:8]),
        level_hint=level_hint,
    )
    try:
        content = _call_openrouter(prompt)
        qs = _parse_question_json(content)
        return [
            {
                "question": str(q["question"]),
                "topic": str(q.get("topic", "Aptitude")),
                "round": "aptitude",
                "source_chunks": [],
            }
            for q in qs[:count]
        ]
    except Exception as e:
        print(f"Aptitude question generation failed ({e}), using fallbacks")
        return [
            {
                "question": f"How would you approach diagnosing a performance bottleneck in a large-scale {role} system?",
                "topic": "Problem Solving",
                "round": "aptitude",
                "source_chunks": [],
            },
            {
                "question": "Given a sorted array of 1 million integers, compare binary search vs linear search in terms of time complexity and when you'd choose each.",
                "topic": "Algorithmic Thinking",
                "round": "aptitude",
                "source_chunks": [],
            },
        ][:count]


def _generate_hr_questions(
    role: str, experience_level: str, count: int = 2
) -> List[Dict]:
    prompt = HR_PROMPT.format(count=count, role=role, level=experience_level)
    try:
        content = _call_openrouter(prompt)
        qs = _parse_question_json(content)
        return [
            {
                "question": str(q["question"]),
                "topic": str(q.get("topic", "Behavioral")),
                "round": "hr",
                "source_chunks": [],
            }
            for q in qs[:count]
        ]
    except Exception as e:
        print(f"HR question generation failed ({e}), using fallbacks")
        return [
            {
                "question": "Tell me about a time you had to collaborate with a difficult team member. How did you handle it?",
                "topic": "Teamwork",
                "round": "hr",
                "source_chunks": [],
            },
            {
                "question": "Where do you see your career in 3 years, and how does this role align with those goals?",
                "topic": "Career Goals",
                "round": "hr",
                "source_chunks": [],
            },
        ][:count]


def assemble_round_questions(
    skills: List[str],
    role: str,
    chunks: List[Dict],
    experience_level: str = "intermediate",
) -> List[Dict]:
    """
    Orchestrates question generation across 3 rounds:
      - 2 aptitude questions
      - 5 technical questions (RAG-grounded via generate_questions())
      - 2 HR/behavioral questions
    Total: 9 questions.
    """
    from services.question_generator import generate_questions

    aptitude_qs = _generate_aptitude_questions(skills, role, experience_level, count=2)

    technical_raw = generate_questions(skills, role, chunks, experience_level)
    technical_qs = [{**q, "round": "technical"} for q in technical_raw]

    hr_qs = _generate_hr_questions(role, experience_level, count=2)

    return aptitude_qs + technical_qs + hr_qs


async def create_session(
    db: aiosqlite.Connection,
    candidate_name: str,
    role: str,
    extracted_skills: List[str],
    questions: List[Dict],
    experience_level: str = "intermediate",
) -> str:
    session_id = str(uuid.uuid4())
    skills_json = json.dumps(extracted_skills)

    await db.execute(
        "INSERT INTO sessions (id, candidate_name, role, extracted_skills, status, experience_level) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, candidate_name, role, skills_json, "in_progress", experience_level),
    )

    for i, q in enumerate(questions):
        source_chunks_json = json.dumps(q.get("source_chunks", []))
        await db.execute(
            "INSERT INTO questions (session_id, question_index, question, topic, source_chunks, round) VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_id,
                i,
                q["question"],
                q["topic"],
                source_chunks_json,
                q.get("round", "technical"),
            ),
        )

    await db.commit()
    return session_id


async def get_session(db: aiosqlite.Connection, session_id: str) -> Optional[Dict]:
    async with db.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ) as cursor:
        session = await cursor.fetchone()

    if not session:
        return None

    async with db.execute(
        "SELECT id, question_index, question, topic, source_chunks, round FROM questions WHERE session_id = ? ORDER BY question_index",
        (session_id,),
    ) as cursor:
        questions_rows = await cursor.fetchall()

    async with db.execute(
        "SELECT COUNT(*) as cnt FROM answers WHERE session_id = ?", (session_id,)
    ) as cursor:
        count_row = await cursor.fetchone()
        answers_count = count_row["cnt"] if count_row else 0

    questions = []
    for q in questions_rows:
        raw_chunks = q["source_chunks"]
        try:
            source_chunks = json.loads(raw_chunks) if raw_chunks else []
        except Exception:
            source_chunks = []
        questions.append({
            "id": q["id"],
            "question": q["question"],
            "topic": q["topic"],
            "round": q["round"] if "round" in q.keys() else "technical",
            "source_chunks": source_chunks,
        })

    return {
        "session_id": session["id"],
        "candidate_name": session["candidate_name"],
        "role": session["role"],
        "extracted_skills": json.loads(session["extracted_skills"]),
        "questions": questions,
        "status": session["status"],
        "answers_count": answers_count,
        "total_questions": len(questions),
        "experience_level": session["experience_level"] if "experience_level" in session.keys() else "intermediate",
    }


async def save_answer(
    db: aiosqlite.Connection,
    session_id: str,
    question_id: int,
    answer: str,
    score: Optional[int] = None,
    feedback: Optional[str] = None,
    strength: Optional[str] = None,
    improvement: Optional[str] = None,
) -> int:
    await db.execute(
        "INSERT INTO answers (session_id, question_id, answer, score, feedback, strength, improvement) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, question_id, answer, score, feedback, strength, improvement),
    )

    async with db.execute(
        "SELECT COUNT(*) as cnt FROM answers WHERE session_id = ?", (session_id,)
    ) as cursor:
        row = await cursor.fetchone()
        answers_count = row["cnt"] if row else 0

    async with db.execute(
        "SELECT COUNT(*) as cnt FROM questions WHERE session_id = ?", (session_id,)
    ) as cursor:
        row = await cursor.fetchone()
        total = row["cnt"] if row else 9

    if answers_count >= total:
        await db.execute(
            "UPDATE sessions SET status = 'completed' WHERE id = ?", (session_id,)
        )

    await db.commit()
    return answers_count


async def get_summary(db: aiosqlite.Connection, session_id: str) -> Optional[Dict]:
    session = await get_session(db, session_id)
    if not session:
        return None

    async with db.execute(
        """
        SELECT q.id as question_id, q.question, q.topic, q.round,
               a.answer, a.score, a.feedback, a.strength, a.improvement
        FROM questions q
        LEFT JOIN answers a ON q.id = a.question_id AND a.session_id = ?
        WHERE q.session_id = ?
        ORDER BY q.question_index
        """,
        (session_id, session_id),
    ) as cursor:
        rows = await cursor.fetchall()

    qa_pairs = []
    topics_covered = []
    answered_count = 0

    for row in rows:
        answered = row["answer"] is not None
        if answered:
            answered_count += 1
            if row["topic"] not in topics_covered:
                topics_covered.append(row["topic"])

        qa_pairs.append({
            "question_id": row["question_id"],
            "question": row["question"],
            "topic": row["topic"],
            "round": row["round"] if "round" in row.keys() else "technical",
            "answer": row["answer"],
            "answered": answered,
            "score": row["score"],
            "feedback": row["feedback"],
            "strength": row["strength"],
            "improvement": row["improvement"],
        })

    total = len(qa_pairs)
    if answered_count == total:
        completion_status = "Completed"
    elif answered_count == 0:
        completion_status = "Not Started"
    else:
        completion_status = f"In Progress ({answered_count}/{total} answered)"

    # Per-round breakdown
    round_breakdown: Dict = {}
    for qa in qa_pairs:
        r = qa["round"]
        if r not in round_breakdown:
            round_breakdown[r] = {"total": 0, "answered": 0, "scores": []}
        round_breakdown[r]["total"] += 1
        if qa["answered"]:
            round_breakdown[r]["answered"] += 1
            if qa["score"] is not None:
                round_breakdown[r]["scores"].append(qa["score"])

    for r in round_breakdown:
        scores = round_breakdown[r].pop("scores")
        round_breakdown[r]["avg_score"] = (
            round(sum(scores) / len(scores), 1) if scores else None
        )

    return {
        "session_id": session_id,
        "candidate_name": session["candidate_name"],
        "role": session["role"],
        "extracted_skills": session["extracted_skills"],
        "qa_pairs": qa_pairs,
        "topics_covered": topics_covered,
        "completion_status": completion_status,
        "total_questions": total,
        "answered_count": answered_count,
        "experience_level": session.get("experience_level", "intermediate"),
        "round_breakdown": round_breakdown,
    }
