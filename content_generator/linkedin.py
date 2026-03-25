from typing import Dict


class LinkedInGenerator:
    def __init__(self, client, model: str):
        self._client = client
        self.model = model

    def generate(self, data: Dict) -> str:
        trends = data["trends"]
        date = data["date"]
        articles_text = "\n".join(
            f"- {a['title']} ({a.get('label','')})\n"
            f"  핵심: {' / '.join(a.get('bullets', []))}\n"
            f"  시사점: {a.get('implication', '')}"
            for a in data["articles"][:7]
            if a.get("category") != "기타"
        )

        focus = data.get("focus_topic", "")
        focus_line = f"\n집중 주제: {focus}\n이 주제에 집중해서 포스트를 작성하세요. 다른 기사는 보조 맥락으로만 활용하세요." if focus else ""

        prompt = f"""다음 AI 뉴스를 바탕으로 링크드인 포스트를 작성하세요.

날짜: {date}{focus_line}
기사 요약:
{articles_text}

요건:
- 400-700자 한국어
- 전문적이고 인사이트 있는 톤
- 첫 줄: 오늘 뉴스에서 가장 임팩트 있는 사실이나 수치로 시작 (클리셰 금지)
- 구체적 기업명·투자 금액·연구 결과 등 수치 반드시 포함
- 번호 목록으로 오늘의 핵심 3가지 (각각 구체적 사례 포함)
- 마지막에 독자에게 실질적인 질문 하나로 마무리
- 해시태그 5개 이내 (마지막에, 반드시 # 기호 포함: 예) #AI #에이전트)
- #, **, * 마크다운 기호 절대 사용하지 말 것

포스트 내용만 반환:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
