import feedparser
from typing import List, Dict


class RSSCollector:
    def __init__(self, feeds: List[Dict]):
        self.feeds = feeds

    def fetch(self, days: int = 4) -> List[Dict]:
        articles = []
        seen_urls = set()

        for feed in self.feeds:
            parsed = feedparser.parse(feed["url"])
            count = 0
            limit = feed.get("max", 10)

            for entry in parsed.entries:
                if count >= limit:
                    break
                url = getattr(entry, "link", "")
                if not url or url in seen_urls:
                    continue

                title = getattr(entry, "title", "").strip()
                summary = getattr(entry, "summary", "").strip()

                seen_urls.add(url)
                articles.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "label": feed["label"],
                    "region": feed["region"],
                })
                count += 1

        return articles
