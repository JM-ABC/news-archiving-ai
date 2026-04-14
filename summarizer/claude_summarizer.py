import anthropic
import json
import random
from typing import List, Dict

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
    # 이커머스 특화
    {
        "name": "상품 상세페이지 카피 작성",
        "difficulty": "prompt-only",
        "example": "상품명·스펙만 넣으면 구매욕 자극하는 상세페이지 문구 자동 생성",
    },
    {
        "name": "고객 리뷰 자동 수집·분석",
        "difficulty": "claude-code",
        "example": "상품 URL만 붙여넣으면 Claude Code가 playwright를 설치·실행해서 JS 렌더링 리뷰 페이지를 크롤링한 뒤 불만·긍정·CS 위험 리뷰를 분류해서 파일로 저장. 프롬프트에는 playwright 설치 지시와 URL을 포함할 것. 마지막 step에 '중간에 권한 확인이 뜨면 허용' 안내 추가.",
    },
    {
        "name": "CS 응대 템플릿 자동화",
        "difficulty": "prompt-only",
        "example": "환불·교환·배송지연 유형별 CS 답변 템플릿 10종 자동 생성",
    },
    {
        "name": "상품 태그·카테고리 자동 분류",
        "difficulty": "claude-code",
        "example": "상품명 목록 CSV를 넣으면 카테고리·검색 태그 자동 분류해서 새 열로 추가",
    },
    {
        "name": "판매 데이터 리포트 자동화",
        "difficulty": "claude-code",
        "example": "주간 판매 엑셀을 넣으면 베스트셀러·재고 위험 상품·매출 추이 요약 리포트 생성",
    },
    {
        "name": "마케팅 소재 멀티포맷 변환",
        "difficulty": "prompt-only",
        "example": "상품 특징 3줄을 넣으면 배너 카피·SNS 문구·이메일 제목 한번에 생성",
    },
    {
        "name": "시즌 프로모션 기획 초안",
        "difficulty": "prompt-only",
        "example": "행사 일정·할인율·타겟 상품만 알려주면 프로모션 기획서 초안 자동 작성",
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
        import re
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
        import re
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

        prompt = f"""오늘의 AI 팁 카테고리: {selected_category["name"]}
난이도: {selected_category["difficulty"]}
참고 예시: {selected_category["example"]}

위 카테고리에서 30-40대 직장인이 지금 바로 실행 가능한 AI 활용법을 하나 제안해줘.
오늘 뉴스 (참고만, 얽매이지 말 것): {articles_text}

아래 JSON 형식으로만 반환해 (마크다운 코드블록 없이):
{{
  "task": "자동화 아이디어 설명 2-3문장 (~어요/에요 어체)",
  "tools": ["툴1", "툴2"],
  "steps": [
    "1단계 설명 (Claude Code에서 어디서 무엇을 누르는지까지 구체적으로)",
    "2단계 설명",
    "3단계 설명",
    "4단계 설명 (결과 확인·저장 등 마무리)"
  ],
  "prompt": "그 툴에 복붙할 수 있는 구체적 프롬프트 (한국어, 경로나 조건은 [대괄호]로 표시)"
}}

스타일 규칙:
- task: "상황 묘사 → Claude/Claude Code가 해결 → 실용적 이점" 3문장, ~어요/에요 어체
- steps: Claude Code 앱을 열고 → 프롬프트 붙여넣고 → 결과 확인하는 흐름. 코딩 지식 없어도 따라할 수 있게. 각 단계 30자 이내.
- prompt: [파일 경로], [조건] 형식으로 독자가 바꿀 부분을 명확히 표시. 2-4문장.
- 전문 용어 설명 불필요 ("Python인지 몰라도 돼요" 같은 안심 문구 가끔 사용)
- difficulty가 claude-code이면 tools에 반드시 "Claude Code" 포함
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

        import re
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
