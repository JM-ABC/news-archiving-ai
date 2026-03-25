from typing import Dict


class ThreadsGenerator:
    def __init__(self, client, model: str):
        self._client = client
        self.model = model

    def generate(self, data: Dict) -> str:
        date = data["date"]
        articles_text = "\n".join(
            f"- {a['title']}: {a.get('implication', '')} (핵심: {a.get('bullets', [''])[0]})"
            for a in data["articles"][:10]
            if a.get("category") != "기타"
        )

        focus = data.get("focus_topic", "")
        if focus:
            topic_line = f"\n집중 주제: {focus}\n이 주제로 포스트를 작성하세요."
        else:
            topic_line = "\n오늘 가장 흥미롭거나 놀라운 기사 하나를 골라 작성하세요."

        prompt = f"""다음 AI 뉴스를 바탕으로 스레드(Threads) 포스트를 작성하세요.

날짜: {date}{topic_line}
기사 목록:
{articles_text}

요건:
- 400자 이내 한국어
- 대화체, 친근한 톤
- 하나의 기사에 집중해서 파고들 것 (여러 기사 나열 금지)
- 첫 문장: 독자가 멈추게 만드는 사실이나 반전 (질문형이나 놀라운 사실로 시작)
- 왜 이게 중요한지 구체적으로 설명
- 마지막에 독자에게 날카로운 질문 하나
- 이모지 2-3개만 사용
- 해시태그 없음

포스트 내용만 반환:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
