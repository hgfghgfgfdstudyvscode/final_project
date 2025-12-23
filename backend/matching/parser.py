from __future__ import annotations

import re
from typing import Any, Dict

from matching.dictionaries import COLORS, STORAGE


def _normalize_text(text: str) -> str:
    text = (text or "").lower()
    return text.replace("ё", "е")


def _extract_color(text: str) -> str | None:
    for key, values in COLORS.items():
        if any(v in text for v in values):
            return key
    return None


_IPHONE_RE = re.compile(r"\biphone\b", re.IGNORECASE)
_IPHONE_MODELS = [str(i) for i in range(17, 13, -1)]
_IPHONE_MODEL_RE = re.compile(r"\b(" + "|".join(_IPHONE_MODELS) + r")\b")
_IPHONE_LINE_PRO_MAX_RE = re.compile(r"\bpro\s*max\b", re.IGNORECASE)
_IPHONE_LINE_PRO_RE = re.compile(r"\bpro\b", re.IGNORECASE)
_IPHONE_LINE_PLUS_RE = re.compile(r"\bplus\b", re.IGNORECASE)
_IPHONE_LINE_MINI_RE = re.compile(r"\bmini\b", re.IGNORECASE)

_MACBOOK_RE = re.compile(r"\bmacbook\b", re.IGNORECASE)
_MACBOOK_SIZE_RE = re.compile(r"(?<!\d)(13|14|15|16)\"(?![\d\.,])", re.IGNORECASE)
_MACBOOK_CHIP_RE = re.compile(r"\bm[1-4]\b", re.IGNORECASE)
_MACBOOK_LINE_PRO_RE = re.compile(r"\bpro\b", re.IGNORECASE)
_MACBOOK_LINE_AIR_RE = re.compile(r"\bair\b", re.IGNORECASE)

_IPAD_RE = re.compile(r"\bipad\b", re.IGNORECASE)
_IPAD_LINE_PRO_RE = re.compile(r"\bipad\s*pro\b", re.IGNORECASE)
_IPAD_LINE_AIR_RE = re.compile(r"\bipad\s*air\b", re.IGNORECASE)
_IPAD_LINE_MINI_RE = re.compile(r"\bipad\s*mini\b", re.IGNORECASE)
_IPAD_SIZE_RE = re.compile(r"(?<!\d)(10\.9|11|13)\"(?![\d\.,])", re.IGNORECASE)
_IPAD_CHIP_RE = re.compile(r"\bm[1-4]\b", re.IGNORECASE)

_AIRPODS_RE = re.compile(r"\bair\s*pods\b", re.IGNORECASE)
_AIRPODS_MAX_RE = re.compile(r"\bair\s*pods\s*max\b", re.IGNORECASE)
_AIRPODS_PRO_RE = re.compile(r"\bair\s*pods\s*pro\b", re.IGNORECASE)

# AirPods Pro поколение: поддерживаем варианты вида
# - "Pro 2" / "Pro 3"
# - "2nd" / "2th" / "3rd" (иногда на сайтах встречаются ошибки)
# - "2-го поколения" / "2го поколения" / "2 поколение"
_AIRPODS_PRO_MODEL_RE = re.compile(r"\bpro\s*([23])\b", re.IGNORECASE)
_AIRPODS_ORDINAL_EN_RE = re.compile(r"\b([23])\s*(?:nd|rd|th)\b", re.IGNORECASE)
_AIRPODS_GEN_EN_RE = re.compile(r"\b([23])\s*gen(?:eration)?\b", re.IGNORECASE)
_AIRPODS_GEN_RU_RE = re.compile(
    r"\b([23])\s*(?:-?\s*го)?\s*поколен(?:ие|ия)\b", re.IGNORECASE
)
_AIRPODS_MODEL_RE = re.compile(
    r"\bair\s*pods\s*(?:gen\s*)?([2-4])\b|\b([2-4])\s*gen\b", re.IGNORECASE
)


def _detect_category(text: str) -> str | None:
    if _IPAD_RE.search(text):
        return "ipad"
    if _IPHONE_RE.search(text):
        return "iphone"
    if _MACBOOK_RE.search(text):
        return "macbook"
    if _AIRPODS_RE.search(text):
        return "airpods"
    return None


def parse_text(text: str) -> Dict[str, Any]:
    text = _normalize_text(text)

    result: Dict[str, Any] = {
        "category": None,
        "model": None,
        "line": None,
        "storage": None,
        "color": None,
        "size": None,
        "chip": None,
    }

    category = _detect_category(text)
    result["category"] = category

    if category == "iphone":
        m = _IPHONE_MODEL_RE.search(text)
        if m:
            result["model"] = m.group(1)

        if _IPHONE_LINE_PRO_MAX_RE.search(text):
            result["line"] = "pro max"
        elif _IPHONE_LINE_PRO_RE.search(text):
            result["line"] = "pro"
        elif _IPHONE_LINE_PLUS_RE.search(text):
            result["line"] = "plus"
        elif _IPHONE_LINE_MINI_RE.search(text):
            result["line"] = "mini"

    elif category == "macbook":
        if _MACBOOK_LINE_PRO_RE.search(text):
            result["line"] = "pro"
        elif _MACBOOK_LINE_AIR_RE.search(text):
            result["line"] = "air"

        cm = _MACBOOK_CHIP_RE.search(text)
        if cm:
            chip = cm.group(0).lower()
            result["chip"] = chip
            result["model"] = chip

        sm = _MACBOOK_SIZE_RE.search(text)
        if sm:
            result["size"] = sm.group(1)

    elif category == "ipad":
        if _IPAD_LINE_PRO_RE.search(text):
            result["line"] = "pro"
        elif _IPAD_LINE_AIR_RE.search(text):
            result["line"] = "air"
        elif _IPAD_LINE_MINI_RE.search(text):
            result["line"] = "mini"
        else:
            result["line"] = "ipad"

        sm = _IPAD_SIZE_RE.search(text)
        if sm:
            result["size"] = sm.group(1)

        cm = _IPAD_CHIP_RE.search(text)
        if cm:
            result["chip"] = cm.group(0).lower()

    elif category == "airpods":
        if _AIRPODS_MAX_RE.search(text):
            result["line"] = "max"
        elif _AIRPODS_PRO_RE.search(text):
            result["line"] = "pro"
        else:
            result["line"] = "airpods"

        if result["line"] == "pro":
            # Пытаемся вытащить поколение Pro более "толерантно" к написанию на сайтах
            for rx in (
                _AIRPODS_PRO_MODEL_RE,
                _AIRPODS_ORDINAL_EN_RE,
                _AIRPODS_GEN_EN_RE,
                _AIRPODS_GEN_RU_RE,
            ):
                pm = rx.search(text)
                if pm:
                    result["model"] = pm.group(1)
                    break
        elif result["line"] == "airpods":
            gm = _AIRPODS_MODEL_RE.search(text)
            if gm:
                result["model"] = gm.group(1) or gm.group(2)

    for key, values in STORAGE.items():
        if any(v in text for v in values):
            result["storage"] = key
            break

    result["color"] = _extract_color(text)

    return result