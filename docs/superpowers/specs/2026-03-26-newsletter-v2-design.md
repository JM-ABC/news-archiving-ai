# 뉴스레터 v2 디자인 스펙

## 목표

`content_generator/newsletter.py`의 `generate()` 메서드를 모노크롬 + Georgia 혼합 폰트 스타일로 교체하고, AI 팁 섹션을 구조화된 자동화 가이드 형태로 고도화한다. 시그니처와 반환 타입은 기존과 동일하게 유지한다.

---

## 디자인 방향

- **컬러**: 전체 모노크롬 — 에메랄드 그린(`#10b981`) 계열 전부 제거, 회색/흰색 계열로 교체
- **폰트**: 혼합 — `AI NEWS` 타이틀·기사 헤드라인은 `Georgia,'Times New Roman',serif`, 나머지는 `'Segoe UI',Arial,sans-serif`
- **모바일**: 패딩 조정, `flex-wrap`, `word-break:keep-all` 적용
- **말투**: bullets·implication·팁 생성 프롬프트 모두 `~어요/에요` 블로그 어체 사용

---

## 컬러 맵

| 요소 | 기존 | 변경 후 |
|---|---|---|
| "NEWS" 타이틀 색 | `#10b981` | `#e5e7eb` |
| "DAILY DIGEST" 라벨 | `#6ee7b7` | `#9ca3af` |
| 헤더 하단 구분선 | `linear-gradient(#10b981,#059669,transparent)` 2px | `rgba(255,255,255,0.12)` 1px |
| 트렌드 배너 배경 | `#10b981` | `#374151` |
| HEADLINE 카드 좌측 보더 | `#10b981` | `#4b5563` |
| HEADLINE 카테고리 태그 텍스트 | `#10b981` | `#d1d5db` |
| 원문 보기 링크 | `#10b981` (no underline) | `#4b5563` + `text-decoration:underline` |
| AI 팁 배경 | `#fffbeb` | `#f9fafb` |
| AI 팁 좌측 보더 | `#f59e0b` | `#6b7280` |
| MORE STORIES 카드 배경 | 없음 | `#f8fafc` |
| MORE STORIES 카드 좌측 보더 | 없음 | `3px solid #d1d5db` |

---

## 데이터 필드 참조

### 기사 딕셔너리 필드 (기존과 동일)

| 필드 | 출처 | 비고 |
|---|---|---|
| `title` | ClaudeSummarizer | 한국어 제목 |
| `category` | ClaudeSummarizer | 기타 필터링에 사용 |
| `bullets` | ClaudeSummarizer | 리스트, 최대 3개, ~어요/에요 어체 |
| `implication` | ClaudeSummarizer | 시사점 문자열, ~어요/에요 어체 |
| `url` | ClaudeSummarizer | 원문 URL |
| `label` | main.py setdefault | 출처명, 없으면 `''` 폴백 |
| `region` | main.py setdefault | KR 또는 GL, 없으면 `''` 폴백 |

### `data` 최상위 필드

| 필드 | 타입 | 출처 | 비고 |
|---|---|---|---|
| `date` | `str` | main.py | YYYY-MM-DD |
| `trends` | `str` | ClaudeSummarizer.generate_trends() | 빈 문자열이면 배너 생략 |
| `articles` | `list[dict]` | ClaudeSummarizer.summarize() | 요약된 기사 목록 |
| `tip` | `dict` | ClaudeSummarizer.generate_tip() | `{"task":str, "tools":list, "prompt":str}`. 빈 dict `{}` 또는 None이면 섹션 생략 |
| ~~`email_from`~~ | ~~`str`~~ | ~~main.py~~ | **v2에서 제거** (투표 기능 삭제) |

---

## 섹션별 변경 상세

### 1. 헤더

- `AI NEWS` 타이틀: `font-family:Georgia,'Times New Roman',serif`
- `flex-wrap:wrap` 적용 — 모바일에서 날짜가 아래로 내려가도 레이아웃 유지
- `padding:24px 28px 18px` (기존 `28px 32px 20px`에서 소폭 축소로 모바일 여백 확보)

### 2. 트렌드 배너

- 레이블과 트렌드 텍스트를 두 줄로 분리:

```html
<div>
  🔑 TODAY'S TRENDS<br>
  <span style="font-weight:400;...">LLM 에이전트화 · 규제 강화 · 멀티모달</span>
</div>
```

- `word-break:keep-all` 적용으로 한국어 단어 단위 줄바꿈

### 3. HEADLINE 섹션

- 기사 제목: `font-family:Georgia,'Times New Roman',serif`
- 카드 좌측 보더: `4px solid #4b5563`
- 카테고리 태그: 배경 `#111827`, 텍스트 `#d1d5db`
- 원문 보기: `color:#4b5563; text-decoration:underline`
- `label`/`region` 없는 경우: `a.get('label', '')` 패턴으로 빈 문자열 폴백

### 4. 💡 AI 자동화 팁 섹션

**구조 변경**: 단순 텍스트 → 3파트 구조화 카드

```
✦ 오늘의 자동화 TASK
  [창의적 업무 자동화 아이디어 2-3문장. 오늘 기사에서 영감을 얻되, 기사에 얽매이지 않음]

🛠 추천 툴
  [툴 태그 목록]

📋 복붙 프롬프트
  [코드 블록 스타일, 그대로 복붙 가능한 구체적 프롬프트]
```

**`generate_tip()` 반환값 변경**: `str` → `dict`

```python
{
  "task": "2-3문장 자동화 아이디어 설명",    # ~어요/에요 어체
  "tools": ["Claude", "ChatGPT"],           # 1~3개 리스트
  "prompt": "복붙 가능한 구체적 프롬프트"
}
```

**빈 케이스 반환**: 기사 목록이 비거나 `category != '기타'` 기사가 없으면 빈 dict `{}` 반환.

**`newsletter.py` 섹션 렌더링 조건**:

```python
tip = data.get("tip") or {}
if tip.get("task"):
    # 섹션 렌더링
```

**JSON 파싱 오류 처리**: `generate_tip()`에서 JSON 파싱 실패 시 `{}` 반환. `summarize()`와 동일한 코드블록 제거 로직 적용 후 재시도.

```python
try:
    return json.loads(raw)
except json.JSONDecodeError:
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
```

**마크다운 후처리**: JSON 파싱 후 `task`와 `prompt` 값에 기존 마크다운 기호 후처리 적용 (bold, italic, header 제거).

**스타일**:
- 툴 태그: `background:#e5e7eb; color:#374151; border-radius:12px; padding:3px 10px; font-size:9px; font-weight:700`
- 프롬프트 박스: `background:#111827; color:#e5e7eb; font-family:'Courier New',Courier,monospace; font-size:10px; padding:12px 14px; border-radius:4px; line-height:1.7; word-break:keep-all`

### 5. MORE STORIES 섹션

- **최대 5개**: `valid[1:6]` (기존 전체 표시에서 최대 5개로 제한)
- **카드 스타일**: `background:#f8fafc; border-left:3px solid #d1d5db; border-radius:4px; padding:14px; margin-bottom:12px`
- 기사 제목: `font-family:Georgia,'Times New Roman',serif`
- **원문 보기 추가**: `url` 링크 표시 (`color:#4b5563; text-decoration:underline`)
- **투표 링크 제거**: `mailto:` 링크 완전 삭제
- `label`/`region` 없는 경우: `a.get('label', '')` 패턴으로 빈 문자열 폴백

---

## `generate_tip()` 프롬프트 변경

```
다음 AI 뉴스 기사들을 참고해서, 30-40대 직장인이 Claude·ChatGPT·Claude Code·Zapier·n8n 등 AI 도구로 지금 바로 자동화할 수 있는 창의적인 업무 워크플로우를 하나 제안해줘.

오늘 기사에서 영감을 얻되, 기사 내용에 얽매이지 말고 자유롭게 아이디어를 내도 돼.

아래 JSON 형식으로만 반환해 (마크다운 코드블록 없이):
{
  "task": "자동화 아이디어 설명 2-3문장 (~어요/에요 어체)",
  "tools": ["툴1", "툴2"],
  "prompt": "그 툴에 복붙할 수 있는 구체적 프롬프트 (한국어)"
}

조건:
- task는 2-3문장, ~어요/에요 어체 사용
- tools는 1-3개 배열
- prompt는 실제로 Claude나 ChatGPT에 그대로 입력 가능한 구체적 문장
- 마크다운 기호(#, **, *) 사용 금지
```

---

## `summarize()` 프롬프트 변경

`bullets`와 `implication` 생성 시 `~어요/에요` 어체 사용:

```
- bullets: 핵심 내용 3개 (각 50자 이내 한국어, ~어요/에요 어체, 구체적 수치·기업명 포함)
- implication: 산업 시사점 1문장 (40자 이내, ~어요/에요 어체)
```

---

## `main.py` 변경

- `data["email_from"]` 주입 제거 (투표 기능 삭제)
- `data["tip"]`은 `generate_tip()`이 반환하는 dict 그대로 저장

---

## 구현 범위

| 파일 | 변경 내용 |
|---|---|
| `content_generator/newsletter.py` | `generate()` 전체 교체, `email_from` 변수 및 투표 관련 로직 제거 |
| `summarizer/claude_summarizer.py` | `generate_tip()` 반환값 dict로 변경 + 프롬프트 교체 + JSON 파싱 오류 처리, `summarize()` 프롬프트 어체 수정 |
| `main.py` | `email_from` 주입 제거 |
| `tests/test_newsletter.py` | 전체 교체 (새 디자인 기준) |
| `tests/test_claude_summarizer.py` | `generate_tip()` 반환 dict 검증으로 교체 |

- `generate_txt()`: 변경 없음
- 보안: 모든 동적 데이터 `escape()` 유지
- 다크 모드·Outlook 별도 대응 없음

---

## 엣지 케이스

| 상황 | 처리 |
|---|---|
| `data["tip"]`이 빈 dict `{}` 또는 None | AI 팁 섹션 전체 생략 (`tip.get("task")` 로 판별) |
| `tip["tools"]`가 빈 리스트 | 툴 행 생략 |
| `tip["prompt"]`가 빈 문자열 | 프롬프트 박스 생략 |
| `generate_tip()` JSON 파싱 실패 | `{}` 반환 → 팁 섹션 생략 |
| 모든 기사가 "기타" | HEADLINE + MORE STORIES 모두 생략, 헤더+배너+푸터만 렌더링 |
| MORE STORIES 기사가 5개 미만 | 있는 만큼만 표시 |
| `data["trends"]`가 빈 문자열 | 트렌드 배너 전체 생략 |
| `bullets`가 3개 미만 | 있는 만큼만 표시 |
| `label` 또는 `region` 없음 | `a.get('label', '')` 패턴으로 빈 문자열 폴백 |
