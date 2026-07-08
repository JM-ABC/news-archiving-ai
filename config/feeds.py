RSS_FEEDS = [
    # 글로벌 — 일반 독자 친화적 (기술 설명보다 "내 삶과 어떤 관련인지" 중심)
    {"label": "The Verge AI", "region": "GL", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "max": 6},
    {"label": "Wired AI", "region": "GL", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "max": 5},
    {"label": "The Guardian Tech", "region": "GL", "url": "https://www.theguardian.com/technology/rss", "max": 5},
    {"label": "BBC Technology", "region": "GL", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml", "max": 4},
    {"label": "TechCrunch AI", "region": "GL", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "max": 4},
    # 국내 — 일반 독자가 접하기 쉬운 매체
    {"label": "연합뉴스 IT", "region": "KR", "url": "https://www.yna.co.kr/RSS/it.xml", "max": 8},
    {"label": "매일경제 IT", "region": "KR", "url": "https://www.mk.co.kr/rss/50400012/", "max": 6},
    {"label": "AI타임스", "region": "KR", "url": "https://www.aitimes.com/rss/allArticle.xml", "max": 5},
]

# gstack으로 크롤링할 대상 (RSS 없거나 불안정)
CRAWL_TARGETS = [
    {"label": "OpenAI Blog", "region": "GL", "url": "https://openai.com/news", "max": 3},
    {"label": "Anthropic Blog", "region": "GL", "url": "https://www.anthropic.com/news", "max": 3},
    {"label": "Google DeepMind", "region": "GL", "url": "https://deepmind.google/discover/blog/", "max": 2},
]
