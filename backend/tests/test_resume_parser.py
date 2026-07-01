"""
Unit tests for resume_parser service.
Tests skill extraction, name detection, and experience level detection
without requiring a real PDF — uses raw text strings instead.
"""

import pytest
from services.resume_parser import (
    extract_candidate_name,
    extract_skills,
    detect_experience_level,
)


class TestExtractCandidateName:
    def test_simple_name_on_first_line(self):
        text = "John Doe\nSoftware Engineer\nSome Company"
        assert extract_candidate_name(text) == "John Doe"

    def test_name_with_three_parts(self):
        text = "Alice Marie Smith\nML Engineer"
        assert extract_candidate_name(text) == "Alice Marie Smith"

    def test_fallback_when_line_has_digits(self):
        text = "Phone: 123-456-7890\nJohn Doe"
        assert extract_candidate_name(text) == "Candidate"

    def test_empty_text_returns_fallback(self):
        assert extract_candidate_name("") == "Candidate"

    def test_name_too_many_words_returns_fallback(self):
        text = "This is a very long first line with many words\nJohn Doe"
        assert extract_candidate_name(text) == "Candidate"


class TestExtractSkills:
    def test_detects_python(self):
        text = "I have experience with Python and machine learning"
        skills = extract_skills(text)
        assert "Python" in skills

    def test_detects_multiple_skills(self):
        text = "Skills: Python, PyTorch, Docker, PostgreSQL, FastAPI, Redis"
        skills = extract_skills(text)
        assert len(skills) >= 4

    def test_case_insensitive_detection(self):
        text = "PYTORCH and TENSORFLOW are my main frameworks"
        skills = extract_skills(text)
        assert "Pytorch" in skills or "Tensorflow" in skills

    def test_returns_default_when_no_skills_found(self):
        text = "I enjoy hiking and cooking on weekends"
        skills = extract_skills(text)
        assert len(skills) > 0
        assert "Python" in skills or "Machine Learning" in skills

    def test_max_fifteen_skills_returned(self):
        text = " ".join([
            "python pytorch tensorflow keras scikit-learn numpy pandas",
            "matplotlib docker kubernetes aws gcp azure postgresql",
            "mongodb redis elasticsearch fastapi flask django",
        ])
        skills = extract_skills(text)
        assert len(skills) <= 15

    def test_no_duplicates(self):
        text = "python python python machine learning machine learning"
        skills = extract_skills(text)
        assert len(skills) == len(set(skills))


class TestDetectExperienceLevel:
    def test_senior_keyword_returns_advanced(self):
        text = "Senior Software Engineer with 7 years of experience"
        skills = ["Python", "Docker", "Kubernetes", "AWS"]
        assert detect_experience_level(text, skills) == "advanced"

    def test_fresher_keyword_returns_beginner(self):
        text = "Fresher looking for first opportunity in ML"
        skills = ["Python"]
        assert detect_experience_level(text, skills) == "beginner"

    def test_years_experience_advanced(self):
        text = "5 years of experience building ML systems"
        skills = ["Python", "PyTorch", "Docker"]
        assert detect_experience_level(text, skills) == "advanced"

    def test_no_keywords_intermediate(self):
        text = "Software engineer with 2 years experience"
        skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "AWS"]
        assert detect_experience_level(text, skills) == "intermediate"

    def test_many_skills_advanced(self):
        text = "Generalist engineer"
        skills = [
            "Python", "PyTorch", "TensorFlow", "Docker", "Kubernetes",
            "AWS", "PostgreSQL", "Redis", "FastAPI", "Spark",
            "Kafka", "Airflow", "Bert", "Gpt"
        ]
        assert detect_experience_level(text, skills) == "advanced"
