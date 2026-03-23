import pytest
from unittest.mock import patch, MagicMock
from collector.rss_collector import RSSCollector

def test_fetch_returns_list():
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 3}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            MagicMock(
                title="Test Article",
                link="https://example.com/article",
                summary="Summary text",
                published="Mon, 23 Mar 2026 10:00:00 +0900",
            )
        ])
        articles = collector.fetch()
    assert isinstance(articles, list)
    assert len(articles) == 1
    assert articles[0]["title"] == "Test Article"
    assert articles[0]["region"] == "GL"

def test_fetch_deduplicates_by_url():
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 5}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            MagicMock(title="A", link="https://x.com/1", summary="", published="Mon, 23 Mar 2026 10:00:00 +0900"),
            MagicMock(title="A", link="https://x.com/1", summary="", published="Mon, 23 Mar 2026 10:00:00 +0900"),
        ])
        articles = collector.fetch()
    assert len(articles) == 1

def test_fetch_respects_max_per_feed():
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 2}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            MagicMock(title=f"Article {i}", link=f"https://x.com/{i}", summary="", published="Mon, 23 Mar 2026 10:00:00 +0900")
            for i in range(5)
        ])
        articles = collector.fetch()
    assert len(articles) == 2

def test_fetch_returns_required_fields():
    collector = RSSCollector([
        {"label": "TechCrunch", "region": "GL", "url": "https://example.com/feed", "max": 5}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            MagicMock(title="AI News", link="https://example.com/1", summary="Summary", published="Mon, 23 Mar 2026 10:00:00 +0900")
        ])
        articles = collector.fetch()
    article = articles[0]
    assert "title" in article
    assert "url" in article
    assert "summary" in article
    assert "label" in article
    assert "region" in article
    assert article["label"] == "TechCrunch"
