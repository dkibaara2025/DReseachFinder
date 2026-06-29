"""Tests for app.services.llm_service module."""
from app.services.llm_service import _build_prompt


class TestBuildPrompt:
    def test_basic_prompt_structure(self):
        prompt = _build_prompt(
            section="background",
            grant_info={"title": "AI Grant", "agency": "NSF", "description": "Fund AI research", "eligibility": "US researchers"},
            user_profile={"name": "Dr. Smith", "institution": "MIT", "research_interests": ["AI", "ML"], "publication_summary": "10 papers"},
            relevant_papers=[
                {"title": "Paper 1", "authors": ["Alice"], "year": 2023},
                {"title": "Paper 2", "authors": ["Bob"], "year": 2024},
            ],
        )
        assert "background" in prompt
        assert "AI Grant" in prompt
        assert "NSF" in prompt
        assert "Dr. Smith" in prompt
        assert "MIT" in prompt
        assert "Paper 1" in prompt
        assert "Paper 2" in prompt

    def test_all_sections_have_instructions(self):
        for section in ["background", "goals", "methodology", "outcomes", "references"]:
            prompt = _build_prompt(
                section=section,
                grant_info={"title": "T", "agency": "A", "description": "D", "eligibility": "E"},
                user_profile={"name": "N", "institution": "I", "research_interests": [], "publication_summary": ""},
                relevant_papers=[],
            )
            assert section in prompt

    def test_existing_content_included(self):
        prompt = _build_prompt(
            section="methodology",
            grant_info={"title": "T", "agency": "A", "description": "D", "eligibility": "E"},
            user_profile={"name": "N", "institution": "I", "research_interests": [], "publication_summary": ""},
            relevant_papers=[],
            existing_content={"background": "Existing background text here"},
        )
        assert "BACKGROUND" in prompt
        assert "Existing background text here" in prompt

    def test_empty_papers_handled(self):
        prompt = _build_prompt(
            section="goals",
            grant_info={"title": "T", "agency": "A", "description": "D", "eligibility": "E"},
            user_profile={"name": "N", "institution": "I", "research_interests": [], "publication_summary": ""},
            relevant_papers=[],
        )
        assert "goals" in prompt

    def test_research_interests_listed(self):
        prompt = _build_prompt(
            section="background",
            grant_info={"title": "T", "agency": "A", "description": "D", "eligibility": "E"},
            user_profile={
                "name": "N",
                "institution": "I",
                "research_interests": ["NLP", "Computer Vision"],
                "publication_summary": "",
            },
            relevant_papers=[],
        )
        assert "NLP" in prompt
        assert "Computer Vision" in prompt
