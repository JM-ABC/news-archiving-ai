# AI 콘텐츠 생성 에이전트 — 설계 문서

**날짜:** 2026-03-23
**프로젝트:** 뉴스아카이빙_AI
**상태:** 승인됨

---

## 1. 개요

AI 관련 뉴스를 RSS + gstack 브라우저로 자동 수집하고, Claude API로 요약·트렌드 도출 후 뉴스레터(이메일/Notion)와 SNS 콘텐츠 3종(링크드인·스레드·인스타그램)을 생성하는 자동화 파이프라인.

---

## 2. 기술 스택

| 항목 | 선택 | 비고 |
|---|---|---|
| Python | 3.12 | 기존 뉴스아카이빙과 동일 |
| Claude API | `claude-haiku-4-5-20251001` | 비용 절감, 전 모듈 통일 |
| feedparser | RSS 수집 | |
| gstack browse | 웹 크롤링 | `~/.claude/skills/gstack/browse/dist/browse` |
| notion-client | Notion 업로드 | |
| resend | 이메일 발송 | |
| GitHub Actions | 자동화 | 매일 KST 08:00 |

---

## 3. 디렉토리 구조

```
뉴스아카이빙_AI/
├── main.py                          # 파이프라인 진입점
├── collector/
│   ├── __init__.py
│   ├── rss_collector.py             # RSS 피드 수집
│   └── gstack_crawler.py            # gstack 웹 크롤링
├── summarizer/
│   ├── __init__.py
│   └── claude_summarizer.py         # 기사 요약 + 트렌드 도출
├── content_generator/
│   ├── __init__.py
│   ├── newsletter.py                # HTML 뉴스레터 생성
│   ├── linkedin.py                  # 링크드인 포스트 생성
│   ├── threads.py                   # 스레드 포스트 생성
│   └── instagram.py                 # 인스타그램 캡션 + 해시태그 생성
├── publisher/
│   ├── __init__.py
│   ├── notion_publisher.py          # Notion 업로드
│   ├── email_publisher.py           # Resend 이메일 발송
│   └── sns_exporter.py              # SNS 콘텐츠 파일 저장
├── config/
│   ├── feeds.py                     # RSS 피드 목록
│   └── settings.py                  # 환경변수 로드
├── output/                          # SNS 콘텐츠 날짜별 저장
│   └── YYYY-MM-DD/
│       ├── linkedin.md
│       ├── threads.md
│       └── instagram.md
├── trends/                          # 뉴스레터 날짜별 텍스트 저장
│   └── trend_YYYY-MM-DD.txt
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── CLAUDE.md
├── README.md
└── .github/workflows/ai_news.yml
```

---

## 4. 수집 소스

### RSS 피드

| 구분 | 소스 | URL |
|---|---|---|
| 글로벌 | TechCrunch AI | https://techcrunch.com/category/artificial-intelligence/feed/ |
| 글로벌 | MIT Technology Review | https://www.technologyreview.com/feed/ |
| 글로벌 | The Verge AI | https://www.theverge.com/rss/ai-artificial-intelligence/index.xml |
| 글로벌 | VentureBeat AI | https://venturebeat.com/category/ai/feed/ |
| 글로벌 | Wired AI | https://www.wired.com/feed/tag/ai/latest/rss |
| 국내 | 전자신문 AI | https://www.etnews.com/rss/section.xml?id=13 |
| 국내 | ZDNet Korea | https://www.zdnet.co.kr/rss/news.xml |
| 국내 | AI타임스 | https://www.aitimes.com/rss/allArticle.xml |

### gstack 크롤링 대상 (RSS 없거나 불안정)

| 사이트 | URL | 이유 |
|---|---|---|
| OpenAI Blog | https://openai.com/news | 공식 발표, RSS 불안정 |
| Anthropic Blog | https://www.anthropic.com/news | 공식 발표 |
| Google DeepMind | https://deepmind.google/discover/blog/ | 연구 성과 |

---

## 5. 데이터 흐름

```
1/8  RSS 피드 수집        (rss_collector.py)
2/8  gstack 보완 크롤링   (gstack_crawler.py)
3/8  중복 제거 + 정렬     (main.py — 최대 20개, 국내 13 + 글로벌 7)
4/8  Claude 기사 요약     (claude_summarizer.py)
5/8  핵심 트렌드 도출     (claude_summarizer.py — 3가지)
6/8  뉴스레터 HTML 생성   (newsletter.py)
7/8  SNS 콘텐츠 3종 생성  (linkedin.py / threads.py / instagram.py)
8/8  발행                 (email_publisher + notion_publisher + sns_exporter)
```

최소 기사 기준: 10개 미만이면 발송 없이 종료 (`MIN_NEW_ARTICLES = 10`)

---

## 6. SNS 콘텐츠 포맷

### 링크드인
- 길이: 300–600자
- 톤: 전문적, 인사이트 중심
- 구조: 훅 문장 → 번호 목록 (핵심 3가지) → CTA

### 스레드 (Threads)
- 길이: 500자 이내
- 톤: 대화체, 질문 훅
- 구조: 임팩트 있는 첫 문장 → 핵심 내용 → 질문으로 마무리

### 인스타그램
- 캡션: 최대 2200자
- 이모지 풍부하게 사용
- 해시태그: 20–30개 (AI 관련 + 한국어 혼용)

SNS 콘텐츠는 자동 발행 없이 `output/YYYY-MM-DD/` 폴더에 마크다운으로 저장 (수동 복붙).

---

## 7. 환경변수

| 변수 | 필수 | 설명 |
|---|---|---|
| `CLAUDE_API_KEY` | ✅ | Anthropic API 키 |
| `NOTION_API_KEY` | 선택 | Notion Integration 토큰 |
| `NOTION_DATABASE_ID` | 선택 | Notion Database ID |
| `RESEND_API_KEY` | 선택 | Resend 이메일 API 키 |
| `EMAIL_FROM` | 선택 | 발신자 이메일 |
| `EMAIL_TO` | 선택 | 수신자 이메일 (쉼표 구분) |
| `EMAIL_BCC` | 선택 | BCC 이메일 (쉼표 구분) |
| `GSTACK_BINARY` | 선택 | gstack 바이너리 경로 (기본값 자동 탐지) |

---

## 8. 자동화

- **GitHub Actions**: `.github/workflows/ai_news.yml`
- **스케줄**: `cron: '0 23 * * *'` (매일 UTC 23:00 = KST 08:00)
- **수동 실행**: `workflow_dispatch`
- **실행 후**: `trends/` 변경사항 자동 커밋·푸시

---

## 9. 실행 방법

```bash
# 일반 실행
python main.py

# 미리보기 (이메일·Notion 건너뜀)
python main.py --preview
```

---

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 0 | — | — |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |

**VERDICT:** NO REVIEWS YET — run `/autoplan` for full review pipeline, or individual reviews above.
