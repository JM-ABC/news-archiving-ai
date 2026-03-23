import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from publisher.sns_exporter import SNSExporter
from publisher.email_publisher import EmailPublisher
from publisher.notion_publisher import NotionPublisher


# --- SNSExporter tests ---

def test_sns_exporter_creates_files(tmp_path):
    exporter = SNSExporter(output_dir=tmp_path)
    exporter.export("2026-03-24", "linkedin post", "threads post", "instagram post")
    day_dir = tmp_path / "2026-03-24"
    assert day_dir.exists()
    assert (day_dir / "linkedin.md").exists()
    assert (day_dir / "threads.md").exists()
    assert (day_dir / "instagram.md").exists()

def test_sns_exporter_file_contains_content(tmp_path):
    exporter = SNSExporter(output_dir=tmp_path)
    exporter.export("2026-03-24", "my linkedin post", "my threads post", "my instagram post")
    content = (tmp_path / "2026-03-24" / "linkedin.md").read_text(encoding="utf-8")
    assert "my linkedin post" in content

def test_sns_exporter_creates_date_subdirectory(tmp_path):
    exporter = SNSExporter(output_dir=tmp_path)
    exporter.export("2026-03-24", "a", "b", "c")
    assert (tmp_path / "2026-03-24").is_dir()


# --- EmailPublisher tests ---

def test_email_publisher_skips_when_no_api_key():
    pub = EmailPublisher(api_key="", from_addr="a@b.com", to_addrs=["c@d.com"])
    result = pub.send("Subject", "<html>body</html>")
    assert result is False

def test_email_publisher_returns_false_gracefully():
    pub = EmailPublisher(api_key="", from_addr="", to_addrs=[])
    result = pub.send("Test", "body")
    assert result is False


# --- NotionPublisher tests ---

def test_notion_publisher_skips_when_no_api_key():
    pub = NotionPublisher(api_key="", database_id="some-id")
    result = pub.upload("2026-03-24", "trends", [])
    assert result is False

def test_notion_publisher_skips_when_no_database_id():
    pub = NotionPublisher(api_key="some-key", database_id="")
    result = pub.upload("2026-03-24", "trends", [])
    assert result is False
