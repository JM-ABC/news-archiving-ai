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
- bullets: 핵심 내용 3개 (각 30자 이내 한국어)
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

        # JSON 파싱 — 코드블록 제거 후 재시도
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)

    def generate_trends(self, articles: List[Dict]) -> str:
        """전체 기사에서 핵심 트렌드 3가지 도출."""
        if not articles:
            return ""

        titles = "\n".join(f"- {a['title']}" for a in articles)

        prompt = f"""다음 AI 뉴스 기사 제목들을 보고 오늘의 핵심 트렌드 3가지를 한국어로 도출하세요.
각 트렌드는 "• " 로 시작하는 1-2문장으로 작성하세요.

기사 목록:
{titles}

핵심 트렌드 3가지:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
