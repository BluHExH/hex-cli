"""Offline identity knowledge for HEX CLI (no network).

Answers common questions about the product without calling an AI provider.
"""

from __future__ import annotations

import re
from typing import Optional

from hex_cli import __version__

PRODUCT_NAME = "HEX CLI"
COMPANY = "NeonBuild"
TAGLINE = "Powered by HEX"

IDENTITY: dict[str, str] = {
    "who": (
        f"I am {PRODUCT_NAME}, a terminal-based AI coding assistant designed to help "
        "developers work with their projects, write code, understand files, and "
        "perform development tasks."
    ),
    "builder": (
        f"I was developed by {COMPANY}, the company behind the {PRODUCT_NAME} project."
    ),
    "company": (
        f"{COMPANY} is the company that created {PRODUCT_NAME}."
    ),
    "powers": (
        f"I am {TAGLINE}, with support for external AI providers when configured "
        "(OpenRouter, Ollama, Groq, Gemini, and other OpenAI-compatible endpoints)."
    ),
    "can_do": (
        f"{PRODUCT_NAME} can help you inspect and edit project files, run approved "
        "tools, manage git-related tasks, work with sessions, and talk to supported "
        "AI models once a provider is configured."
    ),
    "offline": (
        "Yes. I can answer built-in identity and basic product questions offline. "
        "For advanced AI coding, reasoning, and external model responses, configure "
        "a supported AI provider with /provider or /connect."
    ),
    "api_key": (
        "You do not need an API key for offline identity and basic product help. "
        "You need a provider API key (or a local Ollama setup) for full AI coding "
        "assistance. Use /provider to choose a provider and /connect to add a key."
    ),
    "what_is": (
        f"{PRODUCT_NAME} is a professional terminal AI coding agent ({TAGLINE}). "
        f"Created by {COMPANY}. Version {__version__}."
    ),
    "ai": (
        f"I am an AI coding assistant interface. Offline I use built-in product "
        f"knowledge from {COMPANY}. With a configured provider I use external models."
    ),
    "version": f"{PRODUCT_NAME} version {__version__} — {TAGLINE} | By {COMPANY}.",
}

# Patterns ordered by specificity (first match wins)
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(who (built|created|made|developed)|who('?s| is) (your )?(creator|author|maker))\b", re.I), "builder"),
    (re.compile(r"\b(which|what) company\b.*(creat|build|make|develop|behind)", re.I), "company"),
    (re.compile(r"\bwhat is neonbuild\b", re.I), "company"),
    (re.compile(r"\b(who are you|what are you|who('?s| is) this)\b", re.I), "who"),
    (re.compile(r"\bwhat (is|does) hex( cli)?\b", re.I), "what_is"),
    (re.compile(r"\b(what powers you|powered by|what (are you|is your) (powered|engine))\b", re.I), "powers"),
    (re.compile(r"\b(what can you do|your (capabilities|features)|help me with)\b", re.I), "can_do"),
    (re.compile(r"\b(work offline|without (an )?api|need (an )?api key|do you need.*(key|api))\b", re.I), "offline"),
    (re.compile(r"\b(api key|configure provider|how (do i|to) connect)\b", re.I), "api_key"),
    (re.compile(r"\b(are you (an )?ai|are you a (bot|model|llm))\b", re.I), "ai"),
    (re.compile(r"\b(what )?version\b", re.I), "version"),
]


def try_offline_identity(text: str) -> Optional[str]:
    """Return an offline identity answer, or None if the text is not an identity question."""
    q = (text or "").strip()
    if not q or len(q) > 240:
        return None
    # Avoid hijacking coding tasks
    coding_hints = (
        "write ", "fix ", "implement ", "refactor ", "debug ", "create file",
        "edit ", "function", "class ", "import ", "error:", "traceback",
    )
    lower = q.lower()
    if any(h in lower for h in coding_hints):
        return None
    for pattern, key in _PATTERNS:
        if pattern.search(q):
            return IDENTITY[key]
    return None
