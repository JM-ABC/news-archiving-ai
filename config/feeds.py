RSS_FEEDS = [
    # 글로벌 — 일반 독자 친화적 (기술 설명보다 "내 삶과 어떤 관련인지" 중심)
    {"label": "The Verge AI", "region": "GL", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "max": 6},
    {"label": "Wired AI", "region": "GL", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "max": 5},
    {"label": "The Guardian Tech", "region": "GL", "url": "https://www.theguardian.com/technology/rss", "max": 5},
    {"label": "BBC Technology", "region": "GL", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml", "max": 4},
    {"label": "TechCrunch AI", "region": "GL", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "max": 4},
    # 글로벌 — 대형 AI 플랫폼 공식/준공식 소식 (MAJOR_PLATFORM_LABELS로 prioritize()에서 우선 배정)
    {"label": "OpenAI News", "region": "GL", "url": "https://openai.com/news/rss.xml", "max": 4},
    {"label": "Google DeepMind", "region": "GL", "url": "https://deepmind.google/blog/rss.xml", "max": 3},
    {"label": "Google AI Blog", "region": "GL", "url": "https://blog.google/technology/ai/rss/", "max": 3},
    {"label": "Microsoft AI News", "region": "GL", "url": "https://news.microsoft.com/source/topics/ai/feed/", "max": 3},
    # Anthropic은 공식 RSS가 없음. 커뮤니티가 매일 스크래핑해 올리는 비공식 피드 —
    # 예고 없이 끊길 수 있으니 healthcheck --check-feeds로 주기적 생존 확인 필요.
    {"label": "Anthropic News (비공식)", "region": "GL", "url": "https://tim-hilde.github.io/anthropic-rss/rss.xml", "max": 3},
    # 국내 — 일반 독자가 접하기 쉬운 매체
    # 연합뉴스는 더 이상 별도 IT 카테고리를 운영하지 않음(it.xml 등은 404) — 실제 살아있는
    # 카테고리 중 AI·반도체 기업 소식이 섞여 나오는 "산업" 카테고리로 대체.
    {"label": "연합뉴스 산업", "region": "KR", "url": "https://www.yna.co.kr/rss/industry.xml", "max": 8},
    {"label": "매일경제 IT", "region": "KR", "url": "https://www.mk.co.kr/rss/50400012/", "max": 6},
    {"label": "AI타임스", "region": "KR", "url": "https://www.aitimes.com/rss/allArticle.xml", "max": 5},
]

# 대형 AI 플랫폼 공식 소식 라벨 — prioritize()가 GL 쿼터 안에서 이 라벨들을 먼저 채운다.
# CRAWL_TARGETS 라벨도 포함해두면, gstack 크롤링이 되살아났을 때도 자동으로 우선순위를 받는다.
MAJOR_PLATFORM_LABELS = {
    "OpenAI News", "Google DeepMind", "Google AI Blog", "Microsoft AI News",
    "Anthropic News (비공식)", "OpenAI Blog", "Anthropic Blog",
}

# gstack으로 크롤링할 대상 (RSS 없거나 불안정)
# 주의: 현재 GitHub Actions 워크플로에 gstack 설치 스텝이 없어 CI에서는 항상 0개 수집됨
# (로컬에 gstack 바이너리가 없어도 동일). OpenAI·Google DeepMind는 위 RSS_FEEDS로 대체됐다.
CRAWL_TARGETS = [
    {"label": "OpenAI Blog", "region": "GL", "url": "https://openai.com/news", "max": 3},
    {"label": "Anthropic Blog", "region": "GL", "url": "https://www.anthropic.com/news", "max": 3},
    {"label": "Google DeepMind", "region": "GL", "url": "https://deepmind.google/discover/blog/", "max": 2},
]
