import feedparser
from typing import List, Dict

# AI 관련 키워드 — 제목·요약 중 하나라도 포함되면 수집
_AI_KEYWORDS = [
    # 영문
    "AI", "LLM", "GPT", "ChatGPT", "Claude", "Gemini", "Grok",
    "OpenAI", "Anthropic", "DeepMind", "Mistral", "Llama",
    "machine learning", "deep learning", "neural", "generative",
    "chatbot", "autonomous", "robotics",
    # 한글
    "인공지능", "머신러닝", "딥러닝", "생성형", "생성AI", "챗GPT",
    "챗봇", "자율주행", "딥페이크", "거대언어모델", "자동화",
    "알고리즘", "로봇", "음성인식", "이미지 생성", "추론 모델",
]

def _is_ai_related(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in _AI_KEYWORDS)


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

                if not _is_ai_related(title, summary):
                    continue

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
