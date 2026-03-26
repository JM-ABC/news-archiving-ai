# 뉴스레터 v2 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 뉴스레터를 모노크롬+Georgia 디자인으로 교체하고, AI 팁 섹션을 task/tools/prompt 구조화 카드로 고도화한다.

**Architecture:** 3개 파일 수정 (summarizer → newsletter → main). `generate_tip()`이 dict를 반환하도록 변경하고, `newsletter.py`가 이를 3파트 카드로 렌더링한다. TDD — 테스트 먼저 작성 후 구현.

**Tech Stack:** Python 3.12, html.escape, json, re, pytest

**Spec:** `docs/superpowers/specs/2026-03-26-newsletter-v2-design.md`

---

## 파일 구조

| 파일 | 역할 | 변경 유형 |
|---|---|---|
| `summarizer/claude_summarizer.py` | `generate_tip()` dict 반환 + `summarize()` 어체 수정 | Modify |
| `content_generator/newsletter.py` | `generate()` 전체 교체 — 모노크롬+Georgia+구조화 팁 | Modify |
| `main.py` | `email_from` 주입 제거 | Modify (2줄) |
| `tests/test_claude_summarizer.py` | `generate_tip` 테스트 dict 기준으로 교체 | Modify |
| `tests/test_newsletter.py` | 전체 교체 — 새 디자인·구조 기준 | Modify |

---

## Task 1: ClaudeSummarizer — generate_tip() dict 반환 + summarize() 어체

**Files:**
- Modify: `summarizer/claude_summarizer.py:118-155`
- Modify: `summarizer/claude_summarizer.py:21-33` (summarize 프롬프트 어체)
- Test: `tests/test_claude_summarizer.py`

### 1-1. 테스트 파일 교체 (failing)

- [ ] **Step 1: `tests/test_claude_summarizer.py` 전체 교체**

```python
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
```

- [ ] **Step 2: 실패 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/test_claude_summarizer.py -v 2>&1 | tail -20
```

Expected: `test_generate_tip_returns_dict` FAILED, `test_generate_tip_returns_empty_dict_for_no_articles` FAILED (returns `""` not `{}`)

### 1-2. generate_tip() 구현

- [ ] **Step 3: `summarizer/claude_summarizer.py` — `generate_tip()` 교체 (line 118-155)**

```python
    def generate_tip(self, articles: List[Dict]) -> dict:
        """창의적인 AI 자동화 팁 생성. task/tools/prompt dict 반환."""
        if not articles:
            return {}

        articles_text = "\n".join(
            f"- {a['title']}: {' / '.join(a.get('bullets', [])[:2])}"
            for a in articles
            if a.get("category") != "기타"
        )
        if not articles_text:
            return {}

        prompt = f"""다음 AI 뉴스 기사들을 참고해서, 30-40대 직장인이 Claude·ChatGPT·Claude Code·Zapier·n8n 등 AI 도구로 지금 바로 자동화할 수 있는 창의적인 업무 워크플로우를 하나 제안해줘.

오늘 기사에서 영감을 얻되, 기사 내용에 얽매이지 말고 자유롭게 아이디어를 내도 돼.

아래 JSON 형식으로만 반환해 (마크다운 코드블록 없이):
{{
  "task": "자동화 아이디어 설명 2-3문장 (~어요/에요 어체)",
  "tools": ["툴1", "툴2"],
  "prompt": "그 툴에 복붙할 수 있는 구체적 프롬프트 (한국어)"
}}

조건:
- task는 2-3문장, ~어요/에요 어체 사용
- tools는 1-3개 배열
- prompt는 실제로 Claude나 ChatGPT에 그대로 입력 가능한 구체적 문장
- 마크다운 기호(#, **, *) 사용 금지

기사 목록:
{articles_text}

JSON:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            raw = raw.replace("```json", "").replace("```", "").strip()
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                return {}

        import re
        for field in ("task", "prompt"):
            if field in result and isinstance(result[field], str):
                v = result[field]
                v = re.sub(r'\*\*(.+?)\*\*', r'\1', v)
                v = re.sub(r'\*(.+?)\*', r'\1', v)
                v = re.sub(r'^#{1,6}\s*', '', v, flags=re.MULTILINE)
                v = re.sub(r'_(.+?)_', r'\1', v)
                result[field] = v

        return result
```

- [ ] **Step 4: `summarize()` 프롬프트 어체 수정 (line 26-27)**

기존:
```python
- bullets: 핵심 내용 3개 (각 50자 이내 한국어, 구체적 수치·기업명 포함)
- implication: 산업 시사점 1문장 (40자 이내)
```

변경:
```python
- bullets: 핵심 내용 3개 (각 50자 이내 한국어, ~어요/에요 어체, 구체적 수치·기업명 포함)
- implication: 산업 시사점 1문장 (40자 이내, ~어요/에요 어체)
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/test_claude_summarizer.py -v 2>&1 | tail -20
```

Expected: 모든 테스트 PASSED

- [ ] **Step 6: 커밋**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && git add summarizer/claude_summarizer.py tests/test_claude_summarizer.py && git commit -m "feat: generate_tip() dict 반환, summarize() 어체 ~어요/에요"
```

---

## Task 2: main.py — email_from 제거

**Files:**
- Modify: `main.py:113-120`

- [ ] **Step 1: `main.py` line 119 제거**

기존 (line 113-120):
```python
    tip = summarizer.generate_tip(summarized)
    data = {
        "date": today,
        "trends": trends,
        "articles": summarized,
        "tip": tip,
        "email_from": EMAIL_FROM or "",
    }
```

변경:
```python
    tip = summarizer.generate_tip(summarized)
    data = {
        "date": today,
        "trends": trends,
        "articles": summarized,
        "tip": tip,
    }
```

- [ ] **Step 2: summarizer 테스트 통과 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/test_claude_summarizer.py -q 2>&1 | tail -10
```

Expected: 모두 PASSED
Note: `test_newsletter.py`는 아직 구 버전 — vote·tip(str) 테스트가 실패할 수 있음. Task 3에서 교체.

- [ ] **Step 3: 커밋**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && git add main.py && git commit -m "chore: email_from 제거 (투표 기능 삭제)"
```

---

## Task 3: newsletter.py 전체 교체 + 테스트

**Files:**
- Modify: `content_generator/newsletter.py` (전체 교체)
- Modify: `tests/test_newsletter.py` (전체 교체)

### 3-1. 테스트 파일 교체 (failing)

- [ ] **Step 1: `tests/test_newsletter.py` 전체 교체**

```python
from content_generator.newsletter import NewsletterGenerator

SAMPLE = {
    "date": "2026-03-26",
    "trends": "• AI 모델 경쟁 심화\n• 멀티모달 발전",
    "tip": {
        "task": "회의록을 AI로 정리할 수 있어요. 참석자별 액션 아이템이 자동으로 만들어져요.",
        "tools": ["Claude", "ChatGPT"],
        "prompt": "아래 회의록을 액션 아이템으로 정리해줘. 형식: [담당자] - [할 일]",
    },
    "articles": [
        {
            "title": "GPT-5 출시",
            "category": "모델 출시",
            "bullets": ["성능이 대폭 향상됐어요", "멀티모달을 지원해요", "가격이 인하됐어요"],
            "implication": "AI 경쟁이 더욱 심화됐어요",
            "url": "https://example.com/1",
            "label": "TechCrunch",
            "region": "GL",
        },
        {
            "title": "EU AI법 시행",
            "category": "규제",
            "bullets": ["고위험 AI 등록이 의무화됐어요", "과징금이 3%로 설정됐어요"],
            "implication": "기업 부담이 증가했어요",
            "url": "https://example.com/2",
            "label": "ZDNet",
            "region": "KR",
        },
    ]
}


def test_header_contains_ai_news():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "AI" in html
    assert "NEWS" in html
    assert "2026-03-26" in html
    assert "DAILY DIGEST" in html


def test_header_uses_georgia_font():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "Georgia" in html


def test_header_is_monochrome():
    """헤더에 에메랄드 그린(#10b981)이 없어야 함."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "#10b981" not in html


def test_trends_banner_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "TODAY" in html and "TRENDS" in html
    assert "AI 모델 경쟁 심화" in html


def test_trends_banner_dark_background():
    """트렌드 배너 배경이 #374151이어야 함."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "#374151" in html


def test_trends_banner_skipped_when_empty():
    data = {**SAMPLE, "trends": ""}
    html = NewsletterGenerator().generate(data)
    assert "TODAY" not in html or "TRENDS" not in html


def test_headline_section_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "HEADLINE" in html
    assert "GPT-5 출시" in html
    assert "성능이 대폭 향상됐어요" in html
    assert "AI 경쟁이 더욱 심화됐어요" in html
    assert "https://example.com/1" in html


def test_headline_uses_georgia_font():
    html = NewsletterGenerator().generate(SAMPLE)
    # HEADLINE 섹션 안에 Georgia 폰트 적용 확인
    assert html.count("Georgia") >= 2  # 헤더 + 기사 제목 최소 2곳


def test_more_stories_section_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "MORE STORIES" in html
    assert "EU AI법 시행" in html
    assert "고위험 AI 등록이 의무화됐어요" in html


def test_more_stories_has_url_link():
    """MORE STORIES에 원문 보기 링크가 있어야 함."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "https://example.com/2" in html


def test_more_stories_no_vote_link():
    """투표(mailto:) 링크가 없어야 함."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "mailto:" not in html


def test_more_stories_max_5_articles():
    """MORE STORIES는 최대 5개만 표시."""
    articles = [SAMPLE["articles"][0]] + [
        {"title": f"기사{i}", "category": "규제", "bullets": [f"불릿{i}"],
         "implication": "시사점", "url": f"https://example.com/{i}", "label": "X", "region": "GL"}
        for i in range(2, 9)  # 7개 추가 → 총 8개 비-기타
    ]
    data = {**SAMPLE, "articles": articles}
    html = NewsletterGenerator().generate(data)
    # 6번째 이후 기사 제목이 없어야 함 (기사7, 기사8은 잘려야 함)
    assert "기사7" not in html
    assert "기사8" not in html


def test_tip_section_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "오늘의 자동화 TASK" in html
    assert "회의록을 AI로 정리할 수 있어요" in html
    assert "추천 툴" in html
    assert "Claude" in html
    assert "복붙 프롬프트" in html
    assert "아래 회의록을 액션 아이템으로 정리해줘" in html


def test_tip_section_skipped_when_empty_dict():
    data = {**SAMPLE, "tip": {}}
    html = NewsletterGenerator().generate(data)
    assert "오늘의 자동화 TASK" not in html


def test_tip_section_skipped_when_none():
    data = {**SAMPLE, "tip": None}
    html = NewsletterGenerator().generate(data)
    assert "오늘의 자동화 TASK" not in html


def test_tip_tools_skipped_when_empty():
    data = {**SAMPLE, "tip": {"task": "팁이에요.", "tools": [], "prompt": "프롬프트"}}
    html = NewsletterGenerator().generate(data)
    assert "추천 툴" not in html


def test_tip_prompt_skipped_when_empty():
    data = {**SAMPLE, "tip": {"task": "팁이에요.", "tools": ["Claude"], "prompt": ""}}
    html = NewsletterGenerator().generate(data)
    assert "복붙 프롬프트" not in html


def test_all_categories_other_skips_headline_and_more():
    data = {**SAMPLE, "articles": [
        {"title": "기타 기사", "category": "기타", "bullets": [],
         "implication": "", "url": "https://example.com/3", "label": "X", "region": "GL"}
    ]}
    html = NewsletterGenerator().generate(data)
    assert "HEADLINE" not in html
    assert "MORE STORIES" not in html


def test_xss_escaping():
    data = {
        **SAMPLE,
        "tip": {"task": "<script>alert(1)</script>", "tools": ["Claude"], "prompt": "ok"},
        "articles": [{
            "title": "<b>XSS</b>", "category": "모델 출시",
            "bullets": ["<test>"], "implication": "imp",
            "url": "https://example.com/safe", "label": "T", "region": "GL"
        }]
    }
    html = NewsletterGenerator().generate(data)
    assert "<script>" not in html
    assert "&lt;" in html


def test_mobile_viewport_meta():
    """모바일 viewport meta 태그 포함 확인."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "viewport" in html


def test_label_region_fallback():
    """label/region 없어도 오류 없이 렌더링."""
    data = {**SAMPLE, "articles": [
        {"title": "테스트", "category": "규제", "bullets": ["b1"],
         "implication": "imp", "url": "https://x.com"}  # label/region 없음
    ]}
    html = NewsletterGenerator().generate(data)
    assert "테스트" in html
```

- [ ] **Step 2: 실패 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/test_newsletter.py -v 2>&1 | tail -25
```

Expected: 여러 테스트 FAILED (tip이 string이고, vote 링크가 있고, MORE STORIES url 없고 등)

### 3-2. newsletter.py 교체

- [ ] **Step 3: `content_generator/newsletter.py` 전체 교체**

```python
from html import escape
from typing import Dict


class NewsletterGenerator:
    def generate(self, data: Dict) -> str:
        """에디토리얼 매거진 스타일 HTML 뉴스레터 생성 (v2: 모노크롬 + Georgia)."""
        date = escape(data["date"])
        trends_raw = data.get("trends", "")
        articles = data["articles"]
        tip = data.get("tip") or {}

        # 트렌드 배너
        if trends_raw.strip():
            trend_items = [
                t.lstrip("• ").strip()
                for t in trends_raw.split("\n")
                if t.strip()
            ]
            trends_inline = escape(" · ".join(trend_items))
            trends_banner = f"""
<div style="background:#374151;padding:10px 28px;">
  <div style="font-size:9px;font-weight:900;letter-spacing:2px;color:#e5e7eb;font-family:'Segoe UI',Arial,sans-serif;line-height:1.8;word-break:keep-all;">
    🔑 TODAY&#x27;S TRENDS<br>
    <span style="font-weight:400;color:rgba(229,231,235,0.7);font-size:9px;letter-spacing:0;">{trends_inline}</span>
  </div>
</div>"""
        else:
            trends_banner = ""

        # 기사 분류
        valid = [a for a in articles if a.get("category") != "기타"]
        headline_article = valid[0] if valid else None
        more_articles = valid[1:6] if len(valid) > 1 else []

        # HEADLINE 섹션
        if headline_article:
            a = headline_article
            bullets_html = "".join(
                f"<li style='margin-bottom:4px;'>{escape(b)}</li>"
                for b in a.get("bullets", [])
            )
            headline_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;font-family:'Segoe UI',Arial,sans-serif;">HEADLINE</span>
</div>
<div style="margin-bottom:22px;padding:16px;background:#f8fafc;border-radius:4px;border-left:4px solid #4b5563;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap;">
    <span style="background:#111827;color:#d1d5db;font-size:8px;font-weight:700;padding:2px 8px;border-radius:2px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('category', ''))}</span>
    <span style="color:#9ca3af;font-size:9px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('label', ''))} · {escape(a.get('region', ''))}</span>
  </div>
  <div style="font-size:14px;font-weight:700;color:#111827;line-height:1.4;margin-bottom:8px;font-family:Georgia,'Times New Roman',serif;">{escape(a['title'])}</div>
  <ul style="margin:0 0 8px;padding-left:16px;color:#374151;font-size:11px;line-height:1.8;font-family:'Segoe UI',Arial,sans-serif;">{bullets_html}</ul>
  <div style="font-size:10px;color:#6b7280;font-style:italic;margin-bottom:10px;font-family:'Segoe UI',Arial,sans-serif;">👉 {escape(a.get('implication', ''))}</div>
  <a href="{escape(a['url'])}" style="font-size:10px;color:#4b5563;font-weight:700;text-decoration:underline;font-family:'Segoe UI',Arial,sans-serif;">원문 보기 →</a>
</div>"""
        else:
            headline_html = ""

        # AI 팁 섹션
        if tip.get("task"):
            task_text = escape(tip["task"])

            tools_html = ""
            if tip.get("tools"):
                tags = "".join(
                    f'<span style="background:#e5e7eb;color:#374151;font-size:9px;font-weight:700;padding:3px 10px;border-radius:12px;font-family:\'Segoe UI\',Arial,sans-serif;">{escape(t)}</span> '
                    for t in tip["tools"]
                )
                tools_html = f"""
  <div style="margin-bottom:10px;">
    <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:6px;font-family:'Segoe UI',Arial,sans-serif;">🛠 추천 툴</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">{tags}</div>
  </div>"""

            prompt_html = ""
            if tip.get("prompt"):
                prompt_html = f"""
  <div>
    <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:6px;font-family:'Segoe UI',Arial,sans-serif;">📋 복붙 프롬프트</div>
    <div style="background:#111827;border-radius:4px;padding:12px 14px;font-family:'Courier New',Courier,monospace;font-size:10px;color:#e5e7eb;line-height:1.7;word-break:keep-all;">{escape(tip['prompt'])}</div>
  </div>"""

            tip_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;font-family:'Segoe UI',Arial,sans-serif;">💡 오늘 바로 써먹는 AI 팁</span>
</div>
<div style="margin-bottom:22px;padding:16px;background:#f9fafb;border-radius:4px;border-left:4px solid #6b7280;">
  <div style="margin-bottom:10px;">
    <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:4px;font-family:'Segoe UI',Arial,sans-serif;">✦ 오늘의 자동화 TASK</div>
    <div style="font-size:11px;color:#374151;line-height:1.8;font-family:'Segoe UI',Arial,sans-serif;">{task_text}</div>
  </div>
  {tools_html}
  {prompt_html}
</div>"""
        else:
            tip_html = ""

        # MORE STORIES 섹션
        if more_articles:
            cards = ""
            for i, a in enumerate(more_articles):
                bullets_text = "<br>".join(
                    f"• {escape(b)}" for b in a.get("bullets", [])[:2]
                )
                cards += f"""
<div style="margin-bottom:12px;padding:14px;background:#f8fafc;border-left:3px solid #d1d5db;border-radius:4px;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px;flex-wrap:wrap;">
    <span style="background:#f3f4f6;color:#374151;font-size:8px;font-weight:700;padding:2px 8px;border-radius:2px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('category', ''))}</span>
    <span style="color:#9ca3af;font-size:9px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('label', ''))} · {escape(a.get('region', ''))}</span>
  </div>
  <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:6px;line-height:1.4;font-family:Georgia,'Times New Roman',serif;">{i + 1}. {escape(a['title'])}</div>
  <div style="color:#6b7280;font-size:10px;line-height:1.7;font-family:'Segoe UI',Arial,sans-serif;">{bullets_text}</div>
  <div style="margin-top:10px;"><a href="{escape(a['url'])}" style="font-size:10px;color:#4b5563;font-weight:700;text-decoration:underline;font-family:'Segoe UI',Arial,sans-serif;">원문 보기 →</a></div>
</div>"""
            more_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;font-family:'Segoe UI',Arial,sans-serif;">MORE STORIES</span>
</div>
{cards}"""
        else:
            more_html = ""

        return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 뉴스 | {date}</title></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f1f5f9;margin:0;padding:12px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:4px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

  <!-- 헤더 -->
  <div style="background:#111827;padding:24px 28px 18px;">
    <div style="display:flex;align-items:flex-end;flex-wrap:wrap;gap:8px;margin-bottom:4px;">
      <div>
        <span style="font-size:9px;letter-spacing:3px;color:#9ca3af;font-weight:700;display:block;margin-bottom:8px;font-family:'Segoe UI',Arial,sans-serif;">DAILY DIGEST</span>
        <span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#fff;font-family:Georgia,'Times New Roman',serif;">AI </span><span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#e5e7eb;font-family:Georgia,'Times New Roman',serif;">NEWS</span>
      </div>
      <div style="margin-left:auto;text-align:right;padding-bottom:4px;">
        <div style="color:#6b7280;font-size:9px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">VOL. 01</div>
        <div style="color:#9ca3af;font-size:9px;margin-top:2px;font-family:'Segoe UI',Arial,sans-serif;">{date}</div>
      </div>
    </div>
    <div style="height:1px;background:rgba(255,255,255,0.12);margin-top:14px;"></div>
  </div>

  <!-- 트렌드 배너 -->
  {trends_banner}

  <!-- 기사 섹션 -->
  <div style="padding:22px 28px;">
    {headline_html}
    {tip_html}
    {more_html}
  </div>

  <!-- 푸터 -->
  <div style="background:#111827;padding:16px 28px;text-align:center;">
    <div style="margin-bottom:4px;">
      <span style="font-size:16px;font-weight:900;color:#fff;font-family:Georgia,'Times New Roman',serif;">AI </span><span style="font-size:16px;font-weight:900;color:#e5e7eb;font-family:Georgia,'Times New Roman',serif;">NEWS</span>
    </div>
    <div style="color:#4b5563;font-size:8px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">매일 오전 8시 · AI 뉴스 다이제스트</div>
  </div>

</div>
</body></html>"""

    def generate_txt(self, data: Dict) -> str:
        """텍스트 파일용 리포트 생성."""
        date = data["date"]
        trends = data["trends"]
        articles = data["articles"]

        lines = [f"AI 뉴스 트렌드 | {date}", "---", "", "🔑 오늘의 핵심 트렌드", ""]
        lines += [t for t in trends.split("\n") if t.strip()]
        lines += ["", "---"]

        for a in articles:
            lines.append(f"\n① {a['title']}")
            lines.append(f"   출처: {a.get('label', '')} ({a.get('region', '')})")
            for b in a.get("bullets", []):
                lines.append(f"   - {b}")
            lines.append(f"\n   👉 {a.get('implication', '')}")
            lines.append(f"\n   원문: {a['url']}")
            lines.append("---")

        return "\n".join(lines)
```

- [ ] **Step 4: 전체 테스트 통과 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/ -v 2>&1 | tail -30
```

Expected: 모든 테스트 PASSED (warning 무시)

- [ ] **Step 5: 커밋**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && git add content_generator/newsletter.py tests/test_newsletter.py && git commit -m "feat: 뉴스레터 v2 — 모노크롬+Georgia+AI팁 구조화+MORE STORIES 개선"
```

---

## Task 4: GitHub Push

**Files:** 없음 (git push만)

- [ ] **Step 1: 전체 테스트 최종 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: `N passed, 1 warning`

- [ ] **Step 2: GitHub push**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && git push origin main 2>&1
```

Expected: `main -> main` 정상 push
