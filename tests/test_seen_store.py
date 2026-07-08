import json

from collector.seen_store import load_seen, record_seen


def test_load_seen_missing_file(tmp_path):
    assert load_seen(tmp_path / "seen_urls.json") == set()


def test_record_and_load_roundtrip(tmp_path):
    path = tmp_path / "seen_urls.json"
    record_seen(path, ["https://a.com/1", "https://b.com/2"], "2026-07-06")
    assert load_seen(path) == {"https://a.com/1", "https://b.com/2"}


def test_record_appends_to_existing(tmp_path):
    path = tmp_path / "seen_urls.json"
    record_seen(path, ["https://a.com/1"], "2026-07-04")
    record_seen(path, ["https://b.com/2"], "2026-07-06")
    assert load_seen(path) == {"https://a.com/1", "https://b.com/2"}


def test_record_prunes_old_entries(tmp_path):
    path = tmp_path / "seen_urls.json"
    record_seen(path, ["https://old.com/1"], "2026-05-01")
    record_seen(path, ["https://new.com/2"], "2026-07-06", retention_days=30)
    seen = load_seen(path)
    assert "https://old.com/1" not in seen  # 66일 전 → 정리됨
    assert "https://new.com/2" in seen


def test_load_seen_corrupt_file(tmp_path):
    path = tmp_path / "seen_urls.json"
    path.write_text("not json{{{", encoding="utf-8")
    assert load_seen(path) == set()


def test_record_recovers_from_corrupt_file(tmp_path):
    path = tmp_path / "seen_urls.json"
    path.write_text("not json{{{", encoding="utf-8")
    record_seen(path, ["https://a.com/1"], "2026-07-06")
    assert load_seen(path) == {"https://a.com/1"}


def test_record_invalid_date_entries_pruned(tmp_path):
    path = tmp_path / "seen_urls.json"
    path.write_text(json.dumps({"https://x.com/1": "invalid-date"}), encoding="utf-8")
    record_seen(path, ["https://a.com/1"], "2026-07-06")
    seen = load_seen(path)
    assert "https://x.com/1" not in seen
    assert "https://a.com/1" in seen
