# CLAUDE.md — AI 콘텐츠 생성 에이전트

## 1. 프로젝트 개요

AI 관련 뉴스를 RSS + gstack 브라우저 크롤링으로 자동 수집하고, Claude Haiku API로 요약·분류·트렌드·실용 팁 도출 후 HTML 뉴스레터를 이메일(Resend)·Notion으로 발행하는 에이전트. GitHub Actions로 **월·수·금 오전 8시(KST)** 자동 실행. SNS 콘텐츠 3종(링크드인·스레드·인스타그램) 생성 기능은 현재 비활성화 상태.

---

## 2. 기술 스택

| 항목 | 상세 |
|---|---|
| Python | 3.12 |
| Claude API | `claude-haiku-4-5-20251001` (요약·트렌드·팁 생성) |
| feedparser | RSS 수집 |
| gstack browse | 웹 크롤링 (`~/.claude/skills/gstack/browse/dist/browse`) |
| notion-client | Notion 업로드 |
| resend | 이메일 발송 + 헬스체크 알림 |
| GitHub Actions | 월·수·금 KST 08:00 자동 실행 (`cron: 0 23 * * 0,2,4` UTC) |

의존성은 `requirements.txt`에 정확한 버전으로 고정되어 있다. 업그레이드 시 테스트 통과 확인 후 버전 갱신.

---

## 3. 디렉토리 구조

```
뉴스아카이빙_AI/
├── main.py                          # 8단계 파이프라인 진입점
├── collector/
│   ├── rss_collector.py             # RSS 수집 + AI 키워드·날짜 필터 (RSSCollector)
│   ├── gstack_crawler.py            # gstack 웹 크롤링 (GstackCrawler)
│   └── seen_store.py                # 발송 이력 상태 저장소 (seen_urls.json)
├── summarizer/
│   └── claude_summarizer.py         # 요약 + 트렌드 + 팁 (ClaudeSummarizer)
├── content_generator/
│   ├── newsletter.py                # HTML 뉴스레터, 아웃룩 호환 테이블 기반 (NewsletterGenerator)
│   ├── linkedin.py / threads.py / instagram.py   # SNS 생성기 (현재 비활성화)
├── publisher/
│   ├── email_publisher.py           # 이메일 발송 (EmailPublisher)
│   ├── notion_publisher.py          # Notion 업로드 (NotionPublisher)
│   └── sns_exporter.py              # SNS 파일 저장 (비활성화)
├── scripts/
│   └── healthcheck.py               # 중단 감지·실패 알림·피드 점검
├── config/
│   ├── settings.py                  # 환경변수 + 상수
│   └── feeds.py                     # RSS 피드 목록 + 크롤링 대상
├── tests/                           # 단위 테스트 (pytest)
├── trends/                          # git 제외 (seen_urls.json·issue_count.txt만 예외로 커밋)
│   ├── trend_YYYY-MM-DD.txt         # 발행 텍스트
│   ├── newsletter_YYYY-MM-DD.html   # --preview 시 생성
│   ├── seen_urls.json               # 발송 이력 (URL→날짜, 30일 보존) ★커밋됨
│   ├── issue_count.txt              # 발행 호수(VOL.) 누적 카운터 ★커밋됨
│   └── last_tip_category.txt        # 팁 카테고리 연속 반복 방지
├── output/YYYY-MM-DD/               # SNS 콘텐츠 (비활성화, git 제외)
└── .github/workflows/ai_news.yml    # GitHub Actions
```

---

## 4. 환경변수

| 변수 | 필수 | 설명 |
|---|---|---|
| `CLAUDE_API_KEY` | ✅ | Anthropic API 키 |
| `NOTION_API_KEY` / `NOTION_DATABASE_ID` | 선택 | Notion 연동 |
| `NOTION_ENABLED` | 선택 | `false`(기본) 외 값이면 Notion 업로드 |
| `RESEND_API_KEY` | 선택 | Resend 이메일 API 키 |
| `EMAIL_FROM` / `EMAIL_TO` / `EMAIL_BCC` | 선택 | 발신·수신·BCC (쉼표 구분) |
| `EMAIL_ENABLED` | 선택 | `false`(기본) 외 값이면 이메일 발송 |
| `GSTACK_BINARY` | 선택 | gstack 바이너리 경로 (자동 탐지) |

---

## 5. 실행 방법

```bash
# 미리보기 (trends/에 HTML 저장 + 브라우저 오픈, 발송·이력 기록 없음)
python main.py --preview

# 전체 실행 (발행 성공 시에만 seen_urls.json에 이력 기록)
python main.py

# 주제 각도 직접 선택
python main.py --interactive

# 헬스체크
python scripts/healthcheck.py --check-feeds        # 피드 생존 점검
python scripts/healthcheck.py --check-stale        # 발행 중단 감지 (기본 8일)
```

### 실행 흐름 (8단계)
```
1/8  RSS 피드 수집 (AI 키워드 + 최근 4일 필터)
2/8  gstack 보완 크롤링 (OpenAI·Anthropic·DeepMind)
3/8  중복 제거(seen_urls.json) + 우선순위 정렬 (국내 13 + 글로벌 7)
4/8  Claude 기사 요약
5/8  핵심 트렌드 도출 + AI 팁 생성 (카테고리 연속 반복 방지)
6/8  뉴스레터 HTML + TXT 생성
7/8  SNS 콘텐츠 생성 — 현재 건너뜀 (비활성화)
8/8  이메일·Notion 발행 → 성공 시 발송 이력 기록
```

신규 기사 10개 미만이면 발송 없이 정상 종료 (이력 기록도 안 함).

### 테스트
```bash
python -m pytest tests/ -q
```
CI(GitHub Actions)에서도 파이프라인 실행 전 테스트가 게이트로 돈다.

---

## 6. 운영 주의사항 (침묵 장애 방지)

- **GitHub는 60일간 저장소 활동이 없으면 스케줄 워크플로를 자동 비활성화한다.**
  워크플로가 매 실행 `.github/.heartbeat`를 커밋해 이를 방지하지만, 수동으로 꺼진 경우
  Actions 탭에서 "Enable workflow"로 재활성화해야 한다.
- 워크플로 실패 시 `--notify-failure`가, 8일 이상 발행 없으면 `--check-stale`이
  이메일 경고를 보낸다 (경고 메일에 피드 진단 리포트 포함).
- 발행이 계속 건너뛰어지면(기사 미달) 피드가 죽었을 가능성이 크다 → `--check-feeds`로 확인.

---

## 7. 코드 수정 시 주의사항

### Claude 모델
- 모든 Claude 호출은 `config/settings.py`의 `CLAUDE_MODEL` 참조. 모델 변경 시 이 한 곳만 수정.

### RSS 피드 추가
- `config/feeds.py`의 `RSS_FEEDS`에 추가. 형식: `{"label": "이름", "region": "KR|GL", "url": "...", "max": 숫자}`
- 추가 후 `python scripts/healthcheck.py --check-feeds`로 생존 확인. RSS 후보 URL은 절대
  추측하지 말고 실제로 다운로드해서 `<item>`/`<entry>`가 있는지, 최근 글 날짜가 파싱되는지
  확인할 것 — 검색 결과에 나온 URL도 죽어있거나(410 등) 빈 피드인 경우가 흔하다.

### 대형 AI 플랫폼(OpenAI·Google·Microsoft·Anthropic) 소식 우선순위
- `config/feeds.py`의 `MAJOR_PLATFORM_LABELS`에 라벨을 등록하면 `main.py`의 `prioritize()`가
  글로벌(GL) 쿼터 안에서 해당 라벨 기사를 먼저 채운다 (안정 정렬, 헤드라인 점수는 안 건드림 —
  "일반 독자 유용성" 판단은 여전히 `summarize()`의 Claude 채점에 맡긴다).
- 현재 등록된 소스: `OpenAI News`, `Google DeepMind`, `Google AI Blog`, `Microsoft AI News`
  (모두 공식 RSS), `Anthropic News (비공식)` — **Anthropic은 공식 RSS가 없어 커뮤니티가
  매일 스크래핑하는 비공식 피드를 씀. 예고 없이 끊길 수 있으니 healthcheck로 주기적 확인 필요.**
- Google DeepMind·Microsoft AI News는 발행 주기가 느려 `--check-feeds`의 4일 윈도우에서
  종종 `stale_feed`로 뜨는데, 발행 주기(월·수·금)와 겹치면 대부분 잡히므로 이 자체는 문제
  아님 — 며칠 연속 0개일 때만 실제 이상으로 본다.

### gstack 크롤링 대상 추가
- `config/feeds.py`의 `CRAWL_TARGETS`에 추가.
- **현재 GitHub Actions 워크플로에 gstack 설치 스텝이 없어 CI에서는 `CRAWL_TARGETS`가
  항상 0개를 반환한다** (로컬에 바이너리 없을 때도 동일 — `GSTACK_BINARY`가 `None`이면
  조용히 건너뜀). gstack 바이너리 없으면 `cd ~/.claude/skills/gstack && ./setup` 실행,
  CI에서 실제로 쓰려면 워크플로에 설치 스텝을 추가해야 한다. OpenAI·Google DeepMind는
  이 문제 때문에 위 RSS_FEEDS로 대체했다.

### 기사 쿼터
- `KR_MAX = 13`, `GL_MAX = 7`, `MIN_NEW_ARTICLES = 10` — `config/settings.py`에서 수정.

### 중복 제거 (seen_store)
- `trends/seen_urls.json`이 유일한 발송 이력 소스 (30일 보존, 이메일 발송 성공 시에만 기록).
- `trends/issue_count.txt`는 뉴스레터 VOL. 번호용 누적 카운터 — 30일 보존 대상이 아니므로
  seen_urls.json과 별도 파일로 관리한다 (seen_urls.json에 넣으면 30일 뒤 VOL. 번호가 되돌아간다).
- 두 파일 모두 gitignore 예외로 CI에서 커밋된다 — `.gitignore`는 `trends/*`로 디렉토리 내용을
  제외한 뒤 `!trends/seen_urls.json`·`!trends/issue_count.txt`로 재포함한다. **`trends/`(디렉토리
  전체 제외)로 되돌리면 Git이 하위 파일을 negation으로 되살릴 수 없어 예외가 무력화된다.**

### 절대 수정하지 말 것
- `.gitignore`의 `.env` 항목 — 삭제 시 API 키 노출
- `.gitignore`의 `trends/*` + `!trends/seen_urls.json` + `!trends/issue_count.txt` 예외 —
  `trends/*`를 `trends/`로 바꾸거나 예외 줄을 지우면 CI 중복 제거·발행 호수가 무력화된다
- 워크플로의 하트비트 커밋 스텝(`.github/.heartbeat`) — 삭제 시 60일 후 cron 자동 비활성화
- 워크플로 파이프라인 실행 env의 `EMAIL_ENABLED: "true"` — 삭제 시 CI가 이메일을 조용히
  보내지 않으면서도 정상 종료된 것처럼 보인다
