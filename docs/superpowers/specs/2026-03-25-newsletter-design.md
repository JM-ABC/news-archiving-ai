# 뉴스레터 HTML 디자인 리뉴얼 스펙

## 목표

`content_generator/newsletter.py`의 `generate(self, data: Dict) -> str` 메서드가 반환하는 HTML을 에디토리얼 매거진 스타일로 교체한다. 시그니처와 반환 타입은 기존과 동일하게 유지한다.

---

## 디자인 방향

- **스타일:** 에디토리얼 매거진
- **색상:** 다크 헤더 `#111827` + 에메랄드 그린 `#10b981` 포인트
- **타이포그래피:** `AI NEWS` 한 줄 나란히, `AI ` 흰색 + `NEWS` 그린 (`#10b981`)
- **레이아웃:** 단일 컬럼 680px, 인라인 CSS 전용 (`<style>` 태그 없음), JavaScript 없음, 외부 폰트 없음

---

## 섹션 구조

### 1. 헤더 (`#111827` 배경)
- `DAILY DIGEST` 라벨 (9px, 3px 자간, `#6ee7b7`)
- 타이틀: `AI ` (흰색, 공백 포함) + `NEWS` (`#10b981`), 34px font-weight 900, 한 줄
- 우측 정렬: `VOL. 01` (하드코딩 고정값) + 날짜
- 하단 그린 그라디언트 구분선 (`#10b981` → `#059669` → transparent). Gmail 등 그라디언트 미지원 클라이언트에서는 선이 보이지 않아도 허용 (폴백 처리 불필요)

### 2. 트렌드 배너 (`#10b981` 배경)
- `🔑 TODAY'S TRENDS` + 트렌드 텍스트
- 트렌드 파싱: `data["trends"]` 문자열을 `\n`으로 split → 각 줄에서 `"• "` prefix 제거 → 비어있지 않은 줄을 ` · ` 구분자로 연결하여 한 줄로 표시
- `data["trends"]`가 빈 문자열이면 배너 전체를 생략

### 3. HEADLINE 섹션
- 섹션 제목: `HEADLINE` (검정 2px 하단 보더, 9px 대문자 레터스페이싱)
- 기사 선정: `category != "기타"`인 기사들 중 첫 번째. 해당 기사가 없으면 HEADLINE 섹션 전체 생략
- 카드: 연회색 배경 `#f8fafc` + 좌측 4px 그린 보더 (`#10b981`)
- 카테고리 태그: 검정 배경(`#111827`) + 그린 텍스트(`#10b981`), 8px
- 출처 표시: `{label} · {region}` (9px, `#9ca3af`)
- 제목: 14px font-weight 800
- 불릿: `bullets` 전체 3개를 `<ul><li>`로 표시
- 시사점: `implication` italic, 👉 prefix
- 원문 링크: `url`

### 4. MORE STORIES 섹션
- 섹션 제목: `MORE STORIES` (동일 스타일)
- 기사: HEADLINE에 사용된 기사를 제외한 나머지 중 `category != "기타"` 기사 전체
- 해당 기사가 없으면 MORE STORIES 섹션 전체 생략
- 카드: 배경 없음, 1px `#e5e7eb` 하단 보더 구분 (마지막 기사는 보더 없음)
- 카테고리 태그: 연회색 배경 `#f3f4f6` + 다크 텍스트 `#374151`
- 출처 표시: `{label} · {region}` (9px, `#9ca3af`)
- 제목: 12px font-weight 700
- 불릿: `bullets[:2]` (처음 2개만 `<br>` 구분 텍스트로 표시, `<ul>` 아닌 `•` prefix)
- `implication` 및 원문 링크(`url`): **표시하지 않음** (간결한 카드 디자인 유지)

### 5. 푸터 (`#111827` 배경)
- 타이틀 `AI NEWS` 소형 반복 (헤더와 동일 색상 규칙, 16px)
- 부제: "매일 오전 8시 · AI 뉴스 다이제스트" (8px, `#4b5563`)

---

## 데이터 필드 참조

각 기사 딕셔너리에서 사용하는 필드:

| 필드 | 출처 | 비고 |
|---|---|---|
| `title` | ClaudeSummarizer | 한국어 제목 |
| `category` | ClaudeSummarizer | 기타 필터링에 사용 |
| `bullets` | ClaudeSummarizer | 리스트, 최대 3개 |
| `implication` | ClaudeSummarizer | 시사점 문자열 |
| `url` | ClaudeSummarizer | 원문 URL |
| `label` | main.py setdefault | 출처명 |
| `region` | main.py setdefault | KR 또는 GL |

---

## 구현 범위

- **수정 파일:** `content_generator/newsletter.py`
- **수정 메서드:** `generate()` 전체 교체
- **`generate_txt()`:** 변경 없음
- **보안:** 모든 동적 데이터에 `escape()` 유지 (XSS 방어)
- **Outlook 호환:** 별도 조건부 주석 불필요 (사용자 환경 Gmail 기준)
- **다크 모드:** 별도 대응 없음

---

## 엣지 케이스

| 상황 | 처리 |
|---|---|
| 모든 기사가 "기타" | HEADLINE + MORE STORIES 모두 생략, 헤더+배너+푸터만 렌더링 |
| `data["trends"]`가 빈 문자열 | 트렌드 배너 섹션 생략 |
| `bullets`가 3개 미만 | 있는 만큼만 표시 |
| `label` 또는 `region` 없음 | `a.get('label', '')` 패턴으로 빈 문자열 폴백 |
