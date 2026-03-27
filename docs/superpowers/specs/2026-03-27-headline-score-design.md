# 헤드라인 선정 기준 개선 — 중요도 점수 기반

## 목표

Claude가 각 기사를 요약할 때 중요도 점수(`score`, 1-10)를 함께 반환하도록 하고, 뉴스레터에서 가장 높은 점수의 기사를 헤드라인으로 선정한다.

---

## 배경

기존 헤드라인 선정은 `"기타"` 카테고리 제외 후 단순히 목록의 첫 번째 기사를 사용했다. 기사 순서는 RSS 피드 수집 순서에 의존하므로, 가장 중요한 기사가 헤드라인이 되지 않을 수 있다.

---

## 설계

### 변경 파일

| 파일 | 변경 내용 |
|---|---|
| `summarizer/claude_summarizer.py` | `summarize()` 프롬프트에 `score` 필드 추가 |
| `content_generator/newsletter.py` | `max(valid, key=score)` 로 헤드라인 선정, MORE STORIES 재구성 |
| `tests/test_claude_summarizer.py` | `test_summarize_returns_list`의 fake JSON에 `score` 추가, 반환값에 `score` 포함 검증 |
| `tests/test_newsletter.py` | 최고 점수 기사가 헤드라인 되는지, 헤드라인이 MORE STORIES에 미포함인지 검증 |

### `summarize()` 프롬프트 변경

기존 JSON 필드에 `score` 추가:

```
- score: 오늘 AI 업계 전반에서 이 기사의 중요도 정수 (1-10, 10이 가장 중요)
  기준: 파급력·신뢰성·독자 관련성. 단순 루머·마이너 업데이트는 낮게 채점.
```

반환 JSON 형식:
```json
{
  "title": "한국어 제목",
  "category": "카테고리",
  "bullets": ["...", "...", "..."],
  "implication": "시사점",
  "url": "원문 URL",
  "score": 8
}
```

### `newsletter.py` 헤드라인 선정 로직

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

---

## 엣지 케이스

| 상황 | 처리 |
|---|---|
| `score` 필드 없는 기사 | `a.get("score", 0)` 폴백 — 기존 순서 기반 동작과 유사 |
| 동점 기사 | Python `max()` 기본 동작 — 먼저 등장한 기사 선정 |
| `valid` 비어있음 | 헤드라인 없음 (기존과 동일) |
| JSON 파싱 실패로 score 누락 | 0으로 폴백, 발행 중단 없음 |

---

## 테스트 명세

### `tests/test_claude_summarizer.py`

`test_summarize_returns_list`의 `fake_response`에 `"score": 8` 추가 후 아래 검증:

```python
assert isinstance(result[0]["score"], int)
assert result[0]["score"] == 8
```

### `tests/test_newsletter.py`

SAMPLE에 `score` 필드 추가 (기사별로 다른 값) 후 아래 테스트 추가:

```python
def test_headline_is_highest_score():
    """가장 높은 score 기사가 헤드라인으로 선정되어야 함."""
    articles = [
        {"title": "낮은점수기사", "category": "규제", "bullets": ["b1"],
         "implication": "imp", "url": "https://example.com/low",
         "label": "A", "region": "KR", "score": 3},
        {"title": "높은점수기사", "category": "모델 출시", "bullets": ["b2"],
         "implication": "imp", "url": "https://example.com/high",
         "label": "B", "region": "GL", "score": 9},
    ]
    data = {**SAMPLE, "articles": articles}
    html = NewsletterGenerator().generate(data)
    # 높은점수기사가 HEADLINE에, 낮은점수기사가 MORE STORIES에 있어야 함
    headline_pos = html.index("높은점수기사")
    more_pos = html.index("낮은점수기사")
    assert headline_pos < more_pos  # 헤드라인이 먼저 등장

def test_headline_not_in_more_stories():
    """헤드라인 기사가 MORE STORIES에 중복 노출되지 않아야 함."""
    articles = [
        {"title": "최고기사", "category": "모델 출시", "bullets": ["b"],
         "implication": "imp", "url": "https://example.com/best",
         "label": "X", "region": "GL", "score": 10},
        {"title": "보통기사", "category": "규제", "bullets": ["b"],
         "implication": "imp", "url": "https://example.com/ok",
         "label": "Y", "region": "KR", "score": 5},
    ]
    data = {**SAMPLE, "articles": articles}
    html = NewsletterGenerator().generate(data)
    assert html.count("최고기사") == 1  # 헤드라인에만 1번 등장
```

기존 `test_more_stories_max_5_articles`는 `score` 없는 기사를 사용하므로 변경 없이 통과 (모두 0점 → `max()` 첫 번째 반환, 기존 동작 유지).

---

## 구현 범위

- `generate_txt()`: 변경 없음
- 기사 수집·정렬 파이프라인(`main.py`, `prioritize()`): 변경 없음
- 보안: 기존 `escape()` 그대로 유지
- MORE STORIES 최대 5개 제한 유지
