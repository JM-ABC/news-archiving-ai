from typing import Dict


class InstagramGenerator:
    def __init__(self, client, model: str):
        self._client = client
        self.model = model

    def generate(self, data: Dict) -> str:
        date = data["date"]
        articles_text = "\n".join(
            f"- {a['title']}\n  {' / '.join(a.get('bullets', []))}"
            for a in data["articles"][:6]
            if a.get("category") != "기타"
        )

        focus = data.get("focus_topic", "")
        focus_line = f"\n집중 주제: {focus}\n이 주제에 집중해서 캡션을 작성하세요. 다른 기사는 보조 맥락으로만 활용하세요." if focus else ""

        prompt = f"""다음 AI 뉴스를 바탕으로 인스타그램 캡션을 작성하세요.

날짜: {date}{focus_line}
기사 요약:
{articles_text}

요건:
- 전체 300-500자 한국어
- 오늘 뉴스에서 가장 흥미로운 스토리로 시작 (첫 줄이 핵심)
- 구체적 기업명, 금액, 사례를 활용한 짧은 문단 3-4개
- 각 문단에 이모지 1개 (과하지 않게)
- 마지막 문단: 팔로워에게 질문 또는 오늘의 인사이트 한 줄
- 빈 줄로 문단 구분
- 해시태그는 마지막에 10개 이내 (핵심 키워드만, 한국어+영어 혼용)

캡션 내용만 반환:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
