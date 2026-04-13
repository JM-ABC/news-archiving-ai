#!/usr/bin/env python3
"""AI 콘텐츠 생성 에이전트 - 메인 파이프라인"""

import sys
import anthropic
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from config.settings import (
    CLAUDE_API_KEY, CLAUDE_MODEL,
    NOTION_API_KEY, NOTION_DATABASE_ID,
    RESEND_API_KEY, EMAIL_FROM, EMAIL_TO, EMAIL_BCC,
    GSTACK_BINARY, TRENDS_DIR, OUTPUT_DIR,
    KR_MAX, GL_MAX, MIN_NEW_ARTICLES,
)
from config.feeds import RSS_FEEDS, CRAWL_TARGETS
from collector.rss_collector import RSSCollector
from collector.gstack_crawler import GstackCrawler
from summarizer.claude_summarizer import ClaudeSummarizer
from content_generator.newsletter import NewsletterGenerator
from content_generator.linkedin import LinkedInGenerator
from content_generator.threads import ThreadsGenerator
from content_generator.instagram import InstagramGenerator
from publisher.email_publisher import EmailPublisher
from publisher.notion_publisher import NotionPublisher
from publisher.sns_exporter import SNSExporter

def load_seen_urls(trends_dir: Path) -> set:
    """직전 발송 trend 파일 1개의 URL만 중복 제거 대상으로 사용.
    발송 주기(월·수·금)가 바뀌어도 항상 바로 전 발송분과만 비교한다."""
    seen = set()
    files = sorted(trends_dir.glob("trend_*.txt"))
    if not files:
        return seen
    last_file = files[-1]
    try:
        for line in last_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("http"):
                seen.add(stripped)
            elif stripped.startswith("원문:"):
                url_part = stripped[len("원문:"):].strip()
                if url_part.startswith("http"):
                    seen.add(url_part)
    except Exception as e:
        print(f"[WARN] trend 파일 파싱 실패: {last_file.name} - {e}")
    return seen


def prioritize(articles: list) -> list:
    kr = [a for a in articles if a["region"] == "KR"][:KR_MAX]
    gl = [a for a in articles if a["region"] == "GL"][:GL_MAX]
    return kr + gl


def main():
    preview = "--preview" in sys.argv
    KST = ZoneInfo("Asia/Seoul")
    today = datetime.now(KST).strftime("%Y-%m-%d")
    TRENDS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"=== AI 뉴스 파이프라인 | {today} ===\n")

    # 1/8 RSS 수집
    print("1/8 RSS 피드 수집 중...")
    rss_articles = RSSCollector(RSS_FEEDS).fetch()
    print(f"    → {len(rss_articles)}개 수집")

    # 2/8 gstack 크롤링
    print("2/8 gstack 크롤링 중...")
    crawled = GstackCrawler(binary_path=GSTACK_BINARY, targets=CRAWL_TARGETS).crawl()
    print(f"    → {len(crawled)}개 수집")

    # 3/8 중복 제거 + 우선순위
    print("3/8 중복 제거 및 정렬 중...")
    seen = load_seen_urls(TRENDS_DIR)
    seen_in_run: set = set()
    all_articles = []
    for a in rss_articles + crawled:
        if a["url"] not in seen and a["url"] not in seen_in_run:
            seen_in_run.add(a["url"])
            all_articles.append(a)
    articles = prioritize(all_articles)
    kr_n = sum(1 for a in articles if a["region"] == "KR")
    gl_n = sum(1 for a in articles if a["region"] == "GL")
    print(f"    → 신규 {len(articles)}개 (국내:{kr_n}, 글로벌:{gl_n})")

    if len(articles) < MIN_NEW_ARTICLES:
        print(f"\n신규 기사 {len(articles)}개 - {MIN_NEW_ARTICLES}개 미달. 발행 건너뜀.")
        return

    # Claude 클라이언트
    claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    summarizer = ClaudeSummarizer(api_key=CLAUDE_API_KEY, model=CLAUDE_MODEL)

    # 4/8 기사 요약
    print("4/8 Claude 요약 중...")
    summarized = summarizer.summarize(articles)
    for i, art in enumerate(summarized):
        if i < len(articles):
            art.setdefault("label", articles[i].get("label", ""))
            art.setdefault("region", articles[i].get("region", ""))
    print(f"    → {len(summarized)}개 완료")

    # 5/8 트렌드 도출
    print("5/8 핵심 트렌드 도출 중...")
    trends = summarizer.generate_trends(articles)
    print("    → 완료")

    # 직전 발송 카테고리 읽기 (연속 반복 방지)
    last_tip_file = TRENDS_DIR / "last_tip_category.txt"
    exclude_names = []
    if last_tip_file.exists():
        try:
            exclude_names = [l.strip() for l in last_tip_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        except Exception:
            pass

    tip = summarizer.generate_tip(summarized, exclude_names=exclude_names)

    # 사용한 카테고리 저장 (최근 2개 유지)
    if tip.get("category_name"):
        recent = exclude_names[-1:] + [tip["category_name"]]  # 직전 1개 + 이번
        last_tip_file.write_text("\n".join(recent), encoding="utf-8")

    data = {
        "date": today,
        "trends": trends,
        "articles": summarized,
        "tip": tip,
    }

    # 6/8 뉴스레터 생성
    print("6/8 뉴스레터 생성 중...")
    gen = NewsletterGenerator()
    html = gen.generate(data)
    txt = gen.generate_txt(data)
    trend_file = TRENDS_DIR / f"trend_{today}.txt"
    trend_file.write_text(txt, encoding="utf-8")
    print(f"    → {trend_file}")

    # 주제 선택 (--interactive 모드)
    interactive = "--interactive" in sys.argv
    if interactive:
        print("\n주제 각도 분석 중...")
        topics = summarizer.propose_topics(summarized)
        print("\n오늘 뉴스에서 집중할 주제를 선택하세요:\n")
        for t in topics:
            print(f"  {t}")
        print()
        choice = input("번호를 입력하세요 (기본값: 자동 선택): ").strip()
        focus_topic = ""
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(topics):
                focus_topic = topics[idx]
                print(f"\n선택: {focus_topic}\n")
        data["focus_topic"] = focus_topic

    # 7/8 SNS 콘텐츠 생성 (비활성화)
    print("7/8 SNS 콘텐츠 생성 건너뜀 (비활성화)")

    if preview:
        html_file = TRENDS_DIR / f"newsletter_{today}.html"
        html_file.write_text(html, encoding="utf-8")
        print("\n[PREVIEW 모드] 이메일·Notion 건너뜀.")
        print(f"  뉴스레터: {trend_file}")
        print(f"  HTML: {html_file}")
        import webbrowser
        webbrowser.open(html_file.as_uri())
        return

    # 8/8 발행
    NotionPublisher(NOTION_API_KEY, NOTION_DATABASE_ID).upload(today, trends, summarized)
    EmailPublisher(RESEND_API_KEY, EMAIL_FROM, EMAIL_TO, EMAIL_BCC).send(
        subject=f"Daily AI | {today}", html=html
    )
    print("\n파이프라인 완료!")


if __name__ == "__main__":
    main()
