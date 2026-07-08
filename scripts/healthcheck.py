#!/usr/bin/env python3
"""파이프라인 헬스체크 — 산출물 중단 감지 + 실패 알림.

사용법:
  python scripts/healthcheck.py --check-stale [--max-age-days 8]
      마지막 trend 파일이 기준일보다 오래됐으면 경고 이메일 발송.
      (피드가 죽거나 MIN_NEW_ARTICLES 미달이 반복되는 침묵 장애 감지)

  python scripts/healthcheck.py --notify-failure
      GitHub Actions 실패 시 알림 이메일 발송 (if: failure() 스텝에서 호출).

  python scripts/healthcheck.py --check-feeds
      RSS 피드·크롤링 대상의 생존 여부를 점검해 리포트 출력.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import RESEND_API_KEY, EMAIL_FROM, EMAIL_TO, TRENDS_DIR  # noqa: E402


def latest_trend_date(trends_dir: Path):
    """trend_YYYY-MM-DD.txt 파일명 기준 가장 최근 발행일 반환. 없으면 None."""
    files = sorted(trends_dir.glob("trend_*.txt"))
    for f in reversed(files):
        try:
            return datetime.strptime(
                f.stem.replace("trend_", ""), "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def latest_publish_date(trends_dir: Path):
    """마지막 발행일 — seen_urls.json(CI에서도 커밋됨) 우선, 없으면 trend 파일명."""
    seen_file = trends_dir / "seen_urls.json"
    if seen_file.exists():
        try:
            data = json.loads(seen_file.read_text(encoding="utf-8"))
            dates = []
            for d in data.values():
                try:
                    dates.append(
                        datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    )
                except (TypeError, ValueError):
                    continue
            if dates:
                return max(dates)
        except Exception as e:
            print(f"[WARN] seen_urls.json 파싱 실패: {e}")
    return latest_trend_date(trends_dir)


def staleness_days(latest, now=None) -> int:
    """마지막 발행 후 경과 일수. 발행 이력이 없으면 -1."""
    if latest is None:
        return -1
    now = now or datetime.now(timezone.utc)
    return (now - latest).days


def send_alert(subject: str, body: str) -> bool:
    """Resend로 경고 이메일 발송. 설정이 없으면 콘솔 출력만."""
    if not (RESEND_API_KEY and EMAIL_FROM and EMAIL_TO):
        print(f"[WARN] 이메일 설정 없음 — 콘솔 출력만.\n제목: {subject}\n{body}")
        return False
    import resend

    resend.api_key = RESEND_API_KEY
    try:
        resend.Emails.send({
            "from": EMAIL_FROM,
            "to": EMAIL_TO,
            "subject": subject,
            "text": body,
        })
    except Exception as e:  # 알림 실패가 워크플로를 실패시키지 않도록
        print(f"[ERROR] 알림 발송 실패: {e}\n제목: {subject}\n{body}")
        return False
    print(f"[OK] 알림 발송: {subject}")
    return True


_UA = {"User-Agent": "Mozilla/5.0 (compatible; news-agent-healthcheck)"}


def check_feed(feed: dict, days: int = 4, timeout: int = 15) -> dict:
    """RSS 피드 1개 점검. status: ok | stale_feed | empty | http_error | error"""
    import feedparser
    import requests

    result = {"label": feed["label"], "url": feed["url"], "status": "ok", "detail": ""}
    try:
        r = requests.get(feed["url"], timeout=timeout, headers=_UA)
    except Exception as e:
        result.update(status="error", detail=str(e)[:120])
        return result
    if r.status_code != 200:
        result.update(status="http_error", detail=f"HTTP {r.status_code}")
        return result

    parsed = feedparser.parse(r.content)
    if not parsed.entries:
        result.update(status="empty", detail="엔트리 0개 (피드 형식 변경 가능성)")
        return result

    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    recent = 0
    for entry in parsed.entries:
        pub = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if pub:
            import calendar
            if calendar.timegm(pub) >= cutoff:
                recent += 1
    if recent == 0:
        result.update(
            status="stale_feed",
            detail=f"전체 {len(parsed.entries)}개, 최근 {days}일 내 0개",
        )
    else:
        result["detail"] = f"최근 {days}일 내 {recent}개"
    return result


def check_crawl_target(target: dict, timeout: int = 15) -> dict:
    """크롤링 대상 URL 접근 가능 여부만 점검."""
    import requests

    result = {"label": target["label"], "url": target["url"], "status": "ok", "detail": ""}
    try:
        r = requests.get(target["url"], timeout=timeout, headers=_UA)
        if r.status_code != 200:
            result.update(status="http_error", detail=f"HTTP {r.status_code}")
    except Exception as e:
        result.update(status="error", detail=str(e)[:120])
    return result


def feed_report(days: int = 4) -> tuple[str, int]:
    """전체 피드 점검 리포트 문자열과 문제 개수 반환."""
    from config.feeds import RSS_FEEDS, CRAWL_TARGETS

    lines, problems = [], 0
    lines.append("── RSS 피드 ──")
    for feed in RSS_FEEDS:
        r = check_feed(feed, days=days)
        mark = "OK" if r["status"] == "ok" else "FAIL"
        if r["status"] != "ok":
            problems += 1
        lines.append(f"[{mark}] {r['label']}: {r['status']} {r['detail']}".rstrip())
    lines.append("── 크롤링 대상 ──")
    for target in CRAWL_TARGETS:
        r = check_crawl_target(target)
        mark = "OK" if r["status"] == "ok" else "FAIL"
        if r["status"] != "ok":
            problems += 1
        lines.append(f"[{mark}] {r['label']}: {r['status']} {r['detail']}".rstrip())
    return "\n".join(lines), problems


def _run_url() -> str:
    server = os.getenv("GITHUB_SERVER_URL", "")
    repo = os.getenv("GITHUB_REPOSITORY", "")
    run_id = os.getenv("GITHUB_RUN_ID", "")
    if server and repo and run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"
    return "(로컬 실행)"


def check_stale(max_age_days: int) -> None:
    latest = latest_publish_date(TRENDS_DIR)
    days = staleness_days(latest)
    if days == -1:
        print("[WARN] 발행 이력 없음 — 첫 실행이면 정상.")
        return
    if days <= max_age_days:
        print(f"[OK] 마지막 발행 {days}일 전 — 정상 (기준 {max_age_days}일).")
        return
    try:
        report, n_problems = feed_report()
        feed_section = f"피드 진단 (문제 {n_problems}건):\n{report}"
    except Exception as e:
        feed_section = f"피드 진단 실패: {e}"
    send_alert(
        f"⚠️ AI 뉴스레터 {days}일째 발행 없음",
        f"마지막 발행: {latest:%Y-%m-%d} ({days}일 전, 기준 {max_age_days}일 초과)\n\n"
        "점검 순서:\n"
        "1. GitHub Actions 탭에서 스케줄이 비활성화됐는지 확인 (60일 무활동 시 자동 비활성화)\n"
        "2. 최근 실행 로그에서 '신규 기사 N개 미달' 반복 여부 확인\n"
        "3. 아래 피드 진단에서 죽은 피드 확인\n\n"
        f"{feed_section}\n\n"
        f"실행 로그: {_run_url()}",
    )


def notify_failure() -> None:
    send_alert(
        "🚨 AI 뉴스 파이프라인 실패",
        f"GitHub Actions 실행이 실패했습니다.\n\n로그: {_run_url()}",
    )


def main():
    parser = argparse.ArgumentParser(description="파이프라인 헬스체크")
    parser.add_argument("--check-stale", action="store_true")
    parser.add_argument("--max-age-days", type=int, default=8)
    parser.add_argument("--notify-failure", action="store_true")
    parser.add_argument("--check-feeds", action="store_true")
    args = parser.parse_args()

    if args.notify_failure:
        notify_failure()
    elif args.check_stale:
        check_stale(args.max_age_days)
    elif args.check_feeds:
        report, n_problems = feed_report()
        print(report)
        print(f"\n문제 {n_problems}건")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
