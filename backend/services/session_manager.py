import uuid
import json
import aiosqlite
from typing import List, Dict, Optional


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
            "INSERT INTO questions (session_id, question_index, question, topic, source_chunks) VALUES (?, ?, ?, ?, ?)",
            (session_id, i, q["question"], q["topic"], source_chunks_json),
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
        "SELECT id, question_index, question, topic, source_chunks FROM questions WHERE session_id = ? ORDER BY question_index",
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
        total = row["cnt"] if row else 5

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
        SELECT q.id as question_id, q.question, q.topic,
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
    }
