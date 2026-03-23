import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional


class GstackCrawler:
    def __init__(self, binary_path: Optional[Path], targets: List[Dict]):
        self.binary = Path(binary_path) if binary_path else None
        self.targets = targets

    def crawl(self) -> List[Dict]:
        if not self.binary:
            if self.targets:
                print("[gstack] 바이너리 없음 - 크롤링 건너뜀")
            return []

        articles = []
        seen_urls = set()
        binary_ok = True

        for target in self.targets:
            if not binary_ok:
                break
            try:
                result = self._crawl_target(target)
                for art in result:
                    if art["url"] not in seen_urls:
                        seen_urls.add(art["url"])
                        articles.append(art)
            except FileNotFoundError:
                print("[gstack] 바이너리 없음 - 크롤링 건너뜀")
                binary_ok = False
            except Exception as e:
                print(f"[gstack] {target['label']} 크롤링 실패: {e}")

        return articles

    def _crawl_target(self, target: Dict) -> List[Dict]:
        chain = json.dumps([
            ["goto", target["url"]],
            ["links"],
        ])

        result = subprocess.run(
            [str(self.binary), "chain"],
            input=chain,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return []

        articles = []
        limit = target.get("max", 3)

        for line in result.stdout.strip().splitlines():
            if " → " not in line:
                continue
            parts = line.split(" → ", 1)
            if len(parts) != 2:
                continue
            title, url = parts[0].strip(), parts[1].strip()
            if not url.startswith("http") or not title:
                continue
            articles.append({
                "title": title,
                "url": url,
                "summary": "",
                "label": target["label"],
                "region": target["region"],
            })
            if len(articles) >= limit:
                break

        return articles
