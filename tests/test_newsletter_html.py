"""뉴스레터 HTML 구조 테스트 — 아웃룩 호환성 검증."""
import pytest
from content_generator.newsletter import NewsletterGenerator

SAMPLE_DATA = {
    "date": "2026-04-15",
    "trends": "• GPT-5 공개\n• 구글 AI 기능 확대\n• 로컬 모델 급성장",
    "articles": [
        {
            "title": "테스트 헤드라인 기사",
            "url": "https://example.com/1",
            "category": "AI 모델",
            "label": "테스트출처",
            "region": "KR",
            "score": 10,
            "bullets": ["핵심 내용 1", "핵심 내용 2"],
            "implication": "이것이 중요한 이유",
        },
        {
            "title": "두 번째 기사",
            "url": "https://example.com/2",
            "category": "AI 정책",
            "label": "출처2",
            "region": "GL",
            "score": 5,
            "bullets": ["내용 A", "내용 B"],
            "implication": "시사점",
        },
    ],
    "tip": {
        "task": "이메일 자동 분류하기",
        "tools": ["Gmail", "Claude"],
        "steps": ["1단계 설명", "2단계 설명", "3단계 설명"],
        "prompt": "다음 이메일을 [카테고리]로 분류해줘:\n[이메일 내용]",
    },
}


def get_html():
    return NewsletterGenerator().generate(SAMPLE_DATA)


def test_no_flex():
    """display:flex 없어야 함 — 아웃룩 미지원."""
    assert "display:flex" not in get_html()


def test_no_box_shadow():
    """box-shadow 없어야 함 — 아웃룩 미지원."""
    assert "box-shadow" not in get_html()


def test_no_border_radius():
    """border-radius 없어야 함 — 아웃룩 미지원."""
    assert "border-radius" not in get_html()


def test_no_rgba():
    """rgba() 없어야 함 — 아웃룩 미지원."""
    assert "rgba(" not in get_html()


def test_bgcolor_body():
    """body에 bgcolor 속성 존재."""
    assert 'bgcolor="#f5f7fa"' in get_html()


def test_header_bgcolor():
    """헤더 다크 배경색 존재."""
    assert 'bgcolor="#111827"' in get_html()


def test_trends_banner_bgcolor():
    """트렌드 배너 배경색 존재."""
    assert 'bgcolor="#374151"' in get_html()


def test_card_bgcolor():
    """콘텐츠 카드 배경색 통일."""
    assert 'bgcolor="#f5f7fa"' in get_html()


def test_table_structure():
    """테이블 기반 구조 사용."""
    html = get_html()
    assert html.count("<table") >= 3


def test_headline_rendered():
    """헤드라인 기사 제목 렌더링."""
    assert "테스트 헤드라인 기사" in get_html()


def test_more_stories_rendered():
    """MORE STORIES 기사 렌더링."""
    assert "두 번째 기사" in get_html()


def test_tip_rendered():
    """AI 팁 렌더링."""
    assert "이메일 자동 분류하기" in get_html()


def test_trends_rendered():
    """트렌드 텍스트 렌더링."""
    assert "GPT-5 공개" in get_html()


def test_xss_escape():
    """XSS 방어 — 특수문자 이스케이프."""
    data = {**SAMPLE_DATA, "date": "<script>alert(1)</script>"}
    html = NewsletterGenerator().generate(data)
    assert "<script>" not in html
