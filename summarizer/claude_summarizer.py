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
- title: 한국어 제목 (원문이 영어면 번역)
- category: 소카테고리 (모델 출시/연구/규제/산업응용/인프라/기타 중 하나)
- bullets: 핵심 내용 3개 (각 50자 이내 한국어, ~어요/에요 어체, 구체적 수치·기업명 포함)
- implication: 산업 시사점 1문장 (40자 이내, ~어요/에요 어체)
- url: 원문 URL (그대로)
- score: 오늘 AI 업계 전반에서 이 기사의 중요도 정수 (1-10, 10이 가장 중요). 기준: 파급력·신뢰성·독자 관련성. 단순 루머·마이너 업데이트는 낮게 채점.

기사 목록:
{articles_text}

JSON 배열만 반환 (마크다운 코드블록 없이):"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=4096,
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

        selected_category = random.choice(TIP_CATEGORIES)

        prompt = f"""오늘의 AI 팁 카테고리: {selected_category["name"]}
난이도: {selected_category["difficulty"]}
참고 예시: {selected_category["example"]}

위 카테고리에서 30-40대 직장인이 지금 바로 실행 가능한 AI 활용법을 하나 제안해줘.
오늘 뉴스 (참고만, 얽매이지 말 것): {articles_text}

아래 JSON 형식으로만 반환해 (마크다운 코드블록 없이):
{{
  "task": "자동화 아이디어 설명 2-3문장 (~어요/에요 어체)",
  "tools": ["툴1", "툴2"],
  "prompt": "그 툴에 복붙할 수 있는 구체적 프롬프트 (한국어)"
}}

스타일 규칙:
- task: "상황 묘사 → Claude/Claude Code가 해결 → 실용적 이점" 3문장, ~어요/에요 어체
- prompt: 경로·조건만 구체적으로, 짧고 직관적하게
- 전문 용어 설명 불필요 ("Python인지 몰라도 돼요" 같은 안심 문구 가끔 사용)
- difficulty가 claude-code이면 tools에 반드시 "Claude Code" 포함
- 마크다운 기호(#, **, *) 사용 금지

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
