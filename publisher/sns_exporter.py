from pathlib import Path
from typing import Dict


class SNSExporter:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)

    def export(self, date: str, linkedin: str, threads: str, instagram: str):
        day_dir = self.output_dir / date
        day_dir.mkdir(parents=True, exist_ok=True)

        (day_dir / "linkedin.md").write_text(
            f"# 링크드인 | {date}\n\n{linkedin}\n", encoding="utf-8"
        )
        (day_dir / "threads.md").write_text(
            f"# 스레드 | {date}\n\n{threads}\n", encoding="utf-8"
        )
        (day_dir / "instagram.md").write_text(
            f"# 인스타그램 | {date}\n\n{instagram}\n", encoding="utf-8"
        )
        print(f"[sns] SNS 콘텐츠 저장 완료 → {day_dir}")
