from bs4 import BeautifulSoup

from matching.parser import parse_text
from core.http import create_session

class AppleMarketParser:
    base_url = "https://apple-market.ru/index.php"

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
                "route": "product/search",
                "search": query,
                "page": page,
            }

            response = self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=15,
                verify=False,
            )

            if response.status_code != 200:
                print(f"AppleMarket HTTP {response.status_code}", flush=True)
                break

            soup = BeautifulSoup(response.text, "lxml")
            cards = soup.select("li.search-page__results-item article.product")
            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break

                title_a = card.select_one("h3.product__name a[href]")
                if not title_a:
                    continue

                title = title_a.get_text(strip=True)
                url = title_a["href"]

                if url in seen:
                    continue
                seen.add(url)

                price_span = card.select_one("div.product__prices span.product__price")
                if not price_span:
                    continue

                price = int("".join(ch for ch in price_span.get_text() if ch.isdigit()))
                attrs = parse_text(title)

                results.append({
                    "shop": "AppleMarket",
                    "title": title,
                    "price": price,
                    "url": url,
                    "_attrs": attrs,
                })

            page += 1

        return results