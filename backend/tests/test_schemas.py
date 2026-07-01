"""
Unit tests for Pydantic schemas / models.
Validates that models accept valid data and reject invalid data correctly.
"""

import pytest
from pydantic import ValidationError
from models.schemas import (
    InterviewQuestion,
    SessionStartResponse,
    AnswerInput,
    AnswerResponse,
    QuestionAnswer,
    InterviewSummary,
)


class TestInterviewQuestion:
    def test_valid_question(self):
        q = InterviewQuestion(id=1, question="What is a transformer?", topic="NLP")
        assert q.id == 1
        assert q.topic == "NLP"

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            InterviewQuestion(question="What is a transformer?", topic="NLP")

    def test_missing_question_raises(self):
        with pytest.raises(ValidationError):
            InterviewQuestion(id=1, topic="NLP")


class TestAnswerInput:
    def test_valid_input(self):
        a = AnswerInput(session_id="abc-123", question_id=1, answer="My answer here")
        assert a.session_id == "abc-123"

    def test_missing_session_id_raises(self):
        with pytest.raises(ValidationError):
            AnswerInput(question_id=1, answer="My answer")


class TestAnswerResponse:
    def test_minimal_response(self):
        r = AnswerResponse(
            success=True,
            next_question_index=1,
            is_complete=False,
            message="Question 2 of 5",
        )
        assert r.score is None
        assert r.feedback is None

    def test_full_response_with_score(self):
        r = AnswerResponse(
            success=True,
            next_question_index=2,
            is_complete=False,
            message="Question 3 of 5",
            score=8,
            feedback="Good answer",
            strength="Clear explanation of concepts",
            improvement="Could mention edge cases",
        )
        assert r.score == 8


class TestSessionStartResponse:
    def test_valid_session(self):
        questions = [
            InterviewQuestion(id=1, question="Q1?", topic="ML"),
            InterviewQuestion(id=2, question="Q2?", topic="Backend"),
        ]
        s = SessionStartResponse(
            session_id="sess-001",
            candidate_name="Jane Doe",
            role="ML Engineer",
            extracted_skills=["Python", "PyTorch"],
            questions=questions,
            total_questions=2,
            experience_level="intermediate",
        )
        assert s.total_questions == 2
        assert len(s.questions) == 2


class TestInterviewSummary:
    def test_summary_with_no_answers(self):
        qa = QuestionAnswer(
            question_id=1,
            question="What is backpropagation?",
            topic="Deep Learning",
            answer=None,
            answered=False,
        )
        summary = InterviewSummary(
            session_id="sess-001",
            candidate_name="Test User",
            role="ML Intern",
            extracted_skills=["Python"],
            qa_pairs=[qa],
            topics_covered=["Deep Learning"],
            completion_status="incomplete",
            total_questions=1,
            answered_count=0,
            experience_level="beginner",
        )
        assert summary.answered_count == 0
        assert summary.qa_pairs[0].answered is False
