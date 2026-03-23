# AI 뉴스 콘텐츠 에이전트

AI 관련 뉴스를 자동 수집·요약하고, 뉴스레터와 SNS 콘텐츠를 자동 생성하는 파이프라인.

---

## 주요 기능

- **뉴스 수집**: RSS 피드 + gstack 브라우저 크롤링 (OpenAI·Anthropic·DeepMind 블로그 포함)
- **AI 요약**: Claude Haiku로 각 기사를 카테고리 분류 + 한국어 요약 생성
- **핵심 트렌드**: 당일 뉴스를 종합한 트렌드 3가지 자동 도출
- **뉴스레터**: HTML 이메일 + Notion 업로드
- **SNS 콘텐츠**: 링크드인·스레드·인스타그램용 포스트 자동 생성
- **자동 실행**: GitHub Actions로 매일 오전 8시(KST) 자동 실행

---

## AI 뉴스 커버리지

| 구분 | 소스 |
|---|---|
| 글로벌 RSS | TechCrunch AI, MIT Tech Review, The Verge AI, VentureBeat AI, Wired AI |
| 국내 RSS | 전자신문 AI, ZDNet Korea, AI타임스 |
| gstack 크롤링 | OpenAI Blog, Anthropic Blog, Google DeepMind Blog |

---

## 설치

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 CLAUDE_API_KEY 등 값 입력
```

### 환경변수

| 변수 | 필수 | 설명 |
|---|---|---|
| `CLAUDE_API_KEY` | ✅ | Anthropic API 키 |
| `NOTION_API_KEY` | 선택 | Notion Integration 토큰 |
| `NOTION_DATABASE_ID` | 선택 | Notion Database ID |
| `RESEND_API_KEY` | 선택 | Resend 이메일 API 키 |
| `EMAIL_FROM` | 선택 | 발신자 이메일 |
| `EMAIL_TO` | 선택 | 수신자 이메일 (쉼표로 다수 지정) |
| `EMAIL_BCC` | 선택 | BCC 이메일 |

---

## 실행

```bash
# 미리보기 (파일 저장만, 이메일·Notion 건너뜀)
python main.py --preview

# 전체 실행
python main.py
```

---

## 출력 구조

```
trends/
└── trend_2026-03-24.txt   # 뉴스레터 텍스트

output/2026-03-24/
├── linkedin.md            # 링크드인 포스트
├── threads.md             # 스레드 포스트
└── instagram.md           # 인스타그램 캡션 + 해시태그
```

SNS 콘텐츠는 파일로 저장됩니다. 복붙해서 직접 게시하세요.

---

## 자동 실행 (GitHub Actions)

저장소 Settings → Secrets에 환경변수 등록 후 매일 **오전 8시(KST)** 자동 실행.

수동 실행: Actions 탭 → `AI 뉴스 콘텐츠 에이전트` → **Run workflow**

---

## 기술 스택

- **Python 3.12**
- **Claude API** (claude-haiku-4-5) — 요약·트렌드·SNS 생성
- **gstack browse** — 헤드리스 브라우저 크롤링
- **feedparser** — RSS 수집
- **notion-client** — Notion 업로드
- **resend** — 이메일 발송
- **GitHub Actions** — 스케줄 자동화
