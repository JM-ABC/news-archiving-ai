import pytest
from unittest.mock import patch, MagicMock
from collector.gstack_crawler import GstackCrawler

def test_crawl_returns_empty_when_binary_missing():
    crawler = GstackCrawler(binary_path=None, targets=[
        {"label": "Test", "region": "GL", "url": "https://example.com", "selector": "a", "max": 2}
    ])
    result = crawler.crawl()
    assert isinstance(result, list)
    assert result == []

def test_crawl_returns_empty_when_binary_path_not_exist(tmp_path):
    crawler = GstackCrawler(binary_path=tmp_path / "nonexistent", targets=[
        {"label": "Test", "region": "GL", "url": "https://example.com", "selector": "a", "max": 2}
    ])
    result = crawler.crawl()
    assert result == []

def test_crawl_parses_links_output():
    from pathlib import Path
    crawler = GstackCrawler(binary_path=Path("/fake/browse"), targets=[
        {"label": "OpenAI Blog", "region": "GL", "url": "https://openai.com/news", "selector": "a", "max": 2}
    ])
    # gstack "links" command outputs "text → url" lines
    mock_output = "AI Article 1 → https://openai.com/article1\nAI Article 2 → https://openai.com/article2\nAI Article 3 → https://openai.com/article3\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
        articles = crawler.crawl()
    assert len(articles) == 2  # max=2
    assert articles[0]["title"] == "AI Article 1"
    assert articles[0]["url"] == "https://openai.com/article1"
    assert articles[0]["region"] == "GL"
    assert articles[0]["label"] == "OpenAI Blog"

def test_crawl_skips_failed_targets():
    from pathlib import Path
    crawler = GstackCrawler(binary_path=Path("/fake/browse"), targets=[
        {"label": "Target1", "region": "GL", "url": "https://example.com/1", "selector": "a", "max": 3},
        {"label": "Target2", "region": "GL", "url": "https://example.com/2", "selector": "a", "max": 3},
    ])
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout=""),  # first fails
            MagicMock(returncode=0, stdout="Article → https://example.com/art\n"),  # second succeeds
        ]
        articles = crawler.crawl()
    assert len(articles) == 1
    assert articles[0]["url"] == "https://example.com/art"
