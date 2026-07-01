from pydantic import BaseModel
from typing import List, Optional


class ChunkSource(BaseModel):
    source: str
    chunk_index: int


class InterviewQuestion(BaseModel):
    id: int
    question: str
    topic: str
    round: str = "technical"
    source_chunks: Optional[List[ChunkSource]] = None


class SessionStartResponse(BaseModel):
    session_id: str
    candidate_name: str
    role: str
    extracted_skills: List[str]
    questions: List[InterviewQuestion]
    total_questions: int
    experience_level: str


class SessionDetail(BaseModel):
    session_id: str
    candidate_name: str
    role: str
    extracted_skills: List[str]
    questions: List[InterviewQuestion]
    status: str
    answers_count: int
    total_questions: int
    experience_level: str


class AnswerInput(BaseModel):
    session_id: str
    question_id: int
    answer: str


class AnswerResponse(BaseModel):
    success: bool
    next_question_index: int
    is_complete: bool
    message: str
    score: Optional[int] = None
    feedback: Optional[str] = None
    strength: Optional[str] = None
    improvement: Optional[str] = None


class QuestionAnswer(BaseModel):
    question_id: int
    question: str
    topic: str
    round: str = "technical"
    answer: Optional[str]
    answered: bool
    score: Optional[int] = None
    feedback: Optional[str] = None
    strength: Optional[str] = None
    improvement: Optional[str] = None


class InterviewSummary(BaseModel):
    session_id: str
    candidate_name: str
    role: str
    extracted_skills: List[str]
    qa_pairs: List[QuestionAnswer]
    topics_covered: List[str]
    completion_status: str
    total_questions: int
    answered_count: int
    experience_level: str
    round_breakdown: Optional[dict] = None


class ErrorResponse(BaseModel):
    error: str
