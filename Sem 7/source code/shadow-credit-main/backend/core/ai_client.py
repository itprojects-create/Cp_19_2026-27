import asyncio
import json
import logging
from functools import lru_cache

from groq import Groq

try:
    from backend.config import get_settings
except ModuleNotFoundError:
    from config import get_settings


logger = logging.getLogger(__name__)


@lru_cache()
def _get_client() -> Groq:
    settings = get_settings()
    api_key = str(getattr(settings, "GROQ_API_KEY", "") or "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Set it in backend/.env")
    return Groq(api_key=api_key)


def _get_default_model() -> str:
    settings = get_settings()
    return str(getattr(settings, "GROQ_MODEL", "llama-3.1-70b-versatile") or "llama-3.1-70b-versatile")


def groq_complete(
    system_prompt: str,
    user_content: str,
    json_mode: bool = False,
    max_tokens: int = 1500,
    temperature: float = 0.2,
) -> str:
    kwargs = {
        "model": _get_default_model(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = _get_client().chat.completions.create(**kwargs)
    return ((response.choices or [{}])[0].message.content or "").strip()


def groq_complete_json(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 1500,
    temperature: float = 0.2,
):
    raw = groq_complete(
        system_prompt=system_prompt,
        user_content=user_content,
        json_mode=True,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        clean = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)


async def groq_complete_async(
    system_prompt: str,
    user_content: str,
    json_mode: bool = False,
    max_tokens: int = 1500,
    temperature: float = 0.2,
) -> str:
    return await asyncio.to_thread(
        groq_complete,
        system_prompt,
        user_content,
        json_mode,
        max_tokens,
        temperature,
    )


async def groq_complete_json_async(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 1500,
    temperature: float = 0.2,
):
    return await asyncio.to_thread(
        groq_complete_json,
        system_prompt,
        user_content,
        max_tokens,
        temperature,
    )
