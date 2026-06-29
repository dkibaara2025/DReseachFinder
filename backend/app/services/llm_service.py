import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GOOGLE_AI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"


async def generate_section(
    section: str,
    grant_info: dict,
    user_profile: dict,
    relevant_papers: list[dict],
    existing_content: dict | None = None,
) -> str:
    """Generate a proposal section using LLM. Falls back from OpenRouter to Google AI."""
    prompt = _build_prompt(section, grant_info, user_profile, relevant_papers, existing_content)

    # Try OpenRouter first
    if settings.openrouter_api_key:
        try:
            return await _call_openrouter(prompt)
        except Exception as e:
            logger.warning(f"OpenRouter failed, falling back to Google AI: {e}")

    # Fallback to Google AI Studio
    if settings.google_ai_studio_api_key:
        try:
            return await _call_google_ai(prompt)
        except Exception as e:
            logger.error(f"Google AI Studio failed: {e}")

    return f"[LLM unavailable] Please write the {section} section manually."


async def _call_openrouter(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert academic grant writer. Write clear, compelling, and well-structured grant proposal sections.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 2000,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_google_ai(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{GOOGLE_AI_URL}?key={settings.google_ai_studio_api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 2000, "temperature": 0.7},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return ""


def _build_prompt(
    section: str,
    grant_info: dict,
    user_profile: dict,
    relevant_papers: list[dict],
    existing_content: dict | None = None,
) -> str:
    papers_text = ""
    for i, p in enumerate(relevant_papers[:10], 1):
        authors = ", ".join(p.get("authors", [])[:3])
        papers_text += f"{i}. {p.get('title', '')} ({authors}, {p.get('year', 'n.d.')})\n"

    existing_text = ""
    if existing_content:
        for key, val in existing_content.items():
            if val and key != section:
                existing_text += f"\n--- {key.upper()} (already written) ---\n{val[:500]}\n"

    section_instructions = {
        "background": "Write a compelling background/introduction section that establishes the context, significance, and novelty of the proposed research.",
        "goals": "Write clear, specific research goals and objectives that are measurable and achievable within the grant timeline.",
        "methodology": "Write a detailed methodology section outlining the research design, methods, data collection, and analysis plans.",
        "outcomes": "Write an expected outcomes section describing anticipated results, their significance, and broader impacts.",
        "references": "Compile and format the reference list based on the cited papers.",
    }

    return f"""Write the "{section}" section of a grant proposal.

GRANT INFORMATION:
- Title: {grant_info.get('title', 'N/A')}
- Agency: {grant_info.get('agency', 'N/A')}
- Description: {grant_info.get('description', 'N/A')[:500]}
- Eligibility: {grant_info.get('eligibility', 'N/A')}

RESEARCHER PROFILE:
- Name: {user_profile.get('name', 'N/A')}
- Institution: {user_profile.get('institution', 'N/A')}
- Research Interests: {', '.join(user_profile.get('research_interests', []))}
- Key Publications: {user_profile.get('publication_summary', 'N/A')}

RELEVANT LITERATURE:
{papers_text}

{existing_text}

INSTRUCTIONS: {section_instructions.get(section, 'Write this section professionally.')}

Write in academic English. Be specific and evidence-based. Reference the relevant literature where appropriate using [Author, Year] format."""
