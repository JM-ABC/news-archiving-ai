# CLAUDE.md — AI 콘텐츠 생성 에이전트

## 1. 프로젝트 개요

AI 관련 뉴스를 RSS + gstack 브라우저 크롤링으로 자동 수집하고, Claude Haiku API로 요약·분류·트렌드 도출 후 뉴스레터(이메일/Notion)와 SNS 콘텐츠 3종(링크드인·스레드·인스타그램)을 자동 생성하는 에이전트. GitHub Actions로 매일 오전 8시(KST) 자동 실행.

---

## 2. 기술 스택

| 항목 | 상세 |
|---|---|
| Python | 3.12 |
| Claude API | `claude-haiku-4-5-20251001` (요약·SNS 생성) |
| feedparser | RSS 수집 |
| gstack browse | 웹 크롤링 (`~/.claude/skills/gstack/browse/dist/browse`) |
| notion-client | Notion 업로드 |
| resend | 이메일 발송 |
| GitHub Actions | 매일 KST 08:00 자동 실행 |

---

## 3. 디렉토리 구조

```
뉴스아카이빙_AI/
├── main.py                          # 8단계 파이프라인 진입점
├── collector/
│   ├── rss_collector.py             # RSS 피드 수집 (RSSCollector)
│   └── gstack_crawler.py            # gstack 웹 크롤링 (GstackCrawler)
├── summarizer/
│   └── claude_summarizer.py         # 기사 요약 + 트렌드 (ClaudeSummarizer)
├── content_generator/
│   ├── newsletter.py                # HTML 뉴스레터 (NewsletterGenerator)
│   ├── linkedin.py                  # 링크드인 포스트 (LinkedInGenerator)
│   ├── threads.py                   # 스레드 포스트 (ThreadsGenerator)
│   └── instagram.py                 # 인스타그램 캡션 (InstagramGenerator)
├── publisher/
│   ├── email_publisher.py           # 이메일 발송 (EmailPublisher)
│   ├── notion_publisher.py          # Notion 업로드 (NotionPublisher)
│   └── sns_exporter.py              # SNS 파일 저장 (SNSExporter)
├── config/
│   ├── settings.py                  # 환경변수 + 상수
│   └── feeds.py                     # RSS 피드 목록 + 크롤링 대상
├── tests/                           # 단위 테스트
├── output/YYYY-MM-DD/               # SNS 콘텐츠 날짜별 저장
│   ├── linkedin.md
│   ├── threads.md
│   └── instagram.md
├── trends/                          # 뉴스레터 텍스트 날짜별 저장
│   └── trend_YYYY-MM-DD.txt
└── .github/workflows/ai_news.yml    # GitHub Actions
```

---

## 4. 환경변수

| 변수 | 필수 | 설명 |
|---|---|---|
| `CLAUDE_API_KEY` | ✅ | Anthropic API 키 |
| `NOTION_API_KEY` | 선택 | Notion Integration 토큰 |
| `NOTION_DATABASE_ID` | 선택 | Notion Database ID |
| `RESEND_API_KEY` | 선택 | Resend 이메일 API 키 |
| `EMAIL_FROM` | 선택 | 발신자 이메일 |
| `EMAIL_TO` | 선택 | 수신자 이메일 (쉼표 구분) |
| `EMAIL_BCC` | 선택 | BCC 이메일 (쉼표 구분) |
| `GSTACK_BINARY` | 선택 | gstack 바이너리 경로 (자동 탐지) |

---

## 5. 실행 방법

```bash
# 미리보기 (파일 저장만, 이메일·Notion 건너뜀)
python main.py --preview

# 전체 실행 (이메일·Notion 발송 포함)
python main.py
```

### 실행 흐름 (8단계)
```
1/8  RSS 피드 수집
2/8  gstack 보완 크롤링 (OpenAI·Anthropic·DeepMind)
3/8  중복 제거 + 우선순위 정렬 (최대 20개, 국내 13 + 글로벌 7)
4/8  Claude 기사 요약
5/8  핵심 트렌드 도출 (3가지)
6/8  뉴스레터 HTML + TXT 생성
7/8  SNS 콘텐츠 3종 생성
8/8  이메일·Notion 발송 + output/ 저장
```

신규 기사 10개 미만이면 발송 없이 정상 종료.

---

## 6. 코드 수정 시 주의사항

### Claude 모델
- 모든 Claude 호출은 `config/settings.py`의 `CLAUDE_MODEL = "claude-haiku-4-5-20251001"` 참조
- 모델 변경 시 이 한 곳만 수정

### RSS 피드 추가
- `config/feeds.py`의 `RSS_FEEDS` 리스트에 항목 추가
- 형식: `{"label": "이름", "region": "KR|GL", "url": "...", "max": 숫자}`

### gstack 크롤링 대상 추가
- `config/feeds.py`의 `CRAWL_TARGETS` 리스트에 항목 추가
- gstack 바이너리: `~/.claude/skills/gstack/browse/dist/browse` (없으면 `cd ~/.claude/skills/gstack && ./setup` 실행)

### 기사 쿼터
- `KR_MAX = 13`, `GL_MAX = 7` (합계 20개) — `config/settings.py`에서 수정
- `MIN_NEW_ARTICLES = 10` — 최소 발송 기준

### 절대 수정하지 말 것
- `.gitignore`의 `.env` 항목 — 삭제 시 API 키 노출
- `output/`, `trends/` — 자동 생성 폴더, git 추적 제외
