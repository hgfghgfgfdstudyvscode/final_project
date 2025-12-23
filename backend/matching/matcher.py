from __future__ import annotations

import re
from typing import Any, Mapping

from matching.filters import contains_stopwords
from matching.parser import parse_text


def _get_title(item: Mapping[str, Any]) -> str:
    return str(item.get("title") or item.get("name") or item.get("product_name") or "")


def _s(v: Any) -> str | None:
    if v is None:
        return None
    return str(v).strip().lower()


def _norm_line(category: str | None, line: Any) -> str | None:
    if category == "iphone":
        return _s(line) or "base"
    return _s(line)


def _eq(a: Any, b: Any) -> bool:
    return _s(a) == _s(b)


_PRICE_INT_RE = re.compile(r"\d+")


def _price_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = "".join(_PRICE_INT_RE.findall(value))
        if not digits:
            return None
        return int(digits)
    return None


def _required_match(query: Mapping[str, Any], attrs: Mapping[str, Any]) -> bool:
    qc = _s(query.get("category"))
    ac = _s(attrs.get("category"))
    if qc is not None and qc != ac:
        return False

    cat = qc or ac
    if cat is None:
        return False

    if cat == "iphone":
        if query.get("model") is not None and not _eq(query.get("model"), attrs.get("model")):
            return False
        if query.get("storage") is not None and not _eq(query.get("storage"), attrs.get("storage")):
            return False
        ql = _norm_line(cat, query.get("line"))
        il = _norm_line(cat, attrs.get("line"))
        if ql is not None and not _eq(ql, il):
            return False
        if query.get("color") is not None and not _eq(query.get("color"), attrs.get("color")):
            return False
        return True

    if cat == "macbook":
        if query.get("line") is not None and not _eq(query.get("line"), attrs.get("line")):
            return False
        if query.get("size") is not None and not _eq(query.get("size"), attrs.get("size")):
            return False
        if query.get("chip") is not None and not _eq(query.get("chip"), attrs.get("chip")):
            return False
        if query.get("storage") is not None and not _eq(query.get("storage"), attrs.get("storage")):
            return False
        if query.get("color") is not None and not _eq(query.get("color"), attrs.get("color")):
            return False
        return True

    if cat == "ipad":
        if query.get("line") is not None and not _eq(query.get("line"), attrs.get("line")):
            return False
        if query.get("size") is not None and not _eq(query.get("size"), attrs.get("size")):
            return False
        if query.get("storage") is not None and not _eq(query.get("storage"), attrs.get("storage")):
            return False
        if query.get("chip") is not None and not _eq(query.get("chip"), attrs.get("chip")):
            return False
        if query.get("color") is not None and not _eq(query.get("color"), attrs.get("color")):
            return False
        return True

    if cat == "airpods":
        ql = _norm_line(cat, query.get("line"))
        il = _norm_line(cat, attrs.get("line"))
        if ql is not None and not _eq(ql, il):
            return False
        if query.get("model") is not None and not _eq(query.get("model"), attrs.get("model")):
            return False
        if query.get("color") is not None and not _eq(query.get("color"), attrs.get("color")):
            return False
        return True

    return False


def _score(query: Mapping[str, Any], attrs: Mapping[str, Any]) -> int:
    cat = _s(query.get("category")) or _s(attrs.get("category"))
    if not cat:
        return 0

    s = 0

    if cat == "iphone":
        if query.get("model") is not None and _eq(query.get("model"), attrs.get("model")):
            s += 5
        if query.get("storage") is not None and _eq(query.get("storage"), attrs.get("storage")):
            s += 5
        ql = _norm_line(cat, query.get("line"))
        il = _norm_line(cat, attrs.get("line"))
        if ql is not None and _eq(ql, il):
            s += 3
        if query.get("color") is not None and _eq(query.get("color"), attrs.get("color")):
            s += 1
        return s

    if cat == "macbook":
        if query.get("chip") is not None and _eq(query.get("chip"), attrs.get("chip")):
            s += 5
        if query.get("line") is not None and _eq(query.get("line"), attrs.get("line")):
            s += 4
        if query.get("storage") is not None and _eq(query.get("storage"), attrs.get("storage")):
            s += 4
        if query.get("size") is not None and _eq(query.get("size"), attrs.get("size")):
            s += 3
        if query.get("color") is not None and _eq(query.get("color"), attrs.get("color")):
            s += 1
        return s

    if cat == "ipad":
        if query.get("line") is not None and _eq(query.get("line"), attrs.get("line")):
            s += 4
        if query.get("storage") is not None and _eq(query.get("storage"), attrs.get("storage")):
            s += 4
        if query.get("size") is not None and _eq(query.get("size"), attrs.get("size")):
            s += 3
        if query.get("chip") is not None and _eq(query.get("chip"), attrs.get("chip")):
            s += 2
        if query.get("color") is not None and _eq(query.get("color"), attrs.get("color")):
            s += 1
        return s

    if cat == "airpods":
        ql = _norm_line(cat, query.get("line"))
        il = _norm_line(cat, attrs.get("line"))
        if ql is not None and _eq(ql, il):
            s += 5
        if query.get("model") is not None and _eq(query.get("model"), attrs.get("model")):
            s += 3
        if query.get("model") is None and attrs.get("model") is None:
            s += 1
        if query.get("color") is not None and _eq(query.get("color"), attrs.get("color")):
            s += 1
        return s

    return 0


def _specificity(attrs: Mapping[str, Any]) -> int:
    return sum(1 for k in ("model", "line", "storage", "size", "chip", "color") if attrs.get(k) is not None)


def pick_best(items: list[dict], query_attrs: dict) -> dict | None:
    q_category = _s(query_attrs.get("category"))

    best_item: dict | None = None
    best_score = -1
    best_price: int | None = None
    best_spec = -1

    for item in items:
        title = _get_title(item)
        if title and contains_stopwords(title, category=q_category):
            continue

        attrs = item.get("_attrs")
        if not isinstance(attrs, dict):
            attrs = parse_text(title)
            item["_attrs"] = attrs

        if not _required_match(query_attrs, attrs):
            continue

        price = _price_int(item.get("price"))
        if price is None:
            continue

        score = _score(query_attrs, attrs)
        spec = _specificity(attrs)

        if score > best_score:
            best_item = item
            best_score = score
            best_price = price
            best_spec = spec
            continue

        if score == best_score:
            if best_price is None or price < best_price:
                best_item = item
                best_price = price
                best_spec = spec
                continue
            if best_price is not None and price == best_price and spec > best_spec:
                best_item = item
                best_spec = spec

    return best_item