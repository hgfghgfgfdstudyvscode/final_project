from bs4 import BeautifulSoup

from matching.parser import parse_text
from core.http import create_session


class MacApplesParser:
    base_url = "https://macapples.ru/search"

    def __init__(self, session=None):
        self.session = session or create_session()

    def search(self, query: str, limit: int = 20):
        results = []
        page = 1
        seen = set()

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }

        while len(results) < limit and page <= 2:
            params = {"query": query,
                      "page": page}

            response = self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=15
            )

            if response.status_code != 200:
                print(f"MacApples HTTP {response.status_code}", flush=True)
                break

            soup = BeautifulSoup(response.text, "lxml")
            cards = soup.select("div.single-product.grid-v.single-product-v2")
            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break

                title_a = card.select_one('.pro-title a[itemprop="name"][href]')
                if not title_a:
                    continue

                title = title_a.get_text(strip=True)
                url = "https://macapples.ru/" + title_a["href"].lstrip("/")

                if url in seen:
                    continue
                seen.add(url)

                price = int(float(card.select_one('meta[itemprop="price"]')["content"]))

                attrs = parse_text(title)

                results.append({
                    "shop": "MacApples",
                    "title": title,
                    "price": price,
                    "url": url,
                    "_attrs": attrs,
                })

            page += 1

        return results