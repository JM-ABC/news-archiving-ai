import anthropic
import json
from typing import List, Dict


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
- bullets: 핵심 내용 3개 (각 50자 이내 한국어, 구체적 수치·기업명 포함)
- implication: 산업 시사점 1문장 (40자 이내)
- url: 원문 URL (그대로)

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
각 트렌드는 "• " 로 시작하는 1-2문장으로 작성하세요.
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
        raw = re.sub(r'_(.+?)_', r'\1', raw)
        return raw
