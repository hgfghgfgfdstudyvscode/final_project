# parsers/applegod.py

from bs4 import BeautifulSoup
from matching.parser import parse_text
from core.http import create_session


class AppleGodParser:
    base_url = "https://applegod.ru/search/"

    def __init__(self, session=None):
        self.session = session or create_session()

    def search(self, query: str, limit: int = 20):
        results = []
        page = 1
        seen = set()

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        while len(results) < limit and page <= 2:
            params = {
                "q": query,
                "PAGEN_4": page,
            }

            response = self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "lxml")
            cards = soup.select("div.products__card.card-product")
            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break

                title_a = card.select_one(".card-product__title a[href]")
                price_meta = card.select_one('meta[itemprop="price"]')

                if not title_a or not price_meta:
                    continue

                title = title_a.get_text(strip=True)
                url = "https://applegod.ru" + title_a["href"]

                if url in seen:
                    continue
                seen.add(url)

                price = int(float(price_meta["content"]))
                attrs = parse_text(title)

                results.append({
                    "shop": "AppleGod",
                    "title": title,
                    "price": price,
                    "url": url,
                    "_attrs": attrs,
                })

            page += 1

        return results