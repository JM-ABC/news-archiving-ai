"""발송 이력 URL 상태 저장소 — trends/seen_urls.json.

기존 방식(직전 trend 파일 1개 파싱)의 문제:
발행이 건너뛰어지면(기사 미달) trend 파일이 안 생겨서 더 오래된 발송분과만
비교하게 되고, 이미 다룬 기사가 재발행될 수 있다.
상태 파일은 발행 성공 시에만 갱신되며 RETENTION_DAYS 이후 자동 정리된다.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

RETENTION_DAYS = 30


def load_seen(path: Path) -> set:
    """상태 파일에서 발송 이력 URL 집합 로드. 없거나 손상 시 빈 집합."""
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.keys())
    except Exception as e:
        print(f"[WARN] seen_urls 로드 실패: {e}")
        return set()


def record_seen(path: Path, urls, today: str, retention_days: int = RETENTION_DAYS) -> None:
    """발행한 URL을 오늘 날짜로 기록하고 보존 기간이 지난 항목은 정리."""
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    for url in urls:
        data[url] = today

    cutoff = datetime.strptime(today, "%Y-%m-%d") - timedelta(days=retention_days)
    pruned = {}
    for url, d in data.items():
        try:
            if datetime.strptime(d, "%Y-%m-%d") >= cutoff:
                pruned[url] = d
        except (TypeError, ValueError):
            continue
    path.write_text(
        json.dumps(pruned, ensure_ascii=False, indent=1), encoding="utf-8"
    )
