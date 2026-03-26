import json
import pytest
from unittest.mock import MagicMock
from summarizer.claude_summarizer import ClaudeSummarizer

SAMPLE_ARTICLES = [
    {"title": "GPT-5 출시", "url": "https://example.com/1", "summary": "OpenAI가 GPT-5를 발표했다.", "label": "TechCrunch AI", "region": "GL", "category": "모델 출시"},
    {"title": "Claude 4 업데이트", "url": "https://example.com/2", "summary": "Anthropic이 Claude를 업데이트했다.", "label": "Anthropic Blog", "region": "GL", "category": "모델 출시"},
]

def _make_mock_client(response_text: str):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=response_text)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client

def test_summarize_returns_list():
    summarizer = ClaudeSummarizer(api_key="test", model="claude-haiku-4-5-20251001")
    fake_response = '[{"title":"GPT-5 출시","category":"모델 출시","bullets":["성능이 향상됐어요","멀티모달을 지원해요"],"implication":"AI 경쟁이 심화됐어요","url":"https://example.com/1"}]'
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

# --- generate_tip: dict 반환 ---

def test_generate_tip_returns_dict():
    """generate_tip이 task/tools/prompt 키를 가진 dict를 반환하는지 확인."""
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    fake_json = '{"task": "회의록을 AI로 정리할 수 있어요.", "tools": ["Claude", "ChatGPT"], "prompt": "아래 회의록을 액션 아이템으로 정리해줘."}'
    summarizer._client = _make_mock_client(fake_json)
    articles = [{"title": "Claude 오토 모드 출시", "bullets": ["자동화 향상됐어요"], "implication": "생산성이 높아졌어요", "category": "모델 출시"}]
    result = summarizer.generate_tip(articles)
    assert isinstance(result, dict)
    assert "task" in result
    assert "tools" in result
    assert "prompt" in result
    assert isinstance(result["tools"], list)

def test_generate_tip_returns_empty_dict_for_no_articles():
    """기사가 없으면 빈 dict 반환."""
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    assert summarizer.generate_tip([]) == {}

def test_generate_tip_returns_empty_dict_for_all_other_category():
    """모든 기사가 '기타' 카테고리면 빈 dict 반환."""
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    articles = [{"title": "기타 기사", "bullets": [], "category": "기타"}]
    assert summarizer.generate_tip(articles) == {}

def test_generate_tip_handles_json_with_code_block():
    """코드블록으로 감싼 JSON도 파싱 성공."""
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    fake_json = '```json\n{"task": "업무를 자동화해요.", "tools": ["n8n"], "prompt": "자동화 플로우를 만들어줘."}\n```'
    summarizer._client = _make_mock_client(fake_json)
    articles = [{"title": "AI 자동화", "bullets": ["자동화"], "category": "산업응용"}]
    result = summarizer.generate_tip(articles)
    assert isinstance(result, dict)
    assert result.get("task") == "업무를 자동화해요."

def test_generate_tip_returns_empty_dict_on_invalid_json():
    """JSON 파싱 실패 시 빈 dict 반환."""
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    summarizer._client = _make_mock_client("이건 JSON이 아니에요")
    articles = [{"title": "AI", "bullets": [], "category": "모델 출시"}]
    result = summarizer.generate_tip(articles)
    assert result == {}

def test_generate_tip_strips_markdown_from_task_and_prompt():
    """task/prompt 필드에서 마크다운 기호 제거 확인."""
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    fake_json = '{"task": "**강조** 텍스트에요. _밑줄_도 있어요.", "tools": ["Claude"], "prompt": "# 제목\\n*이탤릭* 프롬프트"}'
    summarizer._client = _make_mock_client(fake_json)
    articles = [{"title": "AI", "bullets": ["b"], "category": "모델 출시"}]
    result = summarizer.generate_tip(articles)
    assert "**" not in result["task"]
    assert "_" not in result["task"]
    assert "#" not in result["prompt"]
    assert "*이탤릭*" not in result["prompt"]
