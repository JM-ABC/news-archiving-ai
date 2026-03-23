from typing import Dict


class ThreadsGenerator:
    def __init__(self, client, model: str):
        self._client = client
        self.model = model

    def generate(self, data: Dict) -> str:
        trends = data["trends"]
        date = data["date"]

        prompt = f"""다음 AI 뉴스 트렌드를 바탕으로 스레드(Threads) 포스트를 작성하세요.

날짜: {date}
핵심 트렌드:
{trends}

요건:
- 500자 이내 한국어
- 대화체, 친근한 톤
- 첫 문장이 강렬하게 시작
- 마지막에 독자에게 질문 하나
- 이모지 2-3개 사용
- 해시태그 없음

포스트 내용만 반환:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
