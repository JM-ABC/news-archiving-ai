from typing import Dict


class LinkedInGenerator:
    def __init__(self, client, model: str):
        self._client = client
        self.model = model

    def generate(self, data: Dict) -> str:
        trends = data["trends"]
        date = data["date"]
        titles = "\n".join(f"- {a['title']}" for a in data["articles"][:5])

        prompt = f"""다음 AI 뉴스 트렌드를 바탕으로 링크드인 포스트를 작성하세요.

날짜: {date}
핵심 트렌드:
{trends}

주요 기사:
{titles}

요건:
- 300-600자 한국어
- 전문적이고 인사이트 있는 톤
- 첫 줄이 주목을 끄는 훅
- 번호 목록으로 핵심 3가지
- 마지막에 독자 참여 유도 CTA
- 해시태그 5개 이내 (마지막에)

포스트 내용만 반환:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
