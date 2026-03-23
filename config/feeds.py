RSS_FEEDS = [
    # 글로벌
    {"label": "TechCrunch AI", "region": "GL", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "max": 8},
    {"label": "MIT Tech Review", "region": "GL", "url": "https://www.technologyreview.com/feed/", "max": 5},
    {"label": "The Verge AI", "region": "GL", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "max": 5},
    {"label": "VentureBeat AI", "region": "GL", "url": "https://venturebeat.com/category/ai/feed/", "max": 5},
    {"label": "Wired AI", "region": "GL", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "max": 5},
    # 국내
    {"label": "전자신문 AI", "region": "KR", "url": "https://www.etnews.com/rss/section.xml?id=13", "max": 8},
    {"label": "ZDNet Korea", "region": "KR", "url": "https://www.zdnet.co.kr/rss/news.xml", "max": 6},
    {"label": "AI타임스", "region": "KR", "url": "https://www.aitimes.com/rss/allArticle.xml", "max": 6},
]

# gstack으로 크롤링할 대상 (RSS 없거나 불안정)
CRAWL_TARGETS = [
    {"label": "OpenAI Blog", "region": "GL", "url": "https://openai.com/news", "selector": "article a", "max": 3},
    {"label": "Anthropic Blog", "region": "GL", "url": "https://www.anthropic.com/news", "selector": "article a", "max": 3},
    {"label": "Google DeepMind", "region": "GL", "url": "https://deepmind.google/discover/blog/", "selector": "article a", "max": 2},
]
