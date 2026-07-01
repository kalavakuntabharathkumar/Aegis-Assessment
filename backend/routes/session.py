from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
import aiosqlite
from database.db import get_db
from models.schemas import SessionStartResponse, SessionDetail, InterviewQuestion
from services.resume_parser import parse_resume, detect_experience_level
from services.rag_service import retrieve_relevant_chunks
from services.question_generator import generate_questions
from services.session_manager import create_session, get_session as fetch_session

router = APIRouter()


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session(
    resume: UploadFile = File(...),
    role: str = Form(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await resume.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    candidate_name, extracted_skills, resume_text = parse_resume(pdf_bytes)

    experience_level = detect_experience_level(resume_text, extracted_skills)

    chunks = retrieve_relevant_chunks(extracted_skills, resume_text)

    raw_questions = generate_questions(extracted_skills, role, chunks, experience_level)

    if not raw_questions:
        raise HTTPException(status_code=500, detail="Failed to generate interview questions")

    session_id = await create_session(db, candidate_name, role, extracted_skills, raw_questions, experience_level)

    session = await fetch_session(db, session_id)

    questions = [
        InterviewQuestion(
            id=q["id"],
            question=q["question"],
            topic=q["topic"],
            source_chunks=q.get("source_chunks") or None,
        )
        for q in session["questions"]
    ]

    return SessionStartResponse(
        session_id=session_id,
        candidate_name=candidate_name,
        role=role,
        extracted_skills=extracted_skills,
        questions=questions,
        total_questions=len(questions),
        experience_level=experience_level,
    )


@router.get("/session/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    session = await fetch_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    questions = [
        InterviewQuestion(
            id=q["id"],
            question=q["question"],
            topic=q["topic"],
            source_chunks=q.get("source_chunks") or None,
        )
        for q in session["questions"]
    ]

    return SessionDetail(
        session_id=session["session_id"],
        candidate_name=session["candidate_name"],
        role=session["role"],
        extracted_skills=session["extracted_skills"],
        questions=questions,
        status=session["status"],
        answers_count=session["answers_count"],
        total_questions=session["total_questions"],
        experience_level=session.get("experience_level", "intermediate"),
    )
