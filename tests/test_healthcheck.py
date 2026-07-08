from datetime import datetime, timezone

from scripts.healthcheck import latest_trend_date, staleness_days


def test_latest_trend_date_picks_most_recent(tmp_path):
    (tmp_path / "trend_2026-03-26.txt").write_text("a", encoding="utf-8")
    (tmp_path / "trend_2026-04-15.txt").write_text("b", encoding="utf-8")
    latest = latest_trend_date(tmp_path)
    assert latest == datetime(2026, 4, 15, tzinfo=timezone.utc)


def test_latest_trend_date_ignores_invalid_names(tmp_path):
    (tmp_path / "trend_invalid.txt").write_text("x", encoding="utf-8")
    (tmp_path / "trend_2026-03-26.txt").write_text("a", encoding="utf-8")
    latest = latest_trend_date(tmp_path)
    assert latest == datetime(2026, 3, 26, tzinfo=timezone.utc)


def test_latest_trend_date_empty_dir(tmp_path):
    assert latest_trend_date(tmp_path) is None


def test_staleness_days():
    latest = datetime(2026, 4, 15, tzinfo=timezone.utc)
    now = datetime(2026, 7, 6, tzinfo=timezone.utc)
    assert staleness_days(latest, now) == 82


def test_staleness_days_no_history():
    assert staleness_days(None) == -1


def test_staleness_days_same_day():
    now = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)
    latest = datetime(2026, 7, 6, tzinfo=timezone.utc)
    assert staleness_days(latest, now) == 0


# ── 피드 헬스체크 ──
import time
from unittest.mock import patch, MagicMock

from scripts.healthcheck import check_feed, check_crawl_target

FEED = {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 5}


def _resp(status=200, content=b"<rss/>"):
    return MagicMock(status_code=status, content=content)


def test_check_feed_ok():
    entry = MagicMock(published_parsed=time.gmtime())
    with patch("requests.get", return_value=_resp()), \
         patch("feedparser.parse", return_value=MagicMock(entries=[entry])):
        r = check_feed(FEED)
    assert r["status"] == "ok"


def test_check_feed_http_error():
    with patch("requests.get", return_value=_resp(status=404)):
        r = check_feed(FEED)
    assert r["status"] == "http_error"
    assert "404" in r["detail"]


def test_check_feed_connection_error():
    with patch("requests.get", side_effect=OSError("connection refused")):
        r = check_feed(FEED)
    assert r["status"] == "error"


def test_check_feed_empty():
    with patch("requests.get", return_value=_resp()), \
         patch("feedparser.parse", return_value=MagicMock(entries=[])):
        r = check_feed(FEED)
    assert r["status"] == "empty"


def test_check_feed_stale():
    old_entry = MagicMock(published_parsed=time.gmtime(time.time() - 30 * 86400))
    with patch("requests.get", return_value=_resp()), \
         patch("feedparser.parse", return_value=MagicMock(entries=[old_entry])):
        r = check_feed(FEED)
    assert r["status"] == "stale_feed"


def test_check_crawl_target_ok():
    with patch("requests.get", return_value=_resp()):
        r = check_crawl_target({"label": "T", "url": "https://example.com", "max": 3})
    assert r["status"] == "ok"


# ── 발행일 판정 (seen_urls.json 우선) ──
import json as _json

from scripts.healthcheck import latest_publish_date


def test_latest_publish_date_prefers_seen_urls(tmp_path):
    (tmp_path / "trend_2026-03-26.txt").write_text("a", encoding="utf-8")
    (tmp_path / "seen_urls.json").write_text(
        _json.dumps({"https://a.com/1": "2026-07-01", "https://b.com/2": "2026-07-06"}),
        encoding="utf-8",
    )
    assert latest_publish_date(tmp_path) == datetime(2026, 7, 6, tzinfo=timezone.utc)


def test_latest_publish_date_falls_back_to_trend_files(tmp_path):
    (tmp_path / "trend_2026-04-15.txt").write_text("a", encoding="utf-8")
    assert latest_publish_date(tmp_path) == datetime(2026, 4, 15, tzinfo=timezone.utc)


def test_latest_publish_date_corrupt_seen_falls_back(tmp_path):
    (tmp_path / "seen_urls.json").write_text("broken{{", encoding="utf-8")
    (tmp_path / "trend_2026-04-15.txt").write_text("a", encoding="utf-8")
    assert latest_publish_date(tmp_path) == datetime(2026, 4, 15, tzinfo=timezone.utc)
