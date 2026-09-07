"""
Thin OpenAI wrapper. Never fabricates a response: if OPENAI_API_KEY is not
configured, callers get a clear (key_configured=False) signal instead of a
silently mocked answer.
"""
from openai import OpenAI

from core import config


def is_configured() -> bool:
    return bool(config.OPENAI_API_KEY)


def client() -> OpenAI:
    return OpenAI(api_key=config.OPENAI_API_KEY)


def respond(messages, tools=None):
    """
    Calls the Responses API and returns .output_text.
    Raises whatever exception OpenAI raises; callers decide how to report it
    (Engola never claims success on failure).
    """
    resp = client().responses.create(
        model=config.ENGOLA_MODEL,
        input=messages,
        tools=tools or [{"type": "web_search_preview"}],
    )
    return resp.output_text
