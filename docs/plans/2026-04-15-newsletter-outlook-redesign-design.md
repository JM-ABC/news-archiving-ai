# 뉴스레터 아웃룩 호환 테이블 기반 재설계

**Date:** 2026-04-15  
**Status:** Approved  
**File:** `content_generator/newsletter.py`

---

## 배경

현재 `NewsletterGenerator.generate()`는 `<div>` + CSS 기반 HTML을 생성한다.
아웃룩(Outlook)에서 다음 문제가 발생한다:

- `display:flex` 미지원 → 레이아웃 깨짐
- `box-shadow`, `border-radius` 무시 → 카드 경계 사라짐
- `background:` CSS 속성 불안정 → 배경색 렌더링 실패
- `rgba()` 미지원 → 투명 구분선 무시

**목표:** 아웃룩/Gmail/모바일 등 다양한 클라이언트에서 일관된 렌더링 + 기존 다크 매거진 스타일 유지

---

## 설계

### 전체 구조

```
<body bgcolor="#f5f7fa">
  [외부 래퍼 table — bgcolor="#f5f7fa", width="100%"]
    [메인 컨테이너 table — width="680", bgcolor="#ffffff"]
      Row 1: 헤더 (bgcolor="#111827")
      Row 2: 트렌드 배너 (bgcolor="#374151")
      Row 3: 콘텐츠 영역 (bgcolor="#ffffff", padding: 22px 28px)
      Row 4: 푸터 (bgcolor="#111827")
```

### Section 1: 헤더

- `<table width="100%" bgcolor="#111827">`
- 좌/우 분리: 내부 `<table width="100%"><tr><td>좌</td><td align="right">우</td></tr></table>`
- 구분선: `height="1"` td + `bgcolor="#1f2937"` (rgba 대신 고정색)

### Section 2: 트렌드 배너

- `<table width="100%" bgcolor="#374151">`
- `padding:10px 28px`, `font-size:9px`, `color:#e5e7eb`
- 트렌드 항목은 `<br>` 구분

### Section 3: 콘텐츠 카드

공통 패턴 — 포인트 바 + 내용:
```
<table width="100%" bgcolor="#f5f7fa">
  <tr>
    <td width="4" bgcolor="{포인트색}"></td>  ← 좌측 컬러 바
    <td style="padding:16px;">내용</td>
  </tr>
</table>
```

| 카드 | 포인트 바 색 | 배경 |
|---|---|---|
| HEADLINE | `#4b5563` | `#f5f7fa` |
| MORE STORIES | `#d1d5db` (3px) | `#f5f7fa` |
| AI 팁 | `#6b7280` | `#f5f7fa` |

- AI 팁 내 단계 박스: `bgcolor="#ffffff"`, 테두리 `border:1px solid #e5e7eb`
- AI 팁 내 프롬프트 박스: `bgcolor="#111827"`, 흰색 monospace 텍스트
- 카드 간 여백: `height="12"` 빈 행

### Section 4: 푸터

- `<table width="100%" bgcolor="#111827">`
- `align="center"`, `padding:16px 28px`
- "AI NEWS" + 발행 주기 문구

---

## 아웃룩 호환 체크리스트

| 항목 | 처리 방식 |
|---|---|
| 배경색 | `bgcolor=` HTML 속성 사용 |
| 레이아웃 | 중첩 `<table>` |
| 여백 | `cellpadding` / 빈 `<td>` 스페이서 |
| 구분선 | `height="1"` td + `bgcolor` |
| `rgba()` | 불투명 고정색으로 대체 |
| `flex` | `<table>` 중첩으로 대체 |
| `box-shadow` | 제거 |
| `border-radius` | 제거 |

---

## 유지되는 디자인 요소

- 다크 헤더/푸터: `#111827`
- 트렌드 배너: `#374151`
- 카드 배경: `#f5f7fa` (통일)
- 폰트: `'Segoe UI',Arial,sans-serif` / `Georgia,'Times New Roman',serif`
- 최대 너비: 680px
