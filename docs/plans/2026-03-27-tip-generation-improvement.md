# Tip Generation Improvement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `generate_tip()`이 매일 랜덤 카테고리를 선택하여, 기사와 무관하게 구체적이고 스타일이 일관된 AI 팁을 생성하도록 개선한다.

**Architecture:** `claude_summarizer.py`에 `TIP_CATEGORIES` 상수를 추가하고, `generate_tip()` 프롬프트를 카테고리 주입 방식으로 교체한다. 뉴스레터 렌더링(newsletter.py)과 테스트 인터페이스는 변경 없음.

**Tech Stack:** Python 3.12, `random.choice`, Anthropic Python SDK, pytest + unittest.mock

---

### Task 1: TIP_CATEGORIES 상수 추가 및 카테고리 선택 로직

**Files:**
- Modify: `summarizer/claude_summarizer.py`
- Test: `tests/test_claude_summarizer.py`

**Step 1: 실패하는 테스트 작성**

`tests/test_claude_summarizer.py` 하단에 추가:

```python
def test_generate_tip_uses_category():
    """generate_tip이 TIP_CATEGORIES 중 하나의 카테고리명을 프롬프트에 포함하는지 확인."""
    from summarizer.claude_summarizer import TIP_CATEGORIES
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    captured_prompt = {}

    def capture_call(**kwargs):
        captured_prompt["content"] = kwargs["messages"][0]["content"]
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text='{"task": "t", "tools": ["Claude"], "prompt": "p"}')]
        return mock_msg

    summarizer._client = MagicMock()
    summarizer._client.messages.create.side_effect = capture_call

    articles = [{"title": "AI 뉴스", "bullets": ["내용"], "category": "모델 출시"}]
    summarizer.generate_tip(articles)

    category_names = [c["name"] for c in TIP_CATEGORIES]
    assert any(name in captured_prompt["content"] for name in category_names)
```

**Step 2: 테스트 실행 — 실패 확인**

```bash
pytest tests/test_claude_summarizer.py::test_generate_tip_uses_category -v
```
Expected: `FAILED` — `ImportError: cannot import name 'TIP_CATEGORIES'`

**Step 3: TIP_CATEGORIES 상수 추가**

`summarizer/claude_summarizer.py` 상단 import 블록 아래에 추가:

```python
TIP_CATEGORIES = [
    {
        "name": "파일·폴더 자동화",
        "difficulty": "claude-code",
        "example": "바탕화면 파일을 확장자별로 분류하는 Claude Code 스크립트",
    },
    {
        "name": "아침 브리핑·알림 봇",
        "difficulty": "claude-code",
        "example": "매일 아침 일정+날씨를 슬랙으로 보내는 자동화 봇",
    },
    {
        "name": "엑셀·CSV 자동 통합",
        "difficulty": "claude-code",
        "example": "팀원들한테 받은 엑셀 10개를 하나로 합치는 스크립트",
    },
    {
        "name": "반복 업무 스크립트화",
        "difficulty": "claude-code",
        "example": "매달 반복하는 파일 변환·정리 작업을 Claude Code로 한 번만 만들어두기",
    },
    {
        "name": "계약서·문서 검토",
        "difficulty": "prompt-only",
        "example": "계약서 PDF에서 불리한 조항만 골라 요약",
    },
    {
        "name": "회의록·액션 아이템",
        "difficulty": "prompt-only",
        "example": "회의록을 담당자별 할 일 목록으로 정리",
    },
    {
        "name": "이메일·슬랙 템플릿",
        "difficulty": "prompt-only",
        "example": "매주 반복되는 보고 이메일을 채워넣기만 하면 되는 템플릿으로 변환",
    },
    {
        "name": "콘텐츠·SNS 변환",
        "difficulty": "prompt-only",
        "example": "블로그 초안을 링크드인·스레드·인스타 포맷 3종으로 변환",
    },
    {
        "name": "데이터 분석·인사이트",
        "difficulty": "prompt-only",
        "example": "판매 CSV를 붙여넣어 상위 제품·이상치 자동 분석",
    },
    {
        "name": "리서치·비교 분석",
        "difficulty": "prompt-only",
        "example": "경쟁사 3곳을 기준 항목별로 비교표 자동 생성",
    },
]
```

**Step 4: 테스트 실행 — 통과 확인**

```bash
pytest tests/test_claude_summarizer.py::test_generate_tip_uses_category -v
```
Expected: `PASSED`

**Step 5: 커밋**

```bash
git add summarizer/claude_summarizer.py tests/test_claude_summarizer.py
git commit -m "feat: TIP_CATEGORIES 상수 추가 및 카테고리 선택 테스트"
```

---

### Task 2: generate_tip() 프롬프트 교체

**Files:**
- Modify: `summarizer/claude_summarizer.py:119-180`

**Step 1: 실패하는 테스트 작성**

`tests/test_claude_summarizer.py` 하단에 추가:

```python
def test_generate_tip_prompt_contains_style_rules():
    """프롬프트에 스타일 규칙 키워드가 포함되는지 확인."""
    summarizer = ClaudeSummarizer(api_key="test", model="test-model")
    captured_prompt = {}

    def capture_call(**kwargs):
        captured_prompt["content"] = kwargs["messages"][0]["content"]
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text='{"task": "t", "tools": ["Claude"], "prompt": "p"}')]
        return mock_msg

    summarizer._client = MagicMock()
    summarizer._client.messages.create.side_effect = capture_call

    articles = [{"title": "AI 뉴스", "bullets": ["내용"], "category": "모델 출시"}]
    summarizer.generate_tip(articles)

    assert "스타일" in captured_prompt["content"] or "어요/에요" in captured_prompt["content"]
    assert "claude-code" in captured_prompt["content"].lower() or "Claude Code" in captured_prompt["content"]
```

**Step 2: 테스트 실행 — 실패 확인**

```bash
pytest tests/test_claude_summarizer.py::test_generate_tip_prompt_contains_style_rules -v
```
Expected: `FAILED`

**Step 3: generate_tip() 프롬프트 교체**

`summarizer/claude_summarizer.py`의 `generate_tip()` 메서드에서:

1. 메서드 상단에 `import random` 추가 (파일 상단 import에 없을 경우)
2. `articles_text` 조립 직후, 기존 `prompt = f"""...` 블록 전체를 아래로 교체:

```python
import random
category = random.choice(TIP_CATEGORIES)

prompt = f"""오늘의 AI 팁 카테고리: {category["name"]}
난이도: {category["difficulty"]}
참고 예시: {category["example"]}

위 카테고리에서 30-40대 직장인이 지금 바로 실행 가능한 AI 활용법을 하나 제안해줘.
오늘 뉴스 (참고만, 얽매이지 말 것): {articles_text}

아래 JSON 형식으로만 반환해 (마크다운 코드블록 없이):
{{
  "task": "자동화 아이디어 설명 2-3문장 (~어요/에요 어체)",
  "tools": ["툴1", "툴2"],
  "prompt": "그 툴에 복붙할 수 있는 구체적 프롬프트 (한국어)"
}}

스타일 규칙:
- task: "상황 묘사 → Claude/Claude Code가 해결 → 실용적 이점" 3문장
- prompt: 경로·조건만 구체적으로, 짧고 직관적하게
- 전문 용어 설명 불필요 ("Python인지 몰라도 돼요" 같은 안심 문구 가끔 사용)
- difficulty가 claude-code이면 tools에 반드시 "Claude Code" 포함
- 마크다운 기호(#, **, *) 사용 금지

JSON:"""
```

**Step 4: 테스트 전체 실행**

```bash
pytest tests/test_claude_summarizer.py -v
```
Expected: 모든 테스트 `PASSED` (기존 테스트 포함)

**Step 5: 커밋**

```bash
git add summarizer/claude_summarizer.py tests/test_claude_summarizer.py
git commit -m "feat: generate_tip() 카테고리 기반 프롬프트로 교체"
```

---

### Task 3: import random 위치 정리

**Files:**
- Modify: `summarizer/claude_summarizer.py`

**Step 1: 현재 import 위치 확인**

파일 상단에 `import random`이 있는지 확인. Task 2에서 메서드 내부에 `import random`을 넣었다면 파일 상단으로 이동.

**Step 2: 이동**

`summarizer/claude_summarizer.py` 상단 import 블록에 `import random` 추가, 메서드 내부 `import random` 제거.

**Step 3: 테스트 실행**

```bash
pytest tests/test_claude_summarizer.py -v
```
Expected: 모든 테스트 `PASSED`

**Step 4: 커밋**

```bash
git add summarizer/claude_summarizer.py
git commit -m "refactor: import random을 파일 상단으로 이동"
```

---

### Task 4: 프리뷰 실행으로 실제 출력 검증

**Step 1: 프리뷰 실행**

```bash
python main.py --preview
```
Expected: `8/8` 완료, 오류 없음

**Step 2: 뉴스레터 HTML 확인**

생성된 뉴스레터 HTML에서 "💡 오늘 바로 써먹는 AI 팁" 섹션을 열어 확인:
- `task` 텍스트가 `~어요/에요` 어체인지
- `tools` 태그가 렌더링되는지
- `prompt` 박스가 구체적인 내용인지
- 마크다운 기호(`**`, `*`, `#`)가 남아있지 않은지

**Step 3: 문제 있으면**

- `task`에 마크다운 잔재 → 마크다운 제거 regex 확인 (`claude_summarizer.py:171-178`)
- 팁 섹션 전체 미노출 → JSON 파싱 실패 → `raw` 값 출력해서 확인
