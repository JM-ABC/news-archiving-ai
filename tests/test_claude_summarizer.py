import pytest
from unittest.mock import MagicMock
from summarizer.claude_summarizer import ClaudeSummarizer

SAMPLE_ARTICLES = [
    {"title": "GPT-5 출시", "url": "https://example.com/1", "summary": "OpenAI가 GPT-5를 발표했다.", "label": "TechCrunch AI", "region": "GL"},
    {"title": "Claude 4 업데이트", "url": "https://example.com/2", "summary": "Anthropic이 Claude를 업데이트했다.", "label": "Anthropic Blog", "region": "GL"},
]

def _make_mock_client(response_text: str):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=response_text)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client

def test_summarize_returns_list():
    summarizer = ClaudeSummarizer(api_key="test", model="claude-haiku-4-5-20251001")
    fake_response = '[{"title":"GPT-5 출시","category":"모델 출시","bullets":["불렛1","불렛2"],"implication":"시사점","url":"https://example.com/1"}]'
    summarizer._client = _make_mock_client(fake_response)
    result = summarizer.summarize(SAMPLE_ARTICLES[:1])
    assert isinstance(result, list)
    assert result[0]["title"] == "GPT-5 출시"
    assert result[0]["category"] == "모델 출시"
    assert isinstance(result[0]["bullets"], list)

def test_summarize_handles_json_with_code_block():
    summarizer = ClaudeSummarizer(api_key="test", model="claude-haiku-4-5-20251001")
    fake_response = '```json\n[{"title":"Test","category":"기타","bullets":["b1"],"implication":"imp","url":"https://x.com"}]\n```'
    summarizer._client = _make_mock_client(fake_response)
    result = summarizer.summarize(SAMPLE_ARTICLES[:1])
    assert isinstance(result, list)
    assert result[0]["title"] == "Test"

def test_summarize_returns_empty_for_no_articles():
    summarizer = ClaudeSummarizer(api_key="test", model="test")
    result = summarizer.summarize([])
    assert result == []

def test_generate_trends_returns_string():
    summarizer = ClaudeSummarizer(api_key="test", model="claude-haiku-4-5-20251001")
    summarizer._client = _make_mock_client("• AI 모델 경쟁 심화\n• 멀티모달 발전\n• 규제 강화")
    result = summarizer.generate_trends(SAMPLE_ARTICLES)
    assert isinstance(result, str)
    assert len(result) > 0

def test_generate_trends_returns_empty_for_no_articles():
    summarizer = ClaudeSummarizer(api_key="test", model="test")
    result = summarizer.generate_trends([])
    assert result == ""

def test_generate_tip_returns_string(monkeypatch):
    """generate_tip이 문자열을 반환하는지 확인."""
    from unittest.mock import MagicMock
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Claude 오토 모드, 링크드인 프로필 요약에 써보세요.")]
    monkeypatch.setattr(summarizer._client.messages, "create", lambda **kw: mock_msg)
    articles = [{"title": "Claude 오토 모드 출시", "bullets": ["자동화 향상"], "implication": "생산성 향상", "category": "모델 출시"}]
    result = summarizer.generate_tip(articles)
    assert isinstance(result, str)
    assert len(result) > 0

def test_generate_tip_empty_articles():
    """기사가 없으면 빈 문자열 반환."""
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    assert summarizer.generate_tip([]) == ""
