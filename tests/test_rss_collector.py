import time
from unittest.mock import patch, MagicMock
from collector.rss_collector import RSSCollector


def _entry(title, link, summary=""):
    """AI 키워드 필터·날짜 필터를 통과하는 mock RSS 엔트리 생성."""
    return MagicMock(
        title=title,
        link=link,
        summary=summary,
        published_parsed=time.gmtime(),  # 현재 시각 → 날짜 필터 통과
    )


def test_fetch_returns_list():
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 3}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            _entry("AI Test Article", "https://example.com/article", "Summary text")
        ])
        articles = collector.fetch()
    assert isinstance(articles, list)
    assert len(articles) == 1
    assert articles[0]["title"] == "AI Test Article"
    assert articles[0]["region"] == "GL"


def test_fetch_deduplicates_by_url():
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 5}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            _entry("AI 뉴스 A", "https://x.com/1"),
            _entry("AI 뉴스 A", "https://x.com/1"),
        ])
        articles = collector.fetch()
    assert len(articles) == 1


def test_fetch_respects_max_per_feed():
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 2}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            _entry(f"AI Article {i}", f"https://x.com/{i}") for i in range(5)
        ])
        articles = collector.fetch()
    assert len(articles) == 2


def test_fetch_returns_required_fields():
    collector = RSSCollector([
        {"label": "TechCrunch", "region": "GL", "url": "https://example.com/feed", "max": 5}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            _entry("AI News", "https://example.com/1", "Summary")
        ])
        articles = collector.fetch()
    article = articles[0]
    assert "title" in article
    assert "url" in article
    assert "summary" in article
    assert "label" in article
    assert "region" in article
    assert article["label"] == "TechCrunch"


def test_fetch_filters_non_ai_articles():
    """AI 무관 기사는 수집되지 않아야 함."""
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 5}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            _entry("주말 날씨 맑음", "https://x.com/weather", "전국이 맑겠습니다"),
            _entry("ChatGPT 신기능 공개", "https://x.com/ai", "OpenAI가 발표"),
        ])
        articles = collector.fetch()
    assert len(articles) == 1
    assert articles[0]["url"] == "https://x.com/ai"


def test_fetch_filters_old_articles():
    """cutoff(기본 4일)보다 오래된 기사는 제외되어야 함."""
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 5}
    ])
    old = MagicMock(
        title="오래된 AI 뉴스",
        link="https://x.com/old",
        summary="",
        published_parsed=time.gmtime(time.time() - 10 * 86400),  # 10일 전
    )
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[old])
        articles = collector.fetch()
    assert len(articles) == 0
