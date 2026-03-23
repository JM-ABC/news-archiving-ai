from unittest.mock import MagicMock
from content_generator.linkedin import LinkedInGenerator
from content_generator.threads import ThreadsGenerator
from content_generator.instagram import InstagramGenerator

SAMPLE_DATA = {
    "date": "2026-03-24",
    "trends": "• AI 모델 경쟁 심화\n• 멀티모달 발전\n• 규제 강화",
    "articles": [
        {
            "title": "GPT-5 출시",
            "category": "모델 출시",
            "bullets": ["성능 대폭 향상", "멀티모달 지원"],
            "implication": "AI 경쟁 격화",
            "url": "https://example.com/1",
        }
    ]
}

def _mock_client(text):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    m = MagicMock()
    m.messages.create.return_value = mock_msg
    return m

def test_linkedin_generate_returns_string():
    gen = LinkedInGenerator(client=_mock_client("링크드인 포스트 내용"), model="test")
    result = gen.generate(SAMPLE_DATA)
    assert isinstance(result, str)
    assert len(result) > 0

def test_linkedin_calls_api_with_model():
    mock_client = _mock_client("포스트")
    gen = LinkedInGenerator(client=mock_client, model="claude-haiku-4-5-20251001")
    gen.generate(SAMPLE_DATA)
    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-haiku-4-5-20251001"

def test_threads_generate_returns_string():
    gen = ThreadsGenerator(client=_mock_client("스레드 포스트"), model="test")
    result = gen.generate(SAMPLE_DATA)
    assert isinstance(result, str)

def test_threads_calls_api_with_model():
    mock_client = _mock_client("포스트")
    gen = ThreadsGenerator(client=mock_client, model="claude-haiku-4-5-20251001")
    gen.generate(SAMPLE_DATA)
    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-haiku-4-5-20251001"

def test_instagram_generate_returns_string():
    gen = InstagramGenerator(client=_mock_client("인스타 캡션 #AI"), model="test")
    result = gen.generate(SAMPLE_DATA)
    assert isinstance(result, str)

def test_instagram_calls_api_with_model():
    mock_client = _mock_client("캡션")
    gen = InstagramGenerator(client=mock_client, model="claude-haiku-4-5-20251001")
    gen.generate(SAMPLE_DATA)
    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-haiku-4-5-20251001"
