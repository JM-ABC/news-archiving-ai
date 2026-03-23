# AI 콘텐츠 생성 에이전트 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** AI 뉴스를 RSS + gstack으로 수집하고 Claude Haiku로 요약·트렌드 도출 후 뉴스레터(이메일/Notion)와 SNS 콘텐츠 3종(링크드인·스레드·인스타그램)을 자동 생성·저장하는 파이프라인 구축.

**Architecture:** 기능별 모듈 분리 (collector / summarizer / content_generator / publisher), main.py가 8단계 파이프라인을 순차 실행. SNS 콘텐츠는 output/ 폴더에 마크다운으로 저장해 수동 복붙 방식.

**Tech Stack:** Python 3.12, Claude API (claude-haiku-4-5-20251001), feedparser, gstack browse binary, notion-client, resend, GitHub Actions

---

## 전제 조건

- `~/.claude/skills/gstack/browse/dist/browse` 바이너리 존재 (없으면 `cd ~/.claude/skills/gstack && ./setup` 실행)
- `c:/Users/USER/Desktop/뉴스아카이빙_AI/` 를 작업 디렉토리로 사용
- Python 3.12 + pip 사용 가능
- `.env` 파일에 `CLAUDE_API_KEY` 최소 설정

---

## Task 1: 프로젝트 기반 구조 생성

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Create: `config/feeds.py`

**Step 1: 디렉토리 골격 생성**

```bash
cd "c:/Users/USER/Desktop/뉴스아카이빙_AI"
mkdir -p collector summarizer content_generator publisher config tests output trends
touch collector/__init__.py summarizer/__init__.py content_generator/__init__.py publisher/__init__.py config/__init__.py tests/__init__.py
```

**Step 2: requirements.txt 작성**

```
anthropic>=0.40.0
feedparser>=6.0.11
notion-client>=2.2.1
resend>=2.0.0
python-dotenv>=1.0.0
requests>=2.31.0
```

**Step 3: .env.example 작성**

```
CLAUDE_API_KEY=your_anthropic_key_here
NOTION_API_KEY=
NOTION_DATABASE_ID=
RESEND_API_KEY=
EMAIL_FROM=
EMAIL_TO=
EMAIL_BCC=
GSTACK_BINARY=
```

**Step 4: .gitignore 작성**

```
.env
__pycache__/
*.pyc
*.pyo
output/
trends/
*.html
```

**Step 5: config/settings.py 작성**

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
EMAIL_BCC = [e.strip() for e in os.getenv("EMAIL_BCC", "").split(",") if e.strip()]

BASE_DIR = Path(__file__).parent.parent
TRENDS_DIR = BASE_DIR / "trends"
OUTPUT_DIR = BASE_DIR / "output"

# gstack 바이너리 경로 자동 탐지
_gstack_env = os.getenv("GSTACK_BINARY", "")
if _gstack_env:
    GSTACK_BINARY = Path(_gstack_env)
else:
    _candidates = [
        Path.home() / ".claude/skills/gstack/browse/dist/browse",
        BASE_DIR / ".claude/skills/gstack/browse/dist/browse",
    ]
    GSTACK_BINARY = next((p for p in _candidates if p.exists()), None)

KR_MAX = 13
GL_MAX = 7
MIN_NEW_ARTICLES = 10
DEDUP_DAYS = 4
```

**Step 6: config/feeds.py 작성**

```python
RSS_FEEDS = [
    # 글로벌
    {"label": "TechCrunch AI", "region": "GL", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "max": 8},
    {"label": "MIT Tech Review", "region": "GL", "url": "https://www.technologyreview.com/feed/", "max": 5},
    {"label": "The Verge AI", "region": "GL", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "max": 5},
    {"label": "VentureBeat AI", "region": "GL", "url": "https://venturebeat.com/category/ai/feed/", "max": 5},
    {"label": "Wired AI", "region": "GL", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "max": 5},
    # 국내
    {"label": "전자신문 AI", "region": "KR", "url": "https://www.etnews.com/rss/section.xml?id=13", "max": 8},
    {"label": "ZDNet Korea", "region": "KR", "url": "https://www.zdnet.co.kr/rss/news.xml", "max": 6},
    {"label": "AI타임스", "region": "KR", "url": "https://www.aitimes.com/rss/allArticle.xml", "max": 6},
]

# gstack으로 크롤링할 대상 (RSS 없거나 불안정)
CRAWL_TARGETS = [
    {"label": "OpenAI Blog", "region": "GL", "url": "https://openai.com/news", "selector": "article a", "max": 3},
    {"label": "Anthropic Blog", "region": "GL", "url": "https://www.anthropic.com/news", "selector": "article a", "max": 3},
    {"label": "Google DeepMind", "region": "GL", "url": "https://deepmind.google/discover/blog/", "selector": "article a", "max": 2},
]
```

**Step 7: 의존성 설치**

```bash
pip install -r requirements.txt
```

**Step 8: Commit**

```bash
git init
git add requirements.txt .env.example .gitignore config/
git commit -m "feat: 프로젝트 기반 구조 및 설정 모듈"
```

---

## Task 2: RSS 수집 모듈

**Files:**
- Create: `collector/rss_collector.py`
- Create: `tests/test_rss_collector.py`

**Step 1: 테스트 작성**

`tests/test_rss_collector.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from collector.rss_collector import RSSCollector

def test_fetch_returns_list():
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 3}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            MagicMock(
                title="Test Article",
                link="https://example.com/article",
                summary="Summary text",
                published="Mon, 23 Mar 2026 10:00:00 +0900",
            )
        ])
        articles = collector.fetch()
    assert isinstance(articles, list)
    assert len(articles) == 1
    assert articles[0]["title"] == "Test Article"
    assert articles[0]["region"] == "GL"

def test_fetch_deduplicates_by_url():
    collector = RSSCollector([
        {"label": "Test", "region": "GL", "url": "https://example.com/feed", "max": 5}
    ])
    with patch("feedparser.parse") as mock_parse:
        mock_parse.return_value = MagicMock(entries=[
            MagicMock(title="A", link="https://x.com/1", summary="", published="Mon, 23 Mar 2026 10:00:00 +0900"),
            MagicMock(title="A", link="https://x.com/1", summary="", published="Mon, 23 Mar 2026 10:00:00 +0900"),
        ])
        articles = collector.fetch()
    assert len(articles) == 1
```

**Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/test_rss_collector.py -v
```
Expected: FAIL (ImportError)

**Step 3: collector/rss_collector.py 구현**

```python
import feedparser
from datetime import datetime, timezone, timedelta
from typing import List, Dict

class RSSCollector:
    def __init__(self, feeds: List[Dict]):
        self.feeds = feeds

    def fetch(self, days: int = 4) -> List[Dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        articles = []
        seen_urls = set()

        for feed in self.feeds:
            parsed = feedparser.parse(feed["url"])
            count = 0
            limit = feed.get("max", 10)

            for entry in parsed.entries:
                if count >= limit:
                    break
                url = getattr(entry, "link", "")
                if not url or url in seen_urls:
                    continue

                title = getattr(entry, "title", "").strip()
                summary = getattr(entry, "summary", "").strip()

                seen_urls.add(url)
                articles.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "label": feed["label"],
                    "region": feed["region"],
                })
                count += 1

        return articles
```

**Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/test_rss_collector.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add collector/rss_collector.py tests/test_rss_collector.py
git commit -m "feat: RSS 수집 모듈 (RSSCollector)"
```

---

## Task 3: gstack 크롤링 모듈

**Files:**
- Create: `collector/gstack_crawler.py`
- Create: `tests/test_gstack_crawler.py`

**Step 1: 테스트 작성**

`tests/test_gstack_crawler.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from collector.gstack_crawler import GstackCrawler

def test_crawl_returns_list_when_binary_missing():
    crawler = GstackCrawler(binary_path=None, targets=[
        {"label": "Test", "region": "GL", "url": "https://example.com", "selector": "a", "max": 2}
    ])
    result = crawler.crawl()
    assert isinstance(result, list)
    assert result == []  # 바이너리 없으면 빈 리스트 반환

def test_crawl_returns_articles_on_success():
    crawler = GstackCrawler(binary_path="/fake/browse", targets=[
        {"label": "OpenAI Blog", "region": "GL", "url": "https://openai.com/news", "selector": "a", "max": 2}
    ])
    mock_output = "AI Article 1\thttps://openai.com/1\nAI Article 2\thttps://openai.com/2\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
        articles = crawler.crawl()
    assert isinstance(articles, list)
```

**Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/test_gstack_crawler.py -v
```
Expected: FAIL

**Step 3: collector/gstack_crawler.py 구현**

```python
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

class GstackCrawler:
    def __init__(self, binary_path: Optional[Path], targets: List[Dict]):
        self.binary = binary_path
        self.targets = targets

    def crawl(self) -> List[Dict]:
        if not self.binary or not Path(self.binary).exists():
            print("[gstack] 바이너리 없음 — 크롤링 건너뜀")
            return []

        articles = []
        seen_urls = set()

        for target in self.targets:
            try:
                result = self._crawl_target(target)
                for art in result:
                    if art["url"] not in seen_urls:
                        seen_urls.add(art["url"])
                        articles.append(art)
            except Exception as e:
                print(f"[gstack] {target['label']} 크롤링 실패: {e}")

        return articles

    def _crawl_target(self, target: Dict) -> List[Dict]:
        # gstack으로 페이지 접속 후 링크 텍스트+URL 추출
        cmd = [
            str(self.binary),
            "chain"
        ]
        chain = json.dumps([
            ["goto", target["url"]],
            ["links"],
        ])

        result = subprocess.run(
            cmd,
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
            if "\t" not in line and " → " not in line:
                continue
            # gstack links 출력: "텍스트 → URL"
            sep = " → " if " → " in line else "\t"
            parts = line.split(sep, 1)
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
```

**Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/test_gstack_crawler.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add collector/gstack_crawler.py tests/test_gstack_crawler.py
git commit -m "feat: gstack 웹 크롤링 모듈 (GstackCrawler)"
```

---

## Task 4: Claude 요약 + 트렌드 모듈

**Files:**
- Create: `summarizer/claude_summarizer.py`
- Create: `tests/test_claude_summarizer.py`

**Step 1: 테스트 작성**

`tests/test_claude_summarizer.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from summarizer.claude_summarizer import ClaudeSummarizer

SAMPLE_ARTICLES = [
    {"title": "GPT-5 출시", "url": "https://example.com/1", "summary": "OpenAI가 GPT-5를 발표했다.", "label": "TechCrunch AI", "region": "GL"},
    {"title": "Claude 4 업데이트", "url": "https://example.com/2", "summary": "Anthropic이 Claude를 업데이트했다.", "label": "Anthropic Blog", "region": "GL"},
]

def _make_mock_client(response_text: str):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=response_text)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client

def test_summarize_returns_list():
    summarizer = ClaudeSummarizer(api_key="test", model="claude-haiku-4-5-20251001")
    fake_response = '[{"title":"GPT-5 출시","category":"모델 출시","bullets":["불렛1","불렛2"],"implication":"시사점","url":"https://example.com/1"}]'
    with patch("anthropic.Anthropic", return_value=_make_mock_client(fake_response)):
        summarizer._client = _make_mock_client(fake_response)
        result = summarizer.summarize(SAMPLE_ARTICLES[:1])
    assert isinstance(result, list)
    assert result[0]["title"] == "GPT-5 출시"

def test_generate_trends_returns_string():
    summarizer = ClaudeSummarizer(api_key="test", model="claude-haiku-4-5-20251001")
    summarizer._client = _make_mock_client("• AI 모델 경쟁 심화\n• 멀티모달 발전\n• 규제 강화")
    result = summarizer.generate_trends(SAMPLE_ARTICLES)
    assert isinstance(result, str)
    assert len(result) > 0
```

**Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/test_claude_summarizer.py -v
```
Expected: FAIL

**Step 3: summarizer/claude_summarizer.py 구현**

```python
import anthropic
import json
from typing import List, Dict

class ClaudeSummarizer:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def summarize(self, articles: List[Dict]) -> List[Dict]:
        """기사 목록을 받아 요약 + 카테고리 분류 반환."""
        if not articles:
            return []

        articles_text = "\n".join(
            f"- [{i+1}] {a['title']}\n  출처: {a['label']} ({a['region']})\n  내용: {a['summary'][:300]}\n  URL: {a['url']}"
            for i, a in enumerate(articles)
        )

        prompt = f"""다음 AI 관련 뉴스 기사들을 분석하여 JSON 배열로 반환하세요.

각 기사에 대해:
- title: 한국어 제목 (원문이 영어면 번역)
- category: 소카테고리 (모델 출시/연구/규제/산업응용/인프라/기타 중 하나)
- bullets: 핵심 내용 3개 (각 30자 이내 한국어)
- implication: 산업 시사점 1문장 (40자 이내)
- url: 원문 URL (그대로)

기사 목록:
{articles_text}

JSON 배열만 반환 (마크다운 코드블록 없이):"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()

        # JSON 파싱 시도
        try:
            summarized = json.loads(raw)
        except json.JSONDecodeError:
            # 코드블록 제거 후 재시도
            raw = raw.replace("```json", "").replace("```", "").strip()
            summarized = json.loads(raw)

        return summarized

    def generate_trends(self, articles: List[Dict]) -> str:
        """전체 기사에서 핵심 트렌드 3가지 도출."""
        if not articles:
            return ""

        titles = "\n".join(f"- {a['title']}" for a in articles)

        prompt = f"""다음 AI 뉴스 기사 제목들을 보고 오늘의 핵심 트렌드 3가지를 한국어로 도출하세요.
각 트렌드는 "• " 로 시작하는 1-2문장으로 작성하세요.

기사 목록:
{titles}

핵심 트렌드 3가지:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
```

**Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/test_claude_summarizer.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add summarizer/claude_summarizer.py tests/test_claude_summarizer.py
git commit -m "feat: Claude Haiku 기사 요약 및 트렌드 도출 모듈"
```

---

## Task 5: 뉴스레터 HTML 생성

**Files:**
- Create: `content_generator/newsletter.py`
- Create: `tests/test_newsletter.py`

**Step 1: 테스트 작성**

`tests/test_newsletter.py`:

```python
from content_generator.newsletter import NewsletterGenerator

SAMPLE = {
    "date": "2026-03-23",
    "trends": "• AI 모델 경쟁 심화\n• 멀티모달 발전",
    "articles": [
        {"title": "GPT-5 출시", "category": "모델 출시", "bullets": ["불렛1", "불렛2"], "implication": "시사점", "url": "https://x.com/1", "label": "TechCrunch AI", "region": "GL"},
    ]
}

def test_generate_html_contains_title():
    gen = NewsletterGenerator()
    html = gen.generate(SAMPLE)
    assert "GPT-5 출시" in html
    assert "2026-03-23" in html

def test_generate_txt_contains_trends():
    gen = NewsletterGenerator()
    txt = gen.generate_txt(SAMPLE)
    assert "핵심 트렌드" in txt
    assert "GPT-5 출시" in txt
```

**Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/test_newsletter.py -v
```
Expected: FAIL

**Step 3: content_generator/newsletter.py 구현**

```python
from typing import Dict

class NewsletterGenerator:
    def generate(self, data: Dict) -> str:
        """HTML 뉴스레터 생성."""
        date = data["date"]
        trends = data["trends"]
        articles = data["articles"]

        articles_html = ""
        for a in articles:
            bullets_html = "".join(f"<li>{b}</li>" for b in a.get("bullets", []))
            articles_html += f"""
<div style="margin-bottom:24px;padding:16px;border-left:4px solid #4f46e5;">
  <h3 style="margin:0 0 8px;font-size:16px;">{a['title']}</h3>
  <p style="margin:0 0 4px;font-size:12px;color:#6b7280;">
    [{a.get('category','')}] {a.get('label','')} ({a.get('region','')})
  </p>
  <ul style="margin:8px 0;padding-left:20px;">{bullets_html}</ul>
  <p style="margin:8px 0 4px;font-style:italic;color:#374151;">💡 {a.get('implication','')}</p>
  <a href="{a['url']}" style="font-size:12px;color:#4f46e5;">원문 보기 →</a>
</div>"""

        trends_html = "".join(
            f"<li style='margin-bottom:8px;'>{t.lstrip('• ')}</li>"
            for t in trends.split("\n") if t.strip()
        )

        return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><title>AI 뉴스 | {date}</title></head>
<body style="font-family:sans-serif;max-width:680px;margin:0 auto;padding:24px;color:#1f2937;">
<h1 style="font-size:24px;border-bottom:2px solid #4f46e5;padding-bottom:8px;">
  🤖 AI 뉴스 | {date}
</h1>
<h2 style="font-size:18px;color:#4f46e5;">🔑 오늘의 핵심 트렌드</h2>
<ul style="line-height:1.8;">{trends_html}</ul>
<hr style="margin:24px 0;">
{articles_html}
</body></html>"""

    def generate_txt(self, data: Dict) -> str:
        """텍스트 파일용 리포트 생성."""
        date = data["date"]
        trends = data["trends"]
        articles = data["articles"]

        lines = [f"AI 뉴스 트렌드 | {date}", "---", "", "🔑 오늘의 핵심 트렌드", ""]
        lines += [t for t in trends.split("\n") if t.strip()]
        lines += ["", "---"]

        for a in articles:
            lines.append(f"\n① {a['title']}")
            lines.append(f"   출처: {a.get('label','')} ({a.get('region','')})")
            for b in a.get("bullets", []):
                lines.append(f"   - {b}")
            lines.append(f"\n   👉 {a.get('implication','')}")
            lines.append(f"\n   원문: {a['url']}")
            lines.append("---")

        return "\n".join(lines)
```

**Step 4: 테스트 통과 확인**

```bash
python -m pytest tests/test_newsletter.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add content_generator/newsletter.py tests/test_newsletter.py
git commit -m "feat: HTML 뉴스레터 및 텍스트 리포트 생성"
```

---

## Task 6: SNS 콘텐츠 생성 (링크드인·스레드·인스타그램)

**Files:**
- Create: `content_generator/linkedin.py`
- Create: `content_generator/threads.py`
- Create: `content_generator/instagram.py`
- Create: `tests/test_sns_generators.py`

**Step 1: 테스트 작성**

`tests/test_sns_generators.py`:

```python
from unittest.mock import MagicMock
from content_generator.linkedin import LinkedInGenerator
from content_generator.threads import ThreadsGenerator
from content_generator.instagram import InstagramGenerator

SAMPLE_DATA = {
    "date": "2026-03-23",
    "trends": "• AI 모델 경쟁 심화\n• 멀티모달 발전\n• 규제 강화",
    "articles": [
        {"title": "GPT-5 출시", "category": "모델 출시", "bullets": ["성능 대폭 향상", "멀티모달 지원"], "implication": "AI 경쟁 격화", "url": "https://x.com/1"},
    ]
}

def _mock_client(text):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    m = MagicMock()
    m.messages.create.return_value = mock_msg
    return m

def test_linkedin_generate_returns_string():
    gen = LinkedInGenerator(client=_mock_client("링크드인 포스트 내용"), model="test")
    result = gen.generate(SAMPLE_DATA)
    assert isinstance(result, str)
    assert len(result) > 0

def test_threads_generate_returns_string():
    gen = ThreadsGenerator(client=_mock_client("스레드 포스트"), model="test")
    result = gen.generate(SAMPLE_DATA)
    assert isinstance(result, str)

def test_instagram_generate_returns_string():
    gen = InstagramGenerator(client=_mock_client("인스타 캡션 #AI"), model="test")
    result = gen.generate(SAMPLE_DATA)
    assert isinstance(result, str)
```

**Step 2: 테스트 실패 확인**

```bash
python -m pytest tests/test_sns_generators.py -v
```
Expected: FAIL

**Step 3: content_generator/linkedin.py 구현**

```python
from typing import Dict

class LinkedInGenerator:
    def __init__(self, client, model: str):
        self._client = client
        self.model = model

    def generate(self, data: Dict) -> str:
        trends = data["trends"]
        date = data["date"]
        titles = "\n".join(f"- {a['title']}" for a in data["articles"][:5])

        prompt = f"""다음 AI 뉴스 트렌드를 바탕으로 링크드인 포스트를 작성하세요.

날짜: {date}
핵심 트렌드:
{trends}

주요 기사:
{titles}

요건:
- 300-600자 한국어
- 전문적이고 인사이트 있는 톤
- 첫 줄이 주목을 끄는 훅
- 번호 목록으로 핵심 3가지
- 마지막에 독자 참여 유도 CTA
- 해시태그 5개 이내 (마지막에)

포스트 내용만 반환:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
```

**Step 4: content_generator/threads.py 구현**

```python
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
```

**Step 5: content_generator/instagram.py 구현**

```python
from typing import Dict

class InstagramGenerator:
    def __init__(self, client, model: str):
        self._client = client
        self.model = model

    def generate(self, data: Dict) -> str:
        trends = data["trends"]
        date = data["date"]
        titles = "\n".join(f"- {a['title']}" for a in data["articles"][:5])

        prompt = f"""다음 AI 뉴스를 바탕으로 인스타그램 캡션을 작성하세요.

날짜: {date}
핵심 트렌드:
{trends}

주요 기사:
{titles}

요건:
- 이모지 풍부하게 (문단마다 1-2개)
- 핵심 내용을 짧은 문단들로
- 마지막 줄 전에 빈 줄
- 마지막: 해시태그 20-25개 (한국어+영어 혼용, #AI #인공지능 #테크뉴스 등 포함)

캡션 내용만 반환:"""

        msg = self._client.messages.create(
            model=self.model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
```

**Step 6: 테스트 통과 확인**

```bash
python -m pytest tests/test_sns_generators.py -v
```
Expected: PASS

**Step 7: Commit**

```bash
git add content_generator/linkedin.py content_generator/threads.py content_generator/instagram.py tests/test_sns_generators.py
git commit -m "feat: SNS 콘텐츠 생성기 (링크드인·스레드·인스타그램)"
```

---

## Task 7: 발행 모듈 (이메일·Notion·SNS 저장)

**Files:**
- Create: `publisher/email_publisher.py`
- Create: `publisher/notion_publisher.py`
- Create: `publisher/sns_exporter.py`

**Step 1: publisher/email_publisher.py 작성**

```python
import resend
from typing import List

class EmailPublisher:
    def __init__(self, api_key: str, from_addr: str, to_addrs: List[str], bcc_addrs: List[str] = None):
        resend.api_key = api_key
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.bcc_addrs = bcc_addrs or []

    def send(self, subject: str, html: str) -> bool:
        if not self.api_key_valid():
            print("[email] API 키 없음 — 건너뜀")
            return False
        try:
            params = {
                "from": self.from_addr,
                "to": self.to_addrs,
                "subject": subject,
                "html": html,
            }
            if self.bcc_addrs:
                params["bcc"] = self.bcc_addrs
            resend.Emails.send(params)
            print(f"[email] 발송 완료 → {self.to_addrs}")
            return True
        except Exception as e:
            print(f"[email] 발송 실패: {e}")
            return False

    def api_key_valid(self) -> bool:
        import resend as r
        return bool(r.api_key)
```

**Step 2: publisher/notion_publisher.py 작성**

```python
from notion_client import Client
from datetime import datetime
from typing import Dict, List

class NotionPublisher:
    def __init__(self, api_key: str, database_id: str):
        self.database_id = database_id
        self._client = Client(auth=api_key) if api_key else None

    def upload(self, date: str, trends: str, articles: List[Dict]) -> bool:
        if not self._client or not self.database_id:
            print("[notion] 설정 없음 — 건너뜀")
            return False
        try:
            blocks = self._build_blocks(trends, articles)
            self._client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"text": {"content": f"AI 뉴스 | {date}"}}]},
                    "Date": {"date": {"start": date}},
                },
                children=blocks[:100],
            )
            # 100개 초과 시 추가 업로드
            if len(blocks) > 100:
                page = self._client.pages.create(
                    parent={"database_id": self.database_id},
                    properties={"Name": {"title": [{"text": {"content": f"AI 뉴스 | {date}"}}]}},
                    children=blocks[:100],
                )
                for i in range(100, len(blocks), 100):
                    self._client.blocks.children.append(page["id"], children=blocks[i:i+100])
            print(f"[notion] 업로드 완료")
            return True
        except Exception as e:
            print(f"[notion] 업로드 실패: {e}")
            return False

    def _build_blocks(self, trends: str, articles: List[Dict]):
        blocks = []
        blocks.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "🔑 오늘의 핵심 트렌드"}}]}})
        for t in trends.split("\n"):
            if t.strip():
                blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": t.lstrip("• ")}}]}})
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        for a in articles:
            blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": a["title"]}}]}})
            for b in a.get("bullets", []):
                blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": b}}]}})
            if a.get("implication"):
                blocks.append({"object": "block", "type": "quote", "quote": {"rich_text": [{"text": {"content": f"💡 {a['implication']}"}}]}})
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": a["url"], "link": {"url": a["url"]}}}]}})
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        return blocks
```

**Step 3: publisher/sns_exporter.py 작성**

```python
from pathlib import Path
from typing import Dict

class SNSExporter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def export(self, date: str, linkedin: str, threads: str, instagram: str):
        day_dir = self.output_dir / date
        day_dir.mkdir(parents=True, exist_ok=True)

        (day_dir / "linkedin.md").write_text(f"# 링크드인 | {date}\n\n{linkedin}\n", encoding="utf-8")
        (day_dir / "threads.md").write_text(f"# 스레드 | {date}\n\n{threads}\n", encoding="utf-8")
        (day_dir / "instagram.md").write_text(f"# 인스타그램 | {date}\n\n{instagram}\n", encoding="utf-8")

        print(f"[sns] SNS 콘텐츠 저장 완료 → {day_dir}")
```

**Step 4: Commit**

```bash
git add publisher/
git commit -m "feat: 발행 모듈 (이메일·Notion·SNS 파일 저장)"
```

---

## Task 8: main.py 파이프라인 통합

**Files:**
- Create: `main.py`
- Create: `tests/test_main_pipeline.py`

**Step 1: 테스트 작성**

`tests/test_main_pipeline.py`:

```python
import pytest
from unittest.mock import patch, MagicMock

def test_main_imports():
    import main  # ImportError 없어야 함

def test_main_preview_mode_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_API_KEY", "test-key")
    monkeypatch.setenv("TRENDS_DIR", str(tmp_path / "trends"))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "output"))

    with patch("collector.rss_collector.RSSCollector.fetch", return_value=[]), \
         patch("collector.gstack_crawler.GstackCrawler.crawl", return_value=[]):
        import sys
        sys.argv = ["main.py", "--preview"]
        import main
        # 기사 0개 → MIN_NEW_ARTICLES 미달로 조용히 종료
```

**Step 2: main.py 작성**

```python
#!/usr/bin/env python3
"""AI 콘텐츠 생성 에이전트 — 메인 파이프라인"""

import sys
import anthropic
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from config.settings import (
    CLAUDE_API_KEY, CLAUDE_MODEL,
    NOTION_API_KEY, NOTION_DATABASE_ID,
    RESEND_API_KEY, EMAIL_FROM, EMAIL_TO, EMAIL_BCC,
    GSTACK_BINARY, TRENDS_DIR, OUTPUT_DIR,
    KR_MAX, GL_MAX, MIN_NEW_ARTICLES, DEDUP_DAYS,
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

PREVIEW = "--preview" in sys.argv


def load_seen_urls(days: int = DEDUP_DAYS) -> set:
    seen = set()
    cutoff = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=days)
    for f in sorted(TRENDS_DIR.glob("trend_*.txt")):
        try:
            date_str = f.stem.replace("trend_", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Seoul"))
            if file_date >= cutoff:
                for line in f.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("http"):
                        seen.add(line.strip())
        except Exception:
            pass
    return seen


def prioritize(articles: list) -> list:
    kr = [a for a in articles if a["region"] == "KR"][:KR_MAX]
    gl = [a for a in articles if a["region"] == "GL"][:GL_MAX]
    return kr + gl


def main():
    KST = ZoneInfo("Asia/Seoul")
    today = datetime.now(KST).strftime("%Y-%m-%d")
    TRENDS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"=== AI 뉴스 파이프라인 | {today} ===\n")

    # 1/8 RSS 수집
    print("1/8 RSS 피드 수집 중...")
    rss = RSSCollector(RSS_FEEDS)
    rss_articles = rss.fetch()
    print(f"    → {len(rss_articles)}개 수집")

    # 2/8 gstack 크롤링
    print("2/8 gstack 크롤링 중...")
    crawler = GstackCrawler(binary_path=GSTACK_BINARY, targets=CRAWL_TARGETS)
    crawled = crawler.crawl()
    print(f"    → {len(crawled)}개 수집")

    # 3/8 중복 제거 + 우선순위
    print("3/8 중복 제거 및 정렬 중...")
    seen = load_seen_urls()
    all_articles = []
    seen_in_run = set()
    for a in rss_articles + crawled:
        if a["url"] not in seen and a["url"] not in seen_in_run:
            seen_in_run.add(a["url"])
            all_articles.append(a)
    articles = prioritize(all_articles)
    print(f"    → 신규 {len(articles)}개 (국내:{sum(1 for a in articles if a['region']=='KR')}, 글로벌:{sum(1 for a in articles if a['region']=='GL')})")

    if len(articles) < MIN_NEW_ARTICLES:
        print(f"\n신규 기사 {len(articles)}개 — {MIN_NEW_ARTICLES}개 미달. 발행 건너뜀.")
        return

    # Claude 클라이언트
    claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    # 4/8 Claude 요약
    print("4/8 Claude 요약 중...")
    summarizer = ClaudeSummarizer(api_key=CLAUDE_API_KEY, model=CLAUDE_MODEL)
    summarized = summarizer.summarize(articles)
    # 요약 결과에 원본 메타 병합
    for i, art in enumerate(summarized):
        if i < len(articles):
            art.setdefault("label", articles[i].get("label", ""))
            art.setdefault("region", articles[i].get("region", ""))
    print(f"    → {len(summarized)}개 요약 완료")

    # 5/8 트렌드 도출
    print("5/8 핵심 트렌드 도출 중...")
    trends = summarizer.generate_trends(articles)
    print(f"    → 트렌드 도출 완료")

    data = {"date": today, "trends": trends, "articles": summarized}

    # 6/8 뉴스레터 생성
    print("6/8 뉴스레터 HTML 생성 중...")
    newsletter_gen = NewsletterGenerator()
    html = newsletter_gen.generate(data)
    txt = newsletter_gen.generate_txt(data)
    trend_file = TRENDS_DIR / f"trend_{today}.txt"
    trend_file.write_text(txt, encoding="utf-8")
    print(f"    → {trend_file} 저장")

    # 7/8 SNS 콘텐츠 생성
    print("7/8 SNS 콘텐츠 생성 중...")
    linkedin_post = LinkedInGenerator(client=claude_client, model=CLAUDE_MODEL).generate(data)
    threads_post = ThreadsGenerator(client=claude_client, model=CLAUDE_MODEL).generate(data)
    instagram_post = InstagramGenerator(client=claude_client, model=CLAUDE_MODEL).generate(data)
    print("    → 링크드인·스레드·인스타그램 생성 완료")

    if PREVIEW:
        print("\n[PREVIEW 모드] 발행 건너뜀.")
        print(f"  뉴스레터: {trend_file}")
        print(f"  SNS 저장 예정: output/{today}/")
        return

    # 8/8 발행
    print("8/8 발행 중...")
    SNSExporter(OUTPUT_DIR).export(today, linkedin_post, threads_post, instagram_post)
    NotionPublisher(NOTION_API_KEY, NOTION_DATABASE_ID).upload(today, trends, summarized)
    EmailPublisher(RESEND_API_KEY, EMAIL_FROM, EMAIL_TO, EMAIL_BCC).send(
        subject=f"🤖 AI 뉴스 | {today}",
        html=html,
    )
    print("\n✅ 파이프라인 완료!")


if __name__ == "__main__":
    main()
```

**Step 3: 테스트 실행**

```bash
python -m pytest tests/ -v
```
Expected: 전체 PASS

**Step 4: 미리보기 실행 테스트 (CLAUDE_API_KEY 필요)**

```bash
python main.py --preview
```
Expected: `신규 기사 N개` 출력 또는 `MIN_NEW_ARTICLES 미달` 메시지

**Step 5: Commit**

```bash
git add main.py tests/test_main_pipeline.py
git commit -m "feat: 8단계 파이프라인 통합 (main.py)"
```

---

## Task 9: GitHub Actions 자동화

**Files:**
- Create: `.github/workflows/ai_news.yml`

**Step 1: 워크플로우 파일 작성**

`.github/workflows/ai_news.yml`:

```yaml
name: AI 뉴스 콘텐츠 에이전트

on:
  schedule:
    - cron: '0 23 * * *'   # 매일 KST 08:00
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GH_PAT }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: 의존성 설치
        run: pip install -r requirements.txt

      - name: 파이프라인 실행
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          EMAIL_BCC: ${{ secrets.EMAIL_BCC }}
        run: python main.py

      - name: 결과 커밋
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add trends/ output/ || true
          git diff --staged --quiet || git commit -m "feat: AI 뉴스 ${{ env.DATE }} 자동 생성"
          git push
        env:
          DATE: $(date +%Y-%m-%d)
```

**Step 2: Commit**

```bash
git add .github/
git commit -m "feat: GitHub Actions 자동화 (매일 KST 08:00)"
```

---

## Task 10: CLAUDE.md 및 README 작성

**Files:**
- Create: `CLAUDE.md`
- Create: `README.md`

**Step 1: CLAUDE.md 작성** — 기존 뉴스아카이빙/CLAUDE.md 참고해서 이 프로젝트 구조에 맞게 작성

핵심 내용:
- 프로젝트 개요, 기술 스택
- 디렉토리 구조 + 각 파일 역할
- 환경변수 목록
- 실행 방법 (`python main.py --preview`, `python main.py`)
- 코드 수정 시 주의사항 (Claude 모델 위치, 피드 추가 방법)

**Step 2: README.md 작성** — 사용자 대상 설치·실행 가이드

**Step 3: 최종 Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: CLAUDE.md 및 README 작성"
```

---

## 전체 테스트 최종 확인

```bash
python -m pytest tests/ -v --tb=short
python main.py --preview
```

두 명령 모두 오류 없이 실행되면 완료.
