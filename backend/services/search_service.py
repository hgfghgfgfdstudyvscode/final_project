from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from cachetools import TTLCache

from matching.matcher import pick_best
from matching.parser import parse_text
from core.parsers import PARSERS


_PRICE_INT_RE = re.compile(r"\d+")

_CACHE: TTLCache[str, Any] = TTLCache(maxsize=512, ttl=300)
_CACHE_LOCK = threading.Lock()


def _price_int(value) -> int:
    if value is None:
        return 10**18
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = "".join(_PRICE_INT_RE.findall(value))
        if not digits:
            return 10**18
        return int(digits)
    return 10**18


def _color_tokens(color) -> list[str]:
    if not color:
        return []
    return str(color).replace("_", " ").strip().split()


class SearchService:
    def search(self, raw_query: str):
        raw_query = (raw_query or "").strip()
        if len(raw_query) < 2:
            return [{"type": "hint", "message": "Уточните, пожалуйста, ваш запрос"}]

        query_attrs = parse_text(raw_query)
        if self._is_ambiguous_query(query_attrs):
            return [{"type": "hint", "message": "Уточните, пожалуйста, ваш запрос"}]

        search_query = self._build_search_query(query_attrs, raw_query)

        cache_key = f"v1::{search_query.lower().strip()}"
        with _CACHE_LOCK:
            cached = _CACHE.get(cache_key)
        if cached is not None:
            return cached

        results = []

        with ThreadPoolExecutor(max_workers=len(PARSERS)) as ex:
            futures = [ex.submit(parser.search, search_query, 30) for parser in PARSERS]
            for fut in as_completed(futures):
                try:
                    items = fut.result() or []
                except Exception as e:
                    print(f"Parser error: {e}", flush=True)
                    continue

                best = pick_best(items, query_attrs)
                if best:
                    best.pop("_attrs", None)
                    results.append(best)

        if not results:
            none_payload = [{"type": "none", "message": "Ничего не найдено"}]
            with _CACHE_LOCK:
                _CACHE[cache_key] = none_payload
            return none_payload

        results.sort(key=lambda x: _price_int(x.get("price")))

        with _CACHE_LOCK:
            _CACHE[cache_key] = results

        return results

    def _build_search_query(self, attrs: dict, raw: str) -> str:
        cat = attrs.get("category")
        model = attrs.get("model")
        line = attrs.get("line")
        storage = attrs.get("storage")
        size = attrs.get("size")
        chip = attrs.get("chip")
        color = attrs.get("color")
        ram = attrs.get("ram")

        parts: list[str] = []

        if cat == "iphone":
            parts = ["iphone"]
            if model:
                parts.append(str(model))
            if line:
                parts.extend(str(line).split())
            if storage:
                parts.append(self._storage_token(storage))
            parts.extend(_color_tokens(color))

        elif cat == "macbook":
            parts = ["macbook"]
            if line:
                parts.append(str(line))
            if size:
                parts.append(str(size))
            if chip:
                parts.append(str(chip).upper())
            if ram:
                parts.append(f"{ram}gb")
            if storage:
                parts.append(self._storage_token(storage))
            parts.extend(_color_tokens(color))

        elif cat == "ipad":
            parts = ["ipad"]
            if line and line != "ipad":
                parts.append(str(line))
            if size:
                parts.append(str(size))
            if chip:
                parts.append(str(chip).upper())
            if ram:
                parts.append(f"{ram}gb")
            if storage:
                parts.append(self._storage_token(storage))
            parts.extend(_color_tokens(color))

        elif cat == "airpods":
            parts = ["airpods"]
            if line and line != "airpods":
                parts.append(str(line))
            if model:
                parts.append(str(model))
            parts.extend(_color_tokens(color))

        else:
            return raw

        parts = [p for p in parts if p]
        return " ".join(parts) if parts else raw

    def _storage_token(self, storage: str) -> str:
        s = str(storage).lower().strip()
        if s.endswith("gb"):
            return s[:-2]
        return s

    def _is_ambiguous_query(self, attrs: dict) -> bool:
        cat = attrs.get("category")

        if cat == "iphone":
            return not (attrs.get("model") and attrs.get("storage"))

        if cat == "macbook":
            return not (attrs.get("line") and attrs.get("size") and attrs.get("chip") and attrs.get("storage"))

        if cat == "ipad":
            return not (attrs.get("line") and attrs.get("size") and attrs.get("storage"))

        if cat == "airpods":
            return False

        return True