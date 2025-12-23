from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter


def create_session(*, pool_connections: int = 20, pool_maxsize: int = 20) -> requests.Session:
    session = requests.Session()

    adapter = HTTPAdapter(
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        max_retries=0,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
