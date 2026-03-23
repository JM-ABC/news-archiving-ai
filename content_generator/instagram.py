from typing import Dict


class InstagramGenerator:
    def __init__(self, client, model: str):
        self._client = client
        self.model = model

    def generate(self, data: Dict) -> str:
        trends = data["trends"]
        date = data["date"]
        titles = "\n".join(f"- {a['title']}" for a in data["articles"][:5])

        prompt = f"""다음 AI 뉴스를 바탕으로 인스타그램 캡션을 작성하세요.

날짜: {date}
핵심 트렌드:
{trends}

주요 기사:
{titles}

요건:
- 이모지 풍부하게 (문단마다 1-2개)
- 핵심 내용을 짧은 문단들로
- 마지막 줄 전에 빈 줄
- 마지막: 해시태그 20-25개 (한국어+영어 혼용, #AI #인공지능 #테크뉴스 등 포함)

캡션 내용만 반환:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
