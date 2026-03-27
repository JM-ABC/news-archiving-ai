# 헤드라인 중요도 점수 선정 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Claude가 기사 요약 시 중요도 점수(score 1-10)를 반환하도록 하고, 뉴스레터가 가장 높은 점수의 기사를 헤드라인으로 선정한다.

**Architecture:** `summarize()` 프롬프트에 `score` 필드를 추가해 Claude가 각 기사의 중요도를 채점하게 하고, `newsletter.py`에서 `max(valid, key=score)`로 헤드라인을 선정한다. TDD — 실패하는 테스트 먼저 작성 후 구현.

**Tech Stack:** Python 3.12, pytest, unittest.mock

**Spec:** `docs/superpowers/specs/2026-03-27-headline-score-design.md`

---

## 파일 구조

| 파일 | 변경 유형 | 내용 |
|---|---|---|
| `summarizer/claude_summarizer.py` | Modify (line 26-28) | `summarize()` 프롬프트에 `score` 필드 추가 |
| `content_generator/newsletter.py` | Modify (line 35-37) | `max()` 기반 헤드라인 선정 로직으로 교체 |
| `tests/test_claude_summarizer.py` | Modify (line 20, 26) | `fake_response`에 `score` 추가, `score` 검증 assert |
| `tests/test_newsletter.py` | Modify (SAMPLE + 추가) | SAMPLE articles에 `score` 추가, 테스트 2개 추가 |

---

## Task 1: ClaudeSummarizer — summarize() 프롬프트에 score 추가

**Files:**
- Modify: `summarizer/claude_summarizer.py:26-28` (프롬프트)
- Test: `tests/test_claude_summarizer.py:18-26`

### 1-1. 테스트 먼저 수정 (failing)

- [ ] **Step 1: `tests/test_claude_summarizer.py` — `test_summarize_returns_list` 수정**

`fake_response` (line 20) 에 `"score": 8` 추가 후 assert 2개 추가:

기존 (line 20):
```python
    fake_response = '[{"title":"GPT-5 출시","category":"모델 출시","bullets":["성능이 향상됐어요","멀티모달을 지원해요"],"implication":"AI 경쟁이 심화됐어요","url":"https://example.com/1"}]'
```

변경:
```python
    fake_response = '[{"title":"GPT-5 출시","category":"모델 출시","bullets":["성능이 향상됐어요","멀티모달을 지원해요"],"implication":"AI 경쟁이 심화됐어요","url":"https://example.com/1","score":8}]'
```

기존 assert 뒤에 추가 (line 27 이후):
```python
    assert isinstance(result[0]["score"], int)
    assert result[0]["score"] == 8
```

- [ ] **Step 2: 실패 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/test_claude_summarizer.py::test_summarize_returns_list -v 2>&1 | tail -15
```

Expected: FAILED — `KeyError: 'score'` (프롬프트가 아직 score를 요청하지 않으므로 mock 응답에 score가 없을 것이지만, mock 응답에 직접 추가했으므로 이 테스트는 통과할 것)

> **Note:** 이 테스트는 mock을 사용하므로 fake_response에 score를 추가하면 바로 통과됩니다. 실패 확인 단계는 `score` 없는 상태에서 먼저 실행해 원래 동작을 확인하는 용도예요.

실제 확인 방법: fake_response에 score를 추가하기 **전에** 아래 코드로 테스트 실행:
```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -c "
import json
fake = '[{\"title\":\"GPT-5\",\"category\":\"모델 출시\",\"bullets\":[],\"implication\":\"imp\",\"url\":\"https://x.com\"}]'
r = json.loads(fake)
print('score' in r[0])  # False 확인
"
```

Expected: `False` — score 필드 없음 확인

### 1-2. 구현

- [ ] **Step 3: `summarizer/claude_summarizer.py` — 프롬프트 수정 (line 28)**

기존 (line 26-28):
```python
- bullets: 핵심 내용 3개 (각 50자 이내 한국어, ~어요/에요 어체, 구체적 수치·기업명 포함)
- implication: 산업 시사점 1문장 (40자 이내, ~어요/에요 어체)
- url: 원문 URL (그대로)
```

변경 (url 줄 뒤에 score 추가):
```python
- bullets: 핵심 내용 3개 (각 50자 이내 한국어, ~어요/에요 어체, 구체적 수치·기업명 포함)
- implication: 산업 시사점 1문장 (40자 이내, ~어요/에요 어체)
- url: 원문 URL (그대로)
- score: 오늘 AI 업계 전반에서 이 기사의 중요도 정수 (1-10, 10이 가장 중요). 기준: 파급력·신뢰성·독자 관련성. 단순 루머·마이너 업데이트는 낮게 채점.
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/test_claude_summarizer.py -v 2>&1 | tail -20
```

Expected: 모든 테스트 PASSED

- [ ] **Step 5: 커밋**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && git add summarizer/claude_summarizer.py tests/test_claude_summarizer.py && git commit -m "feat: summarize() score 필드 추가 (중요도 1-10)"
```

---

## Task 2: newsletter.py — score 기반 헤드라인 선정

**Files:**
- Modify: `content_generator/newsletter.py:31-34`
- Test: `tests/test_newsletter.py`

### 2-1. 테스트 먼저 수정 (failing)

- [ ] **Step 1: `tests/test_newsletter.py` — SAMPLE articles에 `score` 추가**

SAMPLE의 articles 두 개에 `score` 필드 추가 (line 12-30):

```python
    "articles": [
        {
            "title": "GPT-5 출시",
            "category": "모델 출시",
            "bullets": ["성능이 대폭 향상됐어요", "멀티모달을 지원해요", "가격이 인하됐어요"],
            "implication": "AI 경쟁이 더욱 심화됐어요",
            "url": "https://example.com/1",
            "label": "TechCrunch",
            "region": "GL",
            "score": 7,
        },
        {
            "title": "EU AI법 시행",
            "category": "규제",
            "bullets": ["고위험 AI 등록이 의무화됐어요", "과징금이 3%로 설정됐어요"],
            "implication": "기업 부담이 증가했어요",
            "url": "https://example.com/2",
            "label": "ZDNet",
            "region": "KR",
            "score": 5,
        },
    ]
```

- [ ] **Step 2: `tests/test_newsletter.py` 끝에 테스트 2개 추가**

```python
def test_headline_is_highest_score():
    """가장 높은 score 기사가 헤드라인으로 선정되어야 함."""
    articles = [
        {
            "title": "낮은점수기사",
            "category": "규제",
            "bullets": ["b1"],
            "implication": "imp",
            "url": "https://example.com/low",
            "label": "A",
            "region": "KR",
            "score": 3,
        },
        {
            "title": "높은점수기사",
            "category": "모델 출시",
            "bullets": ["b2"],
            "implication": "imp",
            "url": "https://example.com/high",
            "label": "B",
            "region": "GL",
            "score": 9,
        },
    ]
    data = {**SAMPLE, "articles": articles}
    html = NewsletterGenerator().generate(data)
    headline_pos = html.index("높은점수기사")
    more_pos = html.index("낮은점수기사")
    assert headline_pos < more_pos  # 헤드라인이 MORE STORIES보다 먼저 등장


def test_headline_not_in_more_stories():
    """헤드라인 기사가 MORE STORIES에 중복 노출되지 않아야 함."""
    articles = [
        {
            "title": "최고기사",
            "category": "모델 출시",
            "bullets": ["b"],
            "implication": "imp",
            "url": "https://example.com/best",
            "label": "X",
            "region": "GL",
            "score": 10,
        },
        {
            "title": "보통기사",
            "category": "규제",
            "bullets": ["b"],
            "implication": "imp",
            "url": "https://example.com/ok",
            "label": "Y",
            "region": "KR",
            "score": 5,
        },
    ]
    data = {**SAMPLE, "articles": articles}
    html = NewsletterGenerator().generate(data)
    assert html.count("최고기사") == 1  # 헤드라인에만 1번 등장
```

- [ ] **Step 3: 실패 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/test_newsletter.py::test_headline_is_highest_score tests/test_newsletter.py::test_headline_not_in_more_stories -v 2>&1 | tail -15
```

Expected: FAILED — 현재 `valid[0]` 로직은 score를 무시하므로 "낮은점수기사"(첫 번째)가 헤드라인이 되어 `headline_pos > more_pos`

### 2-2. 구현

- [ ] **Step 4: `content_generator/newsletter.py` — 헤드라인 선정 로직 교체 (line 35-37)**

기존:
```python
        valid = [a for a in articles if a.get("category") != "기타"]
        headline_article = valid[0] if valid else None
        more_articles = valid[1:6] if len(valid) > 1 else []
```

변경:
```python
        valid = [a for a in articles if a.get("category") != "기타"]
        headline_article = max(valid, key=lambda a: a.get("score", 0)) if valid else None
        more_articles = [a for a in valid if a is not headline_article][:5]
```

- [ ] **Step 5: 전체 테스트 통과 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/ -v 2>&1 | tail -30
```

Expected: 58개 테스트 모두 PASSED (기존 56개 + 새 2개)

- [ ] **Step 6: 커밋**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && git add content_generator/newsletter.py tests/test_newsletter.py && git commit -m "feat: 헤드라인 score 기반 선정 (max score 기사가 HEADLINE)"
```

---

## Task 3: GitHub Push

- [ ] **Step 1: 전체 테스트 최종 확인**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: `58 passed, 1 warning`

- [ ] **Step 2: GitHub push**

```bash
cd "c:\Users\USER\Desktop\뉴스아카이빙_AI" && git push origin main
```
