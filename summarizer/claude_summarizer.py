import re
import anthropic
import json
import random
from typing import List, Dict

TIP_CATEGORIES = [
    # 파일·데이터 처리
    {
        "name": "CSV·엑셀 데이터 분석 자동화",
        "difficulty": "claude-code",
        "example": "판매 데이터 CSV를 Claude Code에 넣으면 베스트셀러·이상치·매출 추이를 자동 분석하고 차트 이미지와 요약 리포트를 파일로 저장",
    },
    {
        "name": "여러 문서에서 정보 자동 추출·통합",
        "difficulty": "claude-code",
        "example": "계약서·이메일·보고서 수십 개 파일을 폴더에 넣으면 Claude Code가 핵심 정보(날짜·금액·담당자)를 읽어서 엑셀 한 장으로 자동 통합",
    },
    {
        "name": "파일 일괄 처리·정리 자동화",
        "difficulty": "claude-code",
        "example": "수백 개 파일을 날짜·분류·키워드 기준으로 자동 정리하거나 파일명 일괄 변경하는 스크립트를 Claude Code가 즉시 작성하고 실행까지",
    },
    # 웹 수집
    {
        "name": "웹 정보 자동 수집·요약",
        "difficulty": "claude-code",
        "example": "업계 뉴스·공고 사이트 URL 목록을 주면 Claude Code가 최신 정보를 크롤링해서 주요 내용만 정리한 요약 파일을 생성",
    },
    {
        "name": "경쟁사 정보 모니터링 자동화",
        "difficulty": "claude-code",
        "example": "경쟁사 웹사이트 URL을 넣으면 가격·프로모션·신제품 정보를 수집해서 이전 버전과 비교한 변경 내역 보고서를 자동 생성",
    },
    # 보고서·문서 자동화
    {
        "name": "회의록 자동 정리",
        "difficulty": "claude-code",
        "example": "회의 메모나 녹취 텍스트를 파일로 주면 Claude Code가 안건별 요약·결정사항·담당자별 액션아이템을 정리한 회의록 파일을 자동 생성",
    },
    {
        "name": "정기 보고서 자동 생성",
        "difficulty": "claude-code",
        "example": "매출·비용·KPI 데이터 파일을 넣으면 Claude Code가 전월 대비 분석·차트·경영진 요약이 포함된 HTML 보고서를 자동으로 생성",
    },
    {
        "name": "긴 문서 핵심 요약",
        "difficulty": "prompt-only",
        "example": "계약서·제안서·논문 등 긴 문서를 Claude Code에 드래그앤드롭하면 핵심 조항·위험 요소·결론을 3분 안에 읽을 수 있는 요약본으로 변환",
    },
    # Git·버전관리
    {
        "name": "커밋 메시지·CHANGELOG 자동화",
        "difficulty": "claude-code",
        "example": "코드 변경 후 Claude Code에 '변경사항 보고 커밋 메시지 작성해줘'라고 하면 컨벤션에 맞는 메시지와 CHANGELOG.md를 자동으로 작성하고 커밋까지",
    },
    {
        "name": "GitHub PR 리뷰 자동화",
        "difficulty": "claude-code",
        "example": "변경된 파일을 주면 Claude Code가 버그·보안 취약점·개선사항을 분석하고 GitHub PR에 올릴 리뷰 코멘트 초안을 자동 작성",
    },
    # 자동화 스크립트
    {
        "name": "반복 업무 자동화 스크립트",
        "difficulty": "claude-code",
        "example": "매일 반복되는 파일 정리·데이터 수집·보고서 발송 업무를 설명하면 Claude Code가 파이썬 스크립트를 작성하고 바로 실행까지 완료",
    },
    {
        "name": "외부 서비스 API 연동 자동화",
        "difficulty": "claude-code",
        "example": "Slack·Notion·Google Sheets API 키를 주면 서비스 간 데이터를 자동으로 연동하는 스크립트를 Claude Code가 작성하고 실제 동작을 확인",
    },
    # MCP·외부 도구
    {
        "name": "Notion·Slack MCP 연동",
        "difficulty": "prompt-only",
        "example": "Claude Code에 MCP로 Notion과 Slack을 연결하면 'Notion 프로젝트 DB에서 오늘 마감 항목 뽑아서 Slack 채널에 요약 발송해줘'가 한 문장으로 실행",
    },
    {
        "name": "Google Drive·Sheets 자동 처리",
        "difficulty": "claude-code",
        "example": "Google Sheets URL을 주면 Claude Code가 데이터를 읽어서 분석·정리 후 결과를 새 시트에 자동으로 입력하는 스크립트를 작성하고 실행",
    },
    # CLAUDE.md·설정
    {
        "name": "CLAUDE.md로 팀 작업 규칙 설정",
        "difficulty": "prompt-only",
        "example": "프로젝트 폴더에 CLAUDE.md를 만들어 '항상 한국어로 응답', '이 파일은 수정 금지' 같은 규칙을 설정하면 이후 매번 설명 없이 자동 적용",
    },
    # 멀티 에이전트
    {
        "name": "여러 파일 병렬 동시 분석",
        "difficulty": "claude-code",
        "example": "10개 부서 월간 보고서 파일을 주면 Claude Code가 서브에이전트로 동시에 분석해서 부서별 요약과 전사 종합 리포트를 한번에 생성",
    },
    # GitHub Actions
    {
        "name": "GitHub Actions 자동화 설정",
        "difficulty": "claude-code",
        "example": "코드를 GitHub에 올릴 때마다 자동으로 테스트·배포·알림이 실행되도록 Claude Code가 .github/workflows 파일을 작성하고 설정까지 완료",
    },
    # Claude API
    {
        "name": "사내 업무에 Claude AI 붙이기",
        "difficulty": "claude-code",
        "example": "Anthropic SDK를 Claude Code로 작성하면 회사 챗봇·자동 분류·문서 요약 등 사내 업무에 AI 기능을 추가하는 코드를 빠르게 완성",
    },
]


class ClaudeSummarizer:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def summarize(self, articles: List[Dict]) -> List[Dict]:
        """기사 목록을 받아 요약 + 카테고리 분류 반환."""
        if not articles:
            return []

        articles_text = "\n".join(
            f"- [{i+1}] {a['title']}\n  출처: {a['label']} ({a['region']})\n  내용: {a['summary'][:300]}\n  URL: {a['url']}"
            for i, a in enumerate(articles)
        )

        prompt = f"""다음 AI 관련 뉴스 기사들을 분석하여 JSON 배열로 반환하세요.

각 기사에 대해:
- title: 한국어 제목 (원문이 영어면 번역, 기술 용어는 쉬운 말로 풀어쓰기)
- category: 소카테고리 (신제품·서비스/생활·직장 AI/규제·사회/기업·산업/연구·기술/기타 중 하나)
- bullets: 핵심 내용 3개 (각 50자 이내 한국어, ~어요/에요 어체, 일반인이 "나한테 어떤 의미인지" 관점으로 작성, 전문 용어 사용 최소화)
- implication: 일반 독자 시사점 1문장 (40자 이내, ~어요/에요 어체, "직장인·소비자·시민으로서 알아두면 좋은 점" 관점)
- url: 원문 URL (그대로)
- score: 일반 독자(비개발자 직장인·소비자) 관점 기사 중요도 정수 (1-10, 10이 가장 중요). 기준: ① 내 일상·직업에 직접 영향, ② 쉽게 이해 가능, ③ 당장 알아두면 유용. 연구자·개발자만 관심 가질 기술 세부사항은 낮게 채점.

기사 목록:
{articles_text}

JSON 배열만 반환 (마크다운 코드블록 없이):"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()

        # JSON 파싱 - 코드블록 제거 후 재시도
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)

    def propose_topics(self, articles: List[Dict]) -> List[str]:
        """오늘 기사에서 SNS에 올릴 만한 주제 각도 5-6개 제안."""
        if not articles:
            return []

        articles_text = "\n".join(
            f"- {a['title']}: {' / '.join(a.get('bullets', [])[:2])} (시사점: {a.get('implication', '')})"
            for a in articles
            if a.get("category") != "기타"
        )

        prompt = f"""다음 AI 뉴스 기사들을 보고 SNS 포스팅에 적합한 주제 각도 5-6개를 제안하세요.

기사 목록:
{articles_text}

각 주제는 아래 형식으로 작성하세요:
[번호]. [한 줄 제목] — [이 각도가 흥미로운 이유 1-2문장]

조건:
- 각 주제는 서로 다른 기사나 관점을 다룰 것
- 독자의 호기심을 자극하거나 논쟁을 유발할 수 있는 각도 선택
- 단순 뉴스 나열 금지 — 하나의 관점이나 스토리라인이 있어야 함
- 마크다운 기호(#, **, *) 사용 금지

주제 제안:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        # 번호로 시작하는 줄만 파싱, em dash 등 cp949 불가 문자 제거
        lines = [l.strip() for l in raw.splitlines() if re.match(r"^\d+\.", l.strip())]
        result = lines if lines else raw.splitlines()
        return [l.replace("\u2014", "-").replace("\u2013", "-").replace("\u2022", "-") for l in result]

    def generate_trends(self, articles: List[Dict]) -> str:
        """전체 기사에서 핵심 트렌드 3가지 도출."""
        if not articles:
            return ""

        titles = "\n".join(f"- {a['title']}" for a in articles)

        prompt = f"""다음 AI 뉴스 기사 제목들을 보고 오늘의 핵심 트렌드 3가지를 한국어로 도출하세요.
각 트렌드는 "• " 로 시작하는 단문 1-2문장으로 작성하세요.
문장은 반드시 ~어요/에요 어체로 끝내세요. (예: "~높아지고 있어요.", "~주목받고 있어요.")
기업명·수치·모델명 등 구체적인 정보를 문장 안에 자연스럽게 녹여 쓰세요. 단, 문장은 짧고 간결하게 유지하세요.
#, **, *, _ 같은 마크다운 기호는 절대 사용하지 마세요. 순수 텍스트만 작성하세요.

기사 목록:
{titles}

핵심 트렌드 3가지:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        # 마크다운 기호 후처리 제거
        raw = re.sub(r'\*\*(.+?)\*\*', r'\1', raw)   # **볼드** → 볼드
        raw = re.sub(r'\*(.+?)\*', r'\1', raw)        # *이탤릭* → 이탤릭
        raw = re.sub(r'^#{1,6}\s*', '', raw, flags=re.MULTILINE)  # # 제목 제거
        raw = re.sub(r'_(.+?)_', r'\1', raw)          # _밑줄_ → 밑줄
        return raw

    def generate_tip(self, articles: List[Dict], exclude_names: list = None) -> dict:
        """창의적인 AI 자동화 팁 생성. task/tools/steps/prompt/category_name dict 반환.

        exclude_names: 직전 발송에서 사용한 카테고리명 목록. 연속 반복 방지.
        """
        if not articles:
            return {}

        articles_text = "\n".join(
            f"- {a['title']}: {' / '.join(a.get('bullets', [])[:2])}"
            for a in articles
            if a.get("category") != "기타"
        )
        if not articles_text:
            return {}

        pool = TIP_CATEGORIES
        if exclude_names:
            filtered = [c for c in TIP_CATEGORIES if c["name"] not in exclude_names]
            if filtered:  # 필터 후 남은 게 있을 때만 적용
                pool = filtered

        selected_category = random.choice(pool)

        difficulty_guide = (
            "Claude Code 데스크탑 앱에서 실행하는 흐름으로 작성. 앱 열기 → 폴더 열기 또는 파일 드래그 → 프롬프트 입력 → 결과 확인 순서."
            if selected_category["difficulty"] == "claude-code"
            else "Claude.ai 웹사이트 또는 Claude 앱에서 프롬프트만 붙여넣어 실행하는 흐름으로 작성."
        )

        prompt = f"""오늘의 Claude Code 활용 팁 카테고리: {selected_category["name"]}
실행 방식: {selected_category["difficulty"]} — {difficulty_guide}
참고 예시: {selected_category["example"]}

위 카테고리에서 30-40대 직장인이 Claude Code로 지금 바로 실행 가능한 구체적인 활용법을 하나 제안해줘.
오늘 뉴스 (참고만, 얽매이지 말 것): {articles_text}

아래 JSON 형식으로만 반환해 (마크다운 코드블록 없이):
{{
  "task": "어떤 상황에서 Claude Code가 무엇을 해결해주는지 2-3문장 (~어요/에요 어체)",
  "tools": ["툴1", "툴2"],
  "steps": [
    "1단계: Claude Code 앱에서 구체적으로 무엇을 하는지",
    "2단계",
    "3단계",
    "4단계: 결과 확인 또는 파일 저장"
  ],
  "prompt": "Claude Code 입력창에 그대로 붙여넣을 수 있는 프롬프트 (한국어, 독자가 바꿀 부분은 [대괄호]로 표시)"
}}

스타일 규칙:
- task: "이런 상황 있죠? → Claude Code에 이렇게 하면 → 이런 결과가 나와요" 흐름, ~어요/에요 어체
- steps: 코딩 모르는 직장인이 그대로 따라할 수 있게. 각 단계 35자 이내. "Claude Code 앱을 열고" 같이 앱 조작 기준으로 서술.
- prompt: [파일 경로], [회사명], [조건] 형식으로 독자가 바꿀 부분 명확히 표시. 실제로 동작하는 구체적 지시문.
- 안심 문구 가끔 사용 ("코딩 몰라도 괜찮아요", "Python 설치 안 해도 돼요" 등)
- difficulty가 claude-code이면 tools 첫 번째에 반드시 "Claude Code" 포함
- 마크다운 기호(#, **, *) 사용 금지

JSON:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=1200,
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
                print(f"[WARN] generate_tip JSON 파싱 실패. 원문:\n{raw[:300]}")
                return {}

        def _strip_md(text: str) -> str:
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'_(.+?)_', r'\1', text)
            return text

        for field in ("task", "prompt"):
            if field in result and isinstance(result[field], str):
                result[field] = _strip_md(result[field])

        if "steps" in result and isinstance(result["steps"], list):
            result["steps"] = [_strip_md(s) if isinstance(s, str) else s for s in result["steps"]]

        result["category_name"] = selected_category["name"]
        return result
