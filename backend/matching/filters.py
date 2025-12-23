from __future__ import annotations

import re
from functools import lru_cache
from typing import List

from matching.stopwords import STOP_WORDS


def _normalize_text(text: str) -> str:
    text = (text or "").lower()
    return text.replace("ё", "е")


@lru_cache(maxsize=1)
def _compiled_patterns() -> List[re.Pattern]:
    patterns: List[re.Pattern] = []
    for w in STOP_WORDS:
        w_n = _normalize_text(w)
        patterns.append(re.compile(rf"\b{re.escape(w_n)}\b"))
    return patterns


def contains_stopwords(text: str, category: str | None = None) -> bool:
    _ = category
    text_n = _normalize_text(text)
    return any(p.search(text_n) for p in _compiled_patterns())