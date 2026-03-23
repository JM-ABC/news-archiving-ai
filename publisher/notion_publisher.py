from typing import Dict, List


class NotionPublisher:
    def __init__(self, api_key: str, database_id: str):
        self._api_key = api_key
        self.database_id = database_id

    def upload(self, date: str, trends: str, articles: List[Dict]) -> bool:
        if not self._api_key or not self.database_id:
            print("[notion] 설정 없음 — 건너뜀")
            return False
        try:
            from notion_client import Client
            client = Client(auth=self._api_key)
            blocks = self._build_blocks(trends, articles)

            page = client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"text": {"content": f"AI 뉴스 | {date}"}}]},
                },
                children=blocks[:100],
            )
            # Upload remaining blocks in chunks of 100
            for i in range(100, len(blocks), 100):
                client.blocks.children.append(page["id"], children=blocks[i:i+100])

            print(f"[notion] 업로드 완료")
            return True
        except Exception as e:
            print(f"[notion] 업로드 실패: {e}")
            return False

    def _build_blocks(self, trends: str, articles: List[Dict]) -> List[Dict]:
        blocks = []
        blocks.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🔑 오늘의 핵심 트렌드"}}]}
        })
        for t in trends.split("\n"):
            if t.strip():
                blocks.append({
                    "object": "block", "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"text": {"content": t.lstrip("• ")}}]}
                })
        blocks.append({"object": "block", "type": "divider", "divider": {}})

        for a in articles:
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": a.get("title", "")}}]}
            })
            for b in a.get("bullets", []):
                blocks.append({
                    "object": "block", "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"text": {"content": b}}]}
                })
            if a.get("implication"):
                blocks.append({
                    "object": "block", "type": "quote",
                    "quote": {"rich_text": [{"text": {"content": f"💡 {a['implication']}"}}]}
                })
            url = a.get("url", "")
            if url:
                blocks.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": url, "link": {"url": url}}}]}
                })
            blocks.append({"object": "block", "type": "divider", "divider": {}})

        return blocks
