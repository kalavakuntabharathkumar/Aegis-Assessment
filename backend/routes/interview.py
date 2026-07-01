import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
import aiosqlite
from database.db import get_db
from models.schemas import AnswerInput, AnswerResponse, InterviewSummary, QuestionAnswer
from services.session_manager import save_answer, get_summary as fetch_summary, get_session
from services.answer_scorer import score_answer

router = APIRouter()


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    payload: AnswerInput,
    db: aiosqlite.Connection = Depends(get_db),
):
    session = await get_session(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not payload.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty")

    # Find the question text and topic for scoring
    question_text = ""
    question_topic = ""
    for q in session["questions"]:
        if q["id"] == payload.question_id:
            question_text = q["question"]
            question_topic = q["topic"]
            break

    # Score the answer (non-blocking — fails gracefully)
    score_data = None
    try:
        score_data = await asyncio.to_thread(
            score_answer, question_text, payload.answer, question_topic
        )
    except Exception:
        pass

    answers_count = await save_answer(
        db,
        payload.session_id,
        payload.question_id,
        payload.answer,
        score=score_data.get("score") if score_data else None,
        feedback=score_data.get("feedback") if score_data else None,
        strength=score_data.get("strength") if score_data else None,
        improvement=score_data.get("improvement") if score_data else None,
    )

    total = session["total_questions"]
    is_complete = answers_count >= total
    next_index = answers_count

    return AnswerResponse(
        success=True,
        next_question_index=next_index,
        is_complete=is_complete,
        message="Interview complete!" if is_complete else f"Question {next_index + 1} of {total}",
        score=score_data.get("score") if score_data else None,
        feedback=score_data.get("feedback") if score_data else None,
        strength=score_data.get("strength") if score_data else None,
        improvement=score_data.get("improvement") if score_data else None,
    )


@router.get("/summary/{session_id}", response_model=InterviewSummary)
async def get_summary(
    session_id: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    summary = await fetch_summary(db, session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    qa_pairs = [
        QuestionAnswer(
            question_id=qa["question_id"],
            question=qa["question"],
            topic=qa["topic"],
            answer=qa["answer"],
            answered=qa["answered"],
            score=qa.get("score"),
            feedback=qa.get("feedback"),
            strength=qa.get("strength"),
            improvement=qa.get("improvement"),
        )
        for qa in summary["qa_pairs"]
    ]

    return InterviewSummary(
        session_id=summary["session_id"],
        candidate_name=summary["candidate_name"],
        role=summary["role"],
        extracted_skills=summary["extracted_skills"],
        qa_pairs=qa_pairs,
        topics_covered=summary["topics_covered"],
        completion_status=summary["completion_status"],
        total_questions=summary["total_questions"],
        answered_count=summary["answered_count"],
        experience_level=summary.get("experience_level", "intermediate"),
    )


@router.get("/report/{session_id}")
async def download_report(
    session_id: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    summary = await fetch_summary(db, session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    scores = [qa["score"] for qa in summary["qa_pairs"] if qa.get("score") is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    if avg_score is None:
        overall_rating = "N/A"
    elif avg_score >= 8:
        overall_rating = "Excellent"
    elif avg_score >= 6:
        overall_rating = "Good"
    elif avg_score >= 4:
        overall_rating = "Fair"
    else:
        overall_rating = "Needs Work"

    level_map = {"beginner": "Entry Level", "intermediate": "Mid Level", "advanced": "Senior Level"}
    level_label = level_map.get(summary.get("experience_level", "intermediate"), "Mid Level")

    lines = [
        "╔══════════════════════════════════════════════════════╗",
        "║           AEGIS ASSESSMENT — INTERVIEW REPORT        ║",
        "╚══════════════════════════════════════════════════════╝",
        "",
        f"Candidate:     {summary['candidate_name']}",
        f"Role:          {summary['role']}",
        f"Date:          {datetime.now().strftime('%B %d, %Y')}",
        f"Experience:    {level_label}",
        f"Status:        {summary['completion_status']}",
        "",
        "━" * 54,
        "SKILLS ASSESSED",
        "━" * 54,
        ", ".join(summary["extracted_skills"]) or "N/A",
        "",
        "━" * 54,
        "TOPICS COVERED",
        "━" * 54,
        ", ".join(summary["topics_covered"]) or "N/A",
        "",
        "━" * 54,
        "PERFORMANCE SUMMARY",
        "━" * 54,
        f"Questions Answered: {summary['answered_count']}/{summary['total_questions']}",
        f"Average Score:      {avg_score}/10" if avg_score is not None else "Average Score:      N/A",
        f"Overall Rating:     {overall_rating}",
        "",
        "━" * 54,
        "DETAILED Q&A REVIEW",
        "━" * 54,
    ]

    for i, qa in enumerate(summary["qa_pairs"]):
        score_str = f"{qa['score']}/10" if qa.get("score") is not None else "N/A"
        lines += [
            "",
            f"Q{i + 1} [{qa['topic']}] — Score: {score_str}",
            qa["question"],
            "",
            "Your Answer:",
            qa["answer"] or "(no response provided)",
        ]
        if qa.get("feedback"):
            lines.append(f"\nFeedback: {qa['feedback']}")
        if qa.get("strength"):
            lines.append(f"Strength: {qa['strength']}")
        if qa.get("improvement"):
            lines.append(f"Improve:  {qa['improvement']}")
        lines.append("─" * 54)

    lines += [
        "",
        "━" * 54,
        "Generated by Aegis Assessment • Powered by Claude AI",
        "━" * 54,
    ]

    content = "\n".join(lines)
    filename = f"aegis_report_{session_id[:8]}.txt"

    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
