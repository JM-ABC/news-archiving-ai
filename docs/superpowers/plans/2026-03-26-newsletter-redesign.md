# Newsletter Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `newsletter.py`의 HTML을 에디토리얼 매거진 스타일로 교체하고, AI 팁 섹션과 mailto 투표 링크를 추가한다.

**Architecture:** `ClaudeSummarizer`에 `generate_tip()` 추가 → `main.py`에서 `data["tip"]`·`data["email_from"]` 주입 → `NewsletterGenerator.generate()`에서 6섹션 HTML 렌더링.

**Tech Stack:** Python 3.12, html.escape, anthropic SDK (claude-haiku-4-5-20251001), pytest

---

## 파일 맵

| 파일 | 변경 |
|---|---|
| `summarizer/claude_summarizer.py` | `generate_tip()` 신규 메서드 추가 |
| `main.py` | `data["tip"]`·`data["email_from"]` 주입 (5/8 이후) |
| `content_generator/newsletter.py` | `generate()` 전체 교체 (6섹션 디자인) |
| `tests/test_claude_summarizer.py` | `generate_tip()` 단위 테스트 추가 |
| `tests/test_newsletter.py` | 기존 테스트 업데이트 + 신규 섹션 테스트 추가 |

---

## Task 1: `generate_tip()` 메서드 추가

**Files:**
- Modify: `summarizer/claude_summarizer.py`
- Test: `tests/test_claude_summarizer.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_claude_summarizer.py` 끝에 추가:

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/test_claude_summarizer.py::test_generate_tip_returns_string tests/test_claude_summarizer.py::test_generate_tip_empty_articles -v
```

Expected: `AttributeError: 'ClaudeSummarizer' object has no attribute 'generate_tip'`

- [ ] **Step 3: `generate_tip()` 구현**

`summarizer/claude_summarizer.py` 끝에 추가:

```python
def generate_tip(self, articles: List[Dict]) -> str:
    """오늘 기사 중 30-40대 직장인이 바로 써먹을 수 있는 AI 팁 1-2문장 생성."""
    if not articles:
        return ""

    articles_text = "\n".join(
        f"- {a['title']}: {' / '.join(a.get('bullets', [])[:2])}"
        for a in articles
        if a.get("category") != "기타"
    )
    if not articles_text:
        return ""

    prompt = f"""다음 AI 뉴스 기사들 중 하나를 골라, 30-40대 직장인이 오늘 당장 써먹을 수 있는 구체적인 AI 활용 팁을 1-2문장으로 작성하세요.

조건:
- 특정 도구나 기능명을 명시할 것
- "이렇게 써보세요" 같은 실전 행동 지침 포함
- 마크다운 기호(#, **, *) 사용 금지
- 예시: "오늘 소개된 Claude 오토 모드, 링크드인 프로필 초안 작성에 써보세요. 프롬프트: '내 경력을 보여줄게, 3줄로 요약해줘'"

기사 목록:
{articles_text}

AI 팁:"""

    msg = self._client.messages.create(
        model=self.model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    import re
    raw = re.sub(r'\*\*(.+?)\*\*', r'\1', raw)
    raw = re.sub(r'\*(.+?)\*', r'\1', raw)
    raw = re.sub(r'^#{1,6}\s*', '', raw, flags=re.MULTILINE)
    return raw
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/test_claude_summarizer.py::test_generate_tip_returns_string tests/test_claude_summarizer.py::test_generate_tip_empty_articles -v
```

Expected: 2 passed

- [ ] **Step 5: 커밋**

```bash
git add summarizer/claude_summarizer.py tests/test_claude_summarizer.py
git commit -m "feat: ClaudeSummarizer에 generate_tip() 메서드 추가"
```

---

## Task 2: `main.py`에 `tip`·`email_from` 주입

**Files:**
- Modify: `main.py`

- [ ] **Step 1: 변경 위치 확인**

`main.py`에서 `data = {"date": today, "trends": trends, "articles": summarized}` 라인을 찾는다 (약 113번째 줄).

- [ ] **Step 2: `data` 딕셔너리에 tip·email_from 추가**

기존:
```python
data = {"date": today, "trends": trends, "articles": summarized}
```

변경:
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

- [ ] **Step 3: 전체 테스트 통과 확인**

```bash
python -m pytest tests/ -v --ignore=tests/test_gstack_crawler.py
```

Expected: 모두 pass

- [ ] **Step 4: 커밋**

```bash
git add main.py
git commit -m "feat: main.py에 tip·email_from 데이터 주입"
```

---

## Task 3: `newsletter.py` HTML 디자인 교체

**Files:**
- Modify: `content_generator/newsletter.py`
- Test: `tests/test_newsletter.py`

- [ ] **Step 1: 테스트 파일 전체 교체**

`tests/test_newsletter.py` 파일 전체를 아래 내용으로 교체한다 (기존 테스트 함수 및 SAMPLE 모두 삭제):

```python
from content_generator.newsletter import NewsletterGenerator

SAMPLE = {
    "date": "2026-03-26",
    "trends": "• AI 모델 경쟁 심화\n• 멀티모달 발전",
    "tip": "Claude 오토 모드를 링크드인 프로필 요약에 써보세요.",
    "email_from": "test@example.com",
    "articles": [
        {
            "title": "GPT-5 출시",
            "category": "모델 출시",
            "bullets": ["성능 대폭 향상", "멀티모달 지원", "가격 인하"],
            "implication": "AI 경쟁 격화",
            "url": "https://example.com/1",
            "label": "TechCrunch",
            "region": "GL",
        },
        {
            "title": "EU AI법 시행",
            "category": "규제",
            "bullets": ["고위험 AI 등록 의무", "과징금 3%"],
            "implication": "기업 부담 증가",
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

def test_trends_banner_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "TODAY&#x27;S TRENDS" in html or "TODAY'S TRENDS" in html
    assert "AI 모델 경쟁 심화" in html

def test_trends_banner_skipped_when_empty():
    data = {**SAMPLE, "trends": ""}
    html = NewsletterGenerator().generate(data)
    assert "TODAY&#x27;S TRENDS" not in html and "TODAY'S TRENDS" not in html

def test_headline_section_first_article():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "HEADLINE" in html
    assert "GPT-5 출시" in html
    assert "성능 대폭 향상" in html
    assert "AI 경쟁 격화" in html  # implication in HEADLINE
    assert "https://example.com/1" in html  # url in HEADLINE

def test_more_stories_section():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "MORE STORIES" in html
    assert "EU AI법 시행" in html
    assert "고위험 AI 등록 의무" in html

def test_more_stories_no_implication_or_url():
    html = NewsletterGenerator().generate(SAMPLE)
    # MORE STORIES에는 두 번째 기사 url·implication이 없어야 함
    assert "https://example.com/2" not in html
    assert "기업 부담 증가" not in html  # 두 번째 기사의 implication

def test_tip_section_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "Claude 오토 모드를 링크드인 프로필 요약에 써보세요." in html

def test_tip_section_skipped_when_empty():
    data = {**SAMPLE, "tip": ""}
    html = NewsletterGenerator().generate(data)
    assert "Claude 오토 모드" not in html

def test_vote_link_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "mailto:test@example.com" in html

def test_vote_link_skipped_when_no_email_from():
    data = {**SAMPLE, "email_from": ""}
    html = NewsletterGenerator().generate(data)
    assert "mailto:" not in html

def test_all_categories_other_skips_headline_and_more():
    data = {**SAMPLE, "articles": [
        {"title": "기타 기사", "category": "기타", "bullets": [], "implication": "", "url": "https://example.com/3", "label": "X", "region": "GL"}
    ]}
    html = NewsletterGenerator().generate(data)
    assert "HEADLINE" not in html
    assert "MORE STORIES" not in html

def test_xss_escaping():
    data = {**SAMPLE, "tip": "<script>alert(1)</script>", "articles": [{
        "title": "<b>XSS</b>", "category": "모델 출시",
        "bullets": ["<test>"], "implication": "imp",
        "url": "https://example.com/safe", "label": "T", "region": "GL"
    }]}
    html = NewsletterGenerator().generate(data)
    assert "<script>" not in html
    assert "&lt;b&gt;" in html or "&lt;script&gt;" in html
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/test_newsletter.py -v
```

Expected: 대부분 FAIL (새 디자인 미구현)

- [ ] **Step 3: `generate()` 메서드 교체**

`content_generator/newsletter.py`의 `generate()` 메서드 전체를 아래로 교체:

```python
def generate(self, data: Dict) -> str:
    """에디토리얼 매거진 스타일 HTML 뉴스레터 생성."""
    date = escape(data["date"])
    trends_raw = data.get("trends", "")
    articles = data["articles"]
    tip = data.get("tip", "")
    email_from = data.get("email_from", "")

    # 트렌드 배너
    if trends_raw.strip():
        trend_items = [
            t.lstrip("• ").strip()
            for t in trends_raw.split("\n")
            if t.strip()
        ]
        trends_inline = escape(" · ".join(trend_items))
        trends_banner = f"""
<div style="background:#10b981;padding:10px 32px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#fff;">🔑 TODAY'S TRENDS &nbsp;·&nbsp; </span>
  <span style="color:rgba(255,255,255,0.75);font-size:9px;">{trends_inline}</span>
</div>"""
    else:
        trends_banner = ""

    # 기사 분류
    valid = [a for a in articles if a.get("category") != "기타"]
    headline_article = valid[0] if valid else None
    more_articles = valid[1:] if len(valid) > 1 else []

    # HEADLINE 섹션
    if headline_article:
        a = headline_article
        bullets_html = "".join(
            f"<li style='margin-bottom:4px;'>{escape(b)}</li>"
            for b in a.get("bullets", [])
        )
        headline_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;">HEADLINE</span>
</div>
<div style="margin-bottom:20px;padding:16px;background:#f8fafc;border-radius:4px;border-left:4px solid #10b981;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
    <span style="background:#111827;color:#10b981;font-size:8px;font-weight:700;padding:2px 8px;border-radius:2px;letter-spacing:1px;">{escape(a.get('category',''))}</span>
    <span style="color:#9ca3af;font-size:9px;">{escape(a.get('label',''))} · {escape(a.get('region',''))}</span>
  </div>
  <div style="font-size:14px;font-weight:800;color:#111827;line-height:1.3;margin-bottom:8px;">{escape(a['title'])}</div>
  <ul style="margin:0 0 8px;padding-left:16px;color:#374151;font-size:11px;line-height:1.7;">{bullets_html}</ul>
  <div style="font-size:10px;color:#6b7280;font-style:italic;margin-bottom:8px;">👉 {escape(a.get('implication',''))}</div>
  <a href="{escape(a['url'])}" style="font-size:10px;color:#10b981;font-weight:700;text-decoration:none;">원문 보기 →</a>
</div>"""
    else:
        headline_html = ""

    # AI 팁 섹션
    if tip.strip():
        tip_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;">💡 오늘 바로 써먹는 AI 팁</span>
</div>
<div style="margin-bottom:20px;padding:16px;background:#fffbeb;border-radius:4px;border-left:4px solid #f59e0b;">
  <p style="margin:0;font-size:12px;color:#374151;line-height:1.7;">{escape(tip)}</p>
</div>"""
    else:
        tip_html = ""

    # MORE STORIES 섹션
    if more_articles:
        cards = ""
        for i, a in enumerate(more_articles):
            is_last = i == len(more_articles) - 1
            border = "" if is_last else "border-bottom:1px solid #e5e7eb;"
            bullets_text = "<br>".join(
                f"• {escape(b)}" for b in a.get("bullets", [])[:2]
            )
            vote_link = ""
            if email_from:
                vote_link = (
                    f'<a href="mailto:{escape(email_from)}'
                    f'?subject={escape("AI뉴스 투표 " + data["date"])}'
                    f'&body={escape(str(i+1) + "번 기사 선택")}"'
                    f' style="font-size:10px;color:#10b981;font-weight:700;text-decoration:none;">👍 이 기사 선택</a>'
                )
            cards += f"""
<div style="margin-bottom:14px;padding-bottom:14px;{border}">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px;">
    <span style="background:#f3f4f6;color:#374151;font-size:8px;font-weight:700;padding:2px 8px;border-radius:2px;letter-spacing:1px;">{escape(a.get('category',''))}</span>
    <span style="color:#9ca3af;font-size:9px;">{escape(a.get('label',''))} · {escape(a.get('region',''))}</span>
  </div>
  <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:6px;line-height:1.3;">{i+1}. {escape(a['title'])}</div>
  <div style="color:#6b7280;font-size:10px;line-height:1.6;">{bullets_text}</div>
  {"<div style='margin-top:6px;'>" + vote_link + "</div>" if vote_link else ""}
</div>"""
        more_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;">MORE STORIES</span>
</div>
{cards}"""
    else:
        more_html = ""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><title>AI 뉴스 | {date}</title></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:4px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

  <!-- 헤더 -->
  <div style="background:#111827;padding:28px 32px 20px;">
    <div style="margin-bottom:4px;">
      <span style="font-size:9px;letter-spacing:3px;color:#6ee7b7;font-weight:700;display:block;margin-bottom:8px;">DAILY DIGEST</span>
      <span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#fff;">AI </span><span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#10b981;">NEWS</span>
    </div>
    <div style="text-align:right;margin-top:-28px;">
      <div style="color:#6b7280;font-size:9px;letter-spacing:1px;">VOL. 01</div>
      <div style="color:#9ca3af;font-size:9px;margin-top:2px;">{date}</div>
    </div>
    <div style="height:2px;background:linear-gradient(to right,#10b981,#059669,transparent);margin-top:14px;"></div>
  </div>

  <!-- 트렌드 배너 -->
  {trends_banner}

  <!-- 기사 섹션 -->
  <div style="padding:24px 32px;">
    {headline_html}
    {tip_html}
    {more_html}
  </div>

  <!-- 푸터 -->
  <div style="background:#111827;padding:16px 32px;text-align:center;">
    <div style="margin-bottom:4px;">
      <span style="font-size:16px;font-weight:900;color:#fff;">AI </span><span style="font-size:16px;font-weight:900;color:#10b981;">NEWS</span>
    </div>
    <div style="color:#4b5563;font-size:8px;letter-spacing:1px;">매일 오전 8시 · AI 뉴스 다이제스트</div>
  </div>

</div>
</body></html>"""
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/test_newsletter.py -v
```

Expected: 모두 pass

- [ ] **Step 5: 전체 테스트 통과 확인**

```bash
python -m pytest tests/ -v --ignore=tests/test_gstack_crawler.py
```

Expected: 모두 pass (gstack은 바이너리 의존으로 제외)

- [ ] **Step 6: 커밋**

```bash
git add content_generator/newsletter.py tests/test_newsletter.py
git commit -m "feat: 뉴스레터 에디토리얼 디자인 + AI팁 섹션 + 투표 링크"
```

---

## Task 4: GitHub Push

- [ ] **Step 1: 최종 확인**

```bash
python -m pytest tests/ -v --ignore=tests/test_gstack_crawler.py
```

Expected: 모두 pass

- [ ] **Step 2: Push**

```bash
git push origin main
```
