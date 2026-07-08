# 팁 생성 개선 설계 | 2026-03-27

## 목표

`generate_tip()`이 매일 랜덤 카테고리를 선택하여, 기사와 독립적으로 구체적이고 실용적인 AI 팁을 생성하도록 개선한다.

## 문제

- 현재 팁이 당일 뉴스 기사에 지나치게 의존 → 기사가 규제/정책 위주이면 팁도 추상적이 됨
- 구체적인 시나리오(파일 정리, 계약서 검토 등)가 나오지 않음
- 프롬프트에 스타일 가이드가 없어 출력 톤이 일정하지 않음

## 설계

### 변경 파일

`summarizer/claude_summarizer.py` 한 파일만 수정.

### 카테고리 상수 추가

```python
TIP_CATEGORIES = [
    {"name": "파일·폴더 자동화",      "difficulty": "claude-code",   "example": "바탕화면 파일을 확장자별로 분류하는 Claude Code 스크립트"},
    {"name": "아침 브리핑·알림 봇",   "difficulty": "claude-code",   "example": "매일 아침 일정+날씨를 슬랙으로 보내는 자동화 봇"},
    {"name": "엑셀·CSV 자동 통합",    "difficulty": "claude-code",   "example": "팀원들한테 받은 엑셀 10개를 하나로 합치는 스크립트"},
    {"name": "계약서·문서 검토",      "difficulty": "prompt-only",   "example": "계약서 PDF에서 불리한 조항만 골라 요약"},
    {"name": "회의록·액션 아이템",    "difficulty": "prompt-only",   "example": "회의록을 담당자별 할 일 목록으로 정리"},
    {"name": "이메일·슬랙 템플릿",   "difficulty": "prompt-only",   "example": "매주 반복되는 보고 이메일을 템플릿화"},
    {"name": "콘텐츠·SNS 변환",      "difficulty": "prompt-only",   "example": "블로그 초안을 링크드인·스레드·인스타 포맷으로 변환"},
    {"name": "데이터 분석·인사이트", "difficulty": "prompt-only",   "example": "판매 CSV를 붙여넣어 상위 제품·이상치 분석"},
]
```

### 프롬프트 구조 변경

**기존:** 기사 목록을 주고 "영감을 얻어 워크플로우 제안"

**변경 후:**
```
오늘의 팁 카테고리: {category["name"]}
난이도: {category["difficulty"]}
참고 예시: {category["example"]}

위 카테고리에서 30-40대 직장인이 지금 바로 실행 가능한 AI 팁을 하나 제안해줘.
오늘 뉴스 (참고만): {articles_text}

스타일 규칙:
- task: "상황 묘사 → Claude/Claude Code가 해결 → 실용적 이점" 3문장, ~어요/에요 어체
- prompt: 경로·조건만 구체적으로, 짧고 직관적하게
- 전문 용어 불필요 (예: "Python인지 몰라도 돼요" 같은 안심 문구 가끔 사용)
- claude-code 카테고리면 tools에 반드시 "Claude Code" 포함
```

### 데이터 흐름

```
random.choice(TIP_CATEGORIES)
    ↓
category 주입 → Claude API (max_tokens=600)
    ↓
JSON {task, tools, prompt} 파싱
    ↓
뉴스레터 렌더링 (newsletter.py 변경 없음)
```

## 기대 출력 예시

**파일·폴더 자동화:**
```json
{
  "task": "바탕화면이 파일로 가득 찰 때 Claude Code에게 정리를 맡길 수 있어요. 확장자별로 폴더를 만들고 자동 이동하는 스크립트를 몇 초 만에 만들어줘요. Python인지 몰라도 돼요, Claude Code가 알아서 만들고 실행까지 해요.",
  "tools": ["Claude Code"],
  "prompt": "내 바탕화면 경로는 C:/Users/홍길동/Desktop이야. .pdf .docx .xlsx .jpg .png .zip 파일을 각 확장자명 폴더로 자동 분류하는 스크립트 만들어줘. 실행 전에 어떤 파일이 이동되는지 미리 출력해줘."
}
```

**계약서·문서 검토:**
```json
{
  "task": "계약서 PDF를 Claude에 던지면 불리한 조항만 골라서 요약해줘요. 변호사 검토 전 1차 필터로 쓰기 딱 좋아요. 놓치기 쉬운 위약금·자동갱신 조항도 잡아줘요.",
  "tools": ["Claude"],
  "prompt": "이 계약서에서 나한테 불리하거나 애매한 조항만 골라서 이유랑 같이 알려줘."
}
```

## 테스트 전략

- 기존 `test_generate_tip_*` 테스트는 mock 기반이라 그대로 통과
- 카테고리 상수 추가/프롬프트 변경만이므로 인터페이스 변경 없음
- 실제 품질 검증: `--preview` 실행 후 output HTML 육안 확인
