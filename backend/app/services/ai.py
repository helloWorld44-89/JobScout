import json
import re
from typing import Any

from app.core.config import settings


async def parse_resume(resume_text: str) -> dict[str, list[str]]:
    """Call the configured LiteLLM provider to extract skills and keywords from resume text."""
    from litellm import acompletion  # type: ignore[import-untyped]

    prompt = (
        "Extract structured information from this resume. "
        "Return ONLY a JSON object (no markdown fences) with these keys:\n"
        '- "skills": list of technical skills, tools, and technologies\n'
        '- "keywords": list of job-search keywords matching this person\'s background '
        "(job titles, domains, key terms that appear in relevant job postings)\n\n"
        f"Resume:\n{resume_text[:8000]}"
    )

    call_kwargs: dict[str, Any] = {
        "model": settings.AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    if settings.AI_BASE_URL:
        call_kwargs["api_base"] = settings.AI_BASE_URL

    response = await acompletion(**call_kwargs)
    raw: str = response.choices[0].message.content or ""  # type: ignore[union-attr]
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

    try:
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError:
        data = {}

    def _str_list(val: Any) -> list[str]:
        return [str(x) for x in val] if isinstance(val, list) else []

    return {
        "skills": _str_list(data.get("skills")),
        "keywords": _str_list(data.get("keywords")),
    }
