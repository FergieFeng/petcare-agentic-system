import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from src.agents.jd_analysis.prompt import SYSTEM_PROMPT, build_user_prompt
from src.agents.jd_analysis.schemas import JDAnalysisOutput
from src.shared.llm import build_llm


class JDAnalysisError(Exception):
    pass


def _extract_json(raw_text: str) -> Dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise JDAnalysisError(f"Model response is not valid JSON: {exc}") from exc


def run_jd_analysis(job_description: str) -> Dict[str, Any]:
    if not job_description or not job_description.strip():
        raise JDAnalysisError("job_description cannot be empty.")

    llm = build_llm()
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=build_user_prompt(job_description)),
        ]
    )

    raw = response.content if isinstance(response.content, str) else str(response.content)
    parsed = _extract_json(raw)
    try:
        validated = JDAnalysisOutput.model_validate(parsed)
    except ValidationError as exc:
        raise JDAnalysisError(f"Schema validation failed: {exc}") from exc
    return validated.model_dump()
