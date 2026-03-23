import sys
import pytest
from unittest.mock import patch, MagicMock


def test_main_imports():
    """main.py can be imported without error."""
    import importlib
    import main
    importlib.reload(main)


def test_main_exits_early_when_insufficient_articles(tmp_path, monkeypatch, capsys):
    """When fewer than MIN_NEW_ARTICLES articles, pipeline exits without publishing."""
    monkeypatch.setenv("CLAUDE_API_KEY", "test-key")

    with patch("collector.rss_collector.RSSCollector.fetch", return_value=[]), \
         patch("collector.gstack_crawler.GstackCrawler.crawl", return_value=[]), \
         patch("publisher.email_publisher.EmailPublisher.send") as mock_send, \
         patch("publisher.notion_publisher.NotionPublisher.upload") as mock_upload:

        import importlib
        import main
        monkeypatch.setattr(main, "TRENDS_DIR", tmp_path / "trends")
        monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path / "output")
        (tmp_path / "trends").mkdir()
        (tmp_path / "output").mkdir()

        # Call main() — should exit early with 0 articles
        main.main()

        # No publishing should happen
        mock_send.assert_not_called()
        mock_upload.assert_not_called()

    captured = capsys.readouterr()
    assert "미달" in captured.out or "0" in captured.out


def test_prioritize_splits_kr_gl():
    """prioritize() returns up to KR_MAX KR + GL_MAX GL articles."""
    import importlib
    import main

    kr_articles = [{"region": "KR", "title": f"KR {i}", "url": f"https://kr/{i}", "summary": "", "label": "L"} for i in range(20)]
    gl_articles = [{"region": "GL", "title": f"GL {i}", "url": f"https://gl/{i}", "summary": "", "label": "L"} for i in range(10)]

    result = main.prioritize(kr_articles + gl_articles)
    kr_count = sum(1 for a in result if a["region"] == "KR")
    gl_count = sum(1 for a in result if a["region"] == "GL")

    assert kr_count == 13  # KR_MAX
    assert gl_count == 7   # GL_MAX
