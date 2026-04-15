# 뉴스레터 아웃룩 호환 테이블 기반 재설계 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `newsletter.py`의 `generate()` 메서드를 `<div>` + CSS 기반에서 `<table>` + `bgcolor` 기반으로 재작성해 아웃룩/Gmail/모바일 등 모든 이메일 클라이언트에서 일관되게 렌더링되도록 한다.

**Architecture:** 기존 Python 문자열 f-string 방식 유지. `<div>`/`display:flex`/`box-shadow`/`border-radius`/`rgba()`를 모두 제거하고 `<table>` 중첩 + `bgcolor` HTML 속성으로 대체. `generate_txt()`는 변경 없음.

**Tech Stack:** Python 3.12, html.escape, 표준 이메일 HTML (테이블 기반)

---

### Task 1: 테스트 파일 준비

**Files:**
- Create: `tests/test_newsletter_html.py`

**Step 1: 테스트 파일 생성**

```python
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
```

**Step 2: 테스트 실행 — 실패 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI"
python -m pytest tests/test_newsletter_html.py -v
```

Expected: `test_no_flex`, `test_no_box_shadow`, `test_no_border_radius`, `test_no_rgba`, `test_bgcolor_body` 등 다수 FAIL

**Step 3: 커밋**

```bash
git add tests/test_newsletter_html.py
git commit -m "test: 뉴스레터 아웃룩 호환성 테스트 추가"
```

---

### Task 2: 헬퍼 메서드 — 섹션 레이블 행

**Files:**
- Modify: `content_generator/newsletter.py`

기존 `generate()` 상단에 아래 헬퍼를 추가한다 (클래스 메서드).

**Step 1: 헬퍼 메서드 추가**

`class NewsletterGenerator:` 바로 아래 `generate()` 위에 삽입:

```python
def _section_label(self, text: str) -> str:
    """섹션 구분선 + 레이블 행 (테이블 행 반환)."""
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:14px;">
  <tr>
    <td height="2" bgcolor="#111827"></td>
  </tr>
  <tr>
    <td style="padding-top:6px;font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;font-family:'Segoe UI',Arial,sans-serif;">{text}</td>
  </tr>
</table>"""

def _spacer(self, height: int = 12) -> str:
    """카드 간 여백 행."""
    return f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td height="{height}"></td></tr></table>'
```

**Step 2: 테스트 실행**

```bash
python -m pytest tests/test_newsletter_html.py -v
```

Expected: 일부 통과, 일부 여전히 실패 (generate() 미수정 상태)

---

### Task 3: 헤더 + 트렌드 배너 재작성

**Files:**
- Modify: `content_generator/newsletter.py`

**Step 1: 트렌드 배너 섹션 교체**

기존 `trends_banner` 생성 블록 전체를 아래로 교체:

```python
        # 트렌드 배너
        if trends_raw.strip():
            trend_items = [
                t.lstrip("• ").strip()
                for t in trends_raw.split("\n")
                if t.strip() and "핵심 트렌드" not in t and "트렌드 3가지" not in t
            ]
            trends_lines = "<br>".join(
                f'• {escape(t)}'
                for t in trend_items
            )
            trends_banner = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td bgcolor="#374151" style="padding:10px 28px;font-size:9px;font-weight:900;letter-spacing:0;color:#e5e7eb;font-family:'Segoe UI',Arial,sans-serif;line-height:1.8;word-break:keep-all;">
      🔑 TODAY&#x27;S TRENDS<br>{trends_lines}
    </td>
  </tr>
</table>"""
        else:
            trends_banner = ""
```

**Step 2: 테스트 실행**

```bash
python -m pytest tests/test_newsletter_html.py::test_trends_banner_bgcolor tests/test_newsletter_html.py::test_trends_rendered -v
```

Expected: PASS

---

### Task 4: HEADLINE 카드 재작성

**Files:**
- Modify: `content_generator/newsletter.py`

**Step 1: headline_html 블록 교체**

기존 `if headline_article:` 블록 전체를 교체:

```python
        if headline_article:
            a = headline_article
            bullets_html = "".join(
                f"<tr><td style='padding:2px 0;color:#374151;font-size:11px;font-family:\"Segoe UI\",Arial,sans-serif;'>• {escape(b)}</td></tr>"
                for b in a.get("bullets", [])
            )
            headline_html = f"""
{self._section_label("HEADLINE")}
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:22px;">
  <tr>
    <td width="4" bgcolor="#4b5563"></td>
    <td bgcolor="#f5f7fa" style="padding:16px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-bottom:12px;">
            <span style="background:#111827;color:#d1d5db;font-size:8px;font-weight:700;padding:2px 8px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('category', ''))}</span>
            &nbsp;
            <span style="color:#9ca3af;font-size:9px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('label', ''))} · {escape(a.get('region', ''))}</span>
          </td>
        </tr>
        <tr>
          <td style="font-size:14px;font-weight:700;color:#111827;line-height:1.4;padding-bottom:12px;font-family:Georgia,'Times New Roman',serif;">{escape(a['title'])}</td>
        </tr>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:8px;">
          {bullets_html}
        </table>
        <tr>
          <td style="font-size:10px;color:#6b7280;font-style:italic;padding-bottom:10px;font-family:'Segoe UI',Arial,sans-serif;">👉 {escape(a.get('implication', ''))}</td>
        </tr>
        <tr>
          <td><a href="{escape(a['url'])}" style="font-size:10px;color:#4b5563;font-weight:700;text-decoration:underline;font-family:'Segoe UI',Arial,sans-serif;">원문 보기 →</a></td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""
        else:
            headline_html = ""
```

**Step 2: 테스트 실행**

```bash
python -m pytest tests/test_newsletter_html.py::test_headline_rendered tests/test_newsletter_html.py::test_card_bgcolor -v
```

Expected: PASS

---

### Task 5: MORE STORIES 카드 재작성

**Files:**
- Modify: `content_generator/newsletter.py`

**Step 1: cards 생성 블록 교체**

기존 `if more_articles:` 블록 전체 교체:

```python
        if more_articles:
            cards = ""
            for i, a in enumerate(more_articles):
                bullets_text = "<br>".join(
                    f"• {escape(b)}" for b in a.get("bullets", [])[:2]
                )
                cards += f"""
{self._spacer(8)}
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td width="3" bgcolor="#d1d5db"></td>
    <td bgcolor="#f5f7fa" style="padding:14px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-bottom:6px;">
            <span style="background:#f3f4f6;color:#374151;font-size:8px;font-weight:700;padding:2px 8px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('category', ''))}</span>
            &nbsp;
            <span style="color:#9ca3af;font-size:9px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('label', ''))} · {escape(a.get('region', ''))}</span>
          </td>
        </tr>
        <tr>
          <td style="font-size:12px;font-weight:700;color:#111827;line-height:1.4;padding-bottom:6px;font-family:Georgia,'Times New Roman',serif;">{i + 1}. {escape(a['title'])}</td>
        </tr>
        <tr>
          <td style="color:#6b7280;font-size:10px;line-height:1.7;font-family:'Segoe UI',Arial,sans-serif;">{bullets_text}</td>
        </tr>
        <tr>
          <td style="padding-top:10px;"><a href="{escape(a['url'])}" style="font-size:10px;color:#4b5563;font-weight:700;text-decoration:underline;font-family:'Segoe UI',Arial,sans-serif;">원문 보기 →</a></td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""
            more_html = f"""
{self._section_label("MORE STORIES")}
{cards}"""
        else:
            more_html = ""
```

**Step 2: 테스트 실행**

```bash
python -m pytest tests/test_newsletter_html.py::test_more_stories_rendered -v
```

Expected: PASS

---

### Task 6: AI 팁 카드 재작성

**Files:**
- Modify: `content_generator/newsletter.py`

**Step 1: tip_html 블록 교체**

기존 `if tip.get("task"):` 블록 전체 교체:

```python
        if tip.get("task"):
            task_text = escape(tip["task"])

            tools_html = ""
            if tip.get("tools"):
                tags = "".join(
                    f'<span style="background:#e5e7eb;color:#374151;font-size:9px;font-weight:700;padding:3px 10px;font-family:\'Segoe UI\',Arial,sans-serif;">{escape(t)}</span>&nbsp;'
                    for t in tip["tools"]
                )
                tools_html = f'<tr><td style="padding-bottom:14px;">{tags}</td></tr>'

            steps_html = ""
            if tip.get("steps"):
                step_nums = ["①", "②", "③", "④", "⑤"]
                rows = ""
                for i, step in enumerate(tip["steps"][:5]):
                    num = step_nums[i]
                    rows += f"""
<tr>
  <td width="26" style="vertical-align:top;padding:3px 8px 3px 0;">
    <span style="background:#111827;color:#fff;font-size:11px;font-weight:700;padding:2px 5px;font-family:'Segoe UI',Arial,sans-serif;">{num}</span>
  </td>
  <td style="font-size:11px;color:#374151;line-height:1.6;padding:3px 0;font-family:'Segoe UI',Arial,sans-serif;">{escape(step)}</td>
</tr>"""
                steps_html = f"""
<tr>
  <td style="padding-bottom:14px;">
    <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:8px;font-family:'Segoe UI',Arial,sans-serif;">🪜 이렇게 따라하세요</div>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="border:1px solid #e5e7eb;padding:12px 14px;">
      {rows}
    </table>
  </td>
</tr>"""

            prompt_html = ""
            if tip.get("prompt"):
                prompt_html = f"""
<tr>
  <td>
    <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:6px;font-family:'Segoe UI',Arial,sans-serif;">📋 복붙 프롬프트 — 그대로 붙여넣고 [ ] 부분만 수정하세요</div>
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr>
        <td bgcolor="#111827" style="padding:14px 16px;font-family:'Courier New',Courier,monospace;font-size:11px;color:#e5e7eb;line-height:1.8;word-break:keep-all;white-space:pre-wrap;">{escape(tip['prompt'])}</td>
      </tr>
    </table>
  </td>
</tr>"""

            tip_html = f"""
{self._spacer(8)}
{self._section_label("💡 오늘 바로 써먹는 AI 팁")}
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:22px;">
  <tr>
    <td width="4" bgcolor="#6b7280"></td>
    <td bgcolor="#f5f7fa" style="padding:16px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-bottom:12px;">
            <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:4px;font-family:'Segoe UI',Arial,sans-serif;">✦ 오늘의 자동화 TASK</div>
            <div style="font-size:11px;color:#374151;line-height:1.8;font-family:'Segoe UI',Arial,sans-serif;">{task_text}</div>
          </td>
        </tr>
        {tools_html}
        {steps_html}
        {prompt_html}
      </table>
    </td>
  </tr>
</table>"""
        else:
            tip_html = ""
```

**Step 2: 테스트 실행**

```bash
python -m pytest tests/test_newsletter_html.py::test_tip_rendered -v
```

Expected: PASS

---

### Task 7: 외부 래퍼 + 헤더 + 푸터 재작성

**Files:**
- Modify: `content_generator/newsletter.py`

**Step 1: `return f"""..."""` 블록 전체 교체**

```python
        return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 뉴스 | {date}</title></head>
<body bgcolor="#f5f7fa" style="margin:0;padding:12px;font-family:'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f5f7fa">
  <tr>
    <td align="center" style="padding:12px;">

      <table width="680" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="max-width:680px;">

        <!-- 헤더 -->
        <tr>
          <td bgcolor="#111827" style="padding:24px 28px 18px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td>
                  <div style="font-size:9px;letter-spacing:3px;color:#9ca3af;font-weight:700;margin-bottom:8px;font-family:'Segoe UI',Arial,sans-serif;">DAILY DIGEST</div>
                  <span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#ffffff;font-family:Georgia,'Times New Roman',serif;">AI </span><span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#e5e7eb;font-family:Georgia,'Times New Roman',serif;">NEWS</span>
                </td>
                <td align="right" style="vertical-align:bottom;padding-bottom:4px;">
                  <div style="color:#6b7280;font-size:9px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">VOL. 01</div>
                  <div style="color:#9ca3af;font-size:9px;margin-top:2px;font-family:'Segoe UI',Arial,sans-serif;">{date}</div>
                </td>
              </tr>
              <tr>
                <td colspan="2" height="1" bgcolor="#1f2937" style="padding-top:14px;"></td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- 트렌드 배너 -->
        <tr><td>{trends_banner}</td></tr>

        <!-- 콘텐츠 영역 -->
        <tr>
          <td bgcolor="#ffffff" style="padding:22px 28px;">
            {headline_html}
            {more_html}
            {tip_html}
          </td>
        </tr>

        <!-- 푸터 -->
        <tr>
          <td bgcolor="#111827" style="padding:16px 28px;text-align:center;">
            <span style="font-size:16px;font-weight:900;color:#ffffff;font-family:Georgia,'Times New Roman',serif;">AI </span><span style="font-size:16px;font-weight:900;color:#e5e7eb;font-family:Georgia,'Times New Roman',serif;">NEWS</span>
            <div style="color:#4b5563;font-size:8px;letter-spacing:1px;margin-top:4px;font-family:'Segoe UI',Arial,sans-serif;">매일 오전 8시 · AI 뉴스 다이제스트</div>
          </td>
        </tr>

      </table>

    </td>
  </tr>
</table>

</body></html>"""
```

**Step 2: 전체 테스트 실행**

```bash
python -m pytest tests/test_newsletter_html.py -v
```

Expected: 모든 테스트 PASS

**Step 3: 커밋**

```bash
git add content_generator/newsletter.py tests/test_newsletter_html.py
git commit -m "feat: 뉴스레터 HTML 테이블 기반 아웃룩 호환 재설계"
```

---

### Task 8: 프리뷰 확인

**Step 1: 프리뷰 실행**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI"
python main.py --preview
```

Expected: 오류 없이 완료, `output/2026-04-15/` 폴더 생성

**Step 2: HTML 파일 직접 확인 (선택)**

`trends/trend_2026-04-15.txt` 또는 output 폴더 내 파일이 정상 생성됐는지 확인.

**Step 3: 최종 커밋 (변경사항 있을 경우)**

```bash
git add -A
git commit -m "chore: 프리뷰 확인 완료"
```
