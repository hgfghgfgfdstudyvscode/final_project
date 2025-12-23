from bs4 import BeautifulSoup

from matching.parser import parse_text
from core.http import create_session


class TechmartParser:
    base_url = "https://techmart.ru/index.php?route=product/search"

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
            params = {
                "search": query,
                "page": page,
            }

            response = self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=15
            )

            if response.status_code != 200:
                print(f"Techmart HTTP {response.status_code}", flush=True)
                break

            soup = BeautifulSoup(response.text, "lxml")
            cards = soup.select("#productlist div.product__item")
            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break

                title_a = card.select_one("a.product__title[href]")
                if not title_a:
                    continue

                title = title_a.get_text(strip=True)
                url = title_a["href"]

                if url in seen:
                    continue
                seen.add(url)

                price_span = card.select_one("p.product__price")
                if not price_span:
                    continue
                price = int("".join(ch for ch in price_span.get_text() if ch.isdigit()))

                attrs = parse_text(title)

                results.append({
                    "shop": "Techmart",
                    "title": title,
                    "price": price,
                    "url": url,
                    "_attrs": attrs,
                })

            page += 1

        return results