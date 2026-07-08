import re
from html import escape
from typing import Dict

from config.settings import EMAIL_FROM


def _bare_email(addr: str) -> str:
    """"이름 <메일>" 형식(Resend 발신자 포맷)이면 메일 주소만 추출."""
    m = re.search(r"<([^<>]+)>", addr)
    return m.group(1) if m else addr


class NewsletterGenerator:
    # 카테고리별 배지 색 (배경, 글자) — summarize() 프롬프트의 카테고리 값과 매핑
    _CATEGORY_COLORS = {
        "신제품·서비스": ("#dbeafe", "#1e40af"),
        "생활·직장 AI": ("#dcfce7", "#166534"),
        "규제·사회": ("#fef3c7", "#92400e"),
        "기업·산업": ("#ede9fe", "#5b21b6"),
        "연구·기술": ("#cffafe", "#155e75"),
    }
    _CATEGORY_COLOR_DEFAULT = ("#e5e7eb", "#374151")

    def _category_badge(self, category: str, font_size: int = 11) -> str:
        """카테고리별 색상 배지 span."""
        bg, fg = self._CATEGORY_COLORS.get(category, self._CATEGORY_COLOR_DEFAULT)
        return (
            f'<span style="background:{bg};color:{fg};font-size:{font_size}px;font-weight:700;'
            f'padding:2px 8px;letter-spacing:1px;font-family:\'Segoe UI\',Arial,sans-serif;">'
            f"{escape(category)}</span>"
        )

    def select_shown_articles(self, articles):
        """실제로 뉴스레터 본문(HEADLINE + MORE STORIES)에 노출되는 기사만 반환.

        발송 이력(seen_urls.json) 기록도 반드시 이 결과 기준으로 해야 한다 —
        본문에 안 보여준 기사까지 "이미 봤다"고 기록하면 독자가 보지도 못한
        기사가 다음 발행에서도 영영 재등장하지 않는다.
        """
        valid = [a for a in articles if a.get("category") != "기타"]
        if not valid:
            return []
        headline_article = max(valid, key=lambda a: a.get("score", 0))
        more_articles = [a for a in valid if a is not headline_article][:5]
        return [headline_article] + more_articles

    def _section_label(self, text: str) -> str:
        """섹션 구분선 + 레이블 행 (테이블 행 반환)."""
        return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:14px;">
  <tr>
    <td height="2" bgcolor="#111827"></td>
  </tr>
  <tr>
    <td style="padding-top:6px;font-size:11px;font-weight:700;letter-spacing:2px;color:#111827;font-family:'Segoe UI',Arial,sans-serif;">{text}</td>
  </tr>
</table>"""

    def _spacer(self, height: int = 12) -> str:
        """카드 간 여백 행."""
        return f'<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td height="{height}"></td></tr></table>'

    def generate(self, data: Dict) -> str:
        """에디토리얼 매거진 스타일 HTML 뉴스레터 생성."""
        date = escape(data["date"])
        trends_raw = data.get("trends", "")
        articles = data["articles"]
        tip = data.get("tip") or {}

        # 트렌드 배너
        if trends_raw.strip():
            trend_items = [
                t.lstrip("• ").strip()
                for t in trends_raw.split("\n")
                if t.strip() and "핵심 트렌드" not in t and "트렌드 3가지" not in t
            ]
            trends_lines = "<br>".join(
                f'• {escape(t)}'
                for t in trend_items
            )
            trends_banner = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td bgcolor="#374151" style="padding:12px 28px;font-size:12px;letter-spacing:0;color:#e5e7eb;font-family:'Segoe UI',Arial,sans-serif;line-height:1.8;word-break:keep-all;">
      <span style="font-weight:700;">📈 TODAY&#x27;S TRENDS</span><br><span style="font-weight:400;">{trends_lines}</span>
    </td>
  </tr>
</table>"""
        else:
            trends_banner = ""

        # 기사 분류
        shown = self.select_shown_articles(articles)
        headline_article = shown[0] if shown else None
        more_articles = shown[1:]

        # HEADLINE 섹션
        if headline_article:
            a = headline_article
            bullets_html = "".join(
                f"<tr><td style='padding:3px 0;color:#374151;font-size:13px;font-family:\"Segoe UI\",Arial,sans-serif;'>• {escape(b)}</td></tr>"
                for b in a.get("bullets", [])
            )
            headline_html = f"""
{self._section_label("HEADLINE")}
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:22px;">
  <tr>
    <td width="4" bgcolor="#4b5563"></td>
    <td bgcolor="#f5f7fa" style="padding:16px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-bottom:12px;">
            {self._category_badge(a.get('category', ''))}
            &nbsp;
            <span style="color:#9ca3af;font-size:11px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('label', ''))} · {escape(a.get('region', ''))}</span>
          </td>
        </tr>
        <tr>
          <td style="font-size:20px;font-weight:700;color:#111827;line-height:1.4;padding-bottom:12px;font-family:Georgia,'Times New Roman',serif;">{escape(a['title'])}</td>
        </tr>
        <tr>
          <td style="padding-bottom:8px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              {bullets_html}
            </table>
          </td>
        </tr>
        <tr>
          <td style="font-size:12px;color:#6b7280;font-style:italic;padding-bottom:10px;font-family:'Segoe UI',Arial,sans-serif;">👉 {escape(a.get('implication', ''))}</td>
        </tr>
        <tr>
          <td><a href="{escape(a['url'])}" style="font-size:12px;color:#4b5563;font-weight:700;text-decoration:underline;font-family:'Segoe UI',Arial,sans-serif;">원문 보기 →</a></td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""
        else:
            headline_html = ""

        # AI 팁 섹션
        if tip.get("task"):
            task_text = escape(tip["task"])
            if tip.get("difficulty") == "claude-code":
                difficulty_label = "\U0001f4bb Claude Code 앱 필요"
                difficulty_bg, difficulty_fg = "#1e3a8a", "#dbeafe"
            else:
                difficulty_label = "\U0001f310 웹에서 바로 (설치 없음)"
                difficulty_bg, difficulty_fg = "#166534", "#dcfce7"

            tools_html = ""
            if tip.get("tools"):
                tags = "".join(
                    f'<span style="background:#e5e7eb;color:#374151;font-size:11px;font-weight:700;padding:3px 10px;font-family:\'Segoe UI\',Arial,sans-serif;">{escape(t)}</span>&nbsp;'
                    for t in tip["tools"]
                )
                tools_html = f'<tr><td style="padding-bottom:14px;">{tags}</td></tr>'

            steps_html = ""
            if tip.get("steps"):
                step_nums = ["1", "2", "3", "4", "5"]
                rows = ""
                steps_to_render = tip["steps"][:5]
                for i, step in enumerate(steps_to_render):
                    num = step_nums[i]
                    arrow = ""
                    if i < len(steps_to_render) - 1:
                        arrow = '<div style="text-align:center;color:#9ca3af;font-size:13px;line-height:1;margin:2px 0 2px 22px;">↓</div>'
                    rows += f"""
<table cellpadding="0" cellspacing="0" border="0" style="margin-bottom:2px;">
  <tr>
    <td width="24" valign="top" style="padding-right:10px;"><span style="display:block;width:24px;height:24px;background:#111827;color:#fff;font-size:12px;font-weight:700;text-align:center;font-family:'Segoe UI',Arial,sans-serif;line-height:24px;">{num}</span></td>
    <td style="font-size:13px;color:#374151;line-height:1.6;padding-top:4px;font-family:'Segoe UI',Arial,sans-serif;">{escape(step)}</td>
  </tr>
</table>
{arrow}"""
                steps_html = f"""
<tr>
  <td style="padding-bottom:14px;">
    <div style="font-size:11px;font-weight:700;letter-spacing:1px;color:#6b7280;margin-bottom:8px;font-family:'Segoe UI',Arial,sans-serif;">🪜 이렇게 따라하세요</div>
    <div style="background:#ffffff;border:1px solid #e5e7eb;padding:12px 14px;">
      {rows}
    </div>
  </td>
</tr>"""

            prompt_html = ""
            if tip.get("prompt"):
                prompt_html = f"""
<tr>
  <td>
    <div style="font-size:11px;font-weight:700;letter-spacing:1px;color:#6b7280;margin-bottom:6px;font-family:'Segoe UI',Arial,sans-serif;">📋 복붙 프롬프트 — 그대로 붙여넣고 [ ] 부분만 수정하세요</div>
    <div style="background:#111827;padding:14px 16px;font-family:'Courier New',Courier,monospace;font-size:12px;color:#e5e7eb;line-height:1.8;word-break:keep-all;white-space:pre-wrap;">{escape(tip['prompt'])}</div>
  </td>
</tr>"""

            tip_html = f"""
{self._spacer(8)}
{self._section_label("💡 오늘 바로 써먹는 AI 팁")}
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:22px;">
  <tr>
    <td width="4" bgcolor="#6b7280"></td>
    <td bgcolor="#f5f7fa" style="padding:16px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-bottom:12px;">
            <div style="font-size:11px;font-weight:700;letter-spacing:1px;color:#6b7280;margin-bottom:6px;font-family:'Segoe UI',Arial,sans-serif;">✦ 오늘의 자동화 TASK <span style="background:{difficulty_bg};color:{difficulty_fg};padding:3px 9px;margin-left:4px;font-size:11px;font-weight:700;letter-spacing:0;">{escape(difficulty_label)}</span></div>
            <div style="font-size:13px;color:#374151;line-height:1.8;font-family:'Segoe UI',Arial,sans-serif;">{task_text}</div>
          </td>
        </tr>
        {tools_html}
        {steps_html}
        {prompt_html}
      </table>
    </td>
  </tr>
</table>"""
        else:
            tip_html = ""

        # MORE STORIES 섹션
        if more_articles:
            cards = ""
            for i, a in enumerate(more_articles):
                bullets_text = "<br>".join(
                    f"• {escape(b)}" for b in a.get("bullets", [])[:2]
                )
                cards += f"""
{self._spacer(8)}
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td width="3" bgcolor="#d1d5db"></td>
    <td bgcolor="#f5f7fa" style="padding:14px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-bottom:6px;">
            {self._category_badge(a.get('category', ''))}
            &nbsp;
            <span style="color:#9ca3af;font-size:11px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('label', ''))} · {escape(a.get('region', ''))}</span>
          </td>
        </tr>
        <tr>
          <td style="font-size:15px;font-weight:700;color:#111827;line-height:1.4;padding-bottom:6px;font-family:Georgia,'Times New Roman',serif;"><span style="display:inline-block;width:20px;height:20px;background:#111827;color:#ffffff;font-size:11px;font-weight:700;text-align:center;line-height:20px;font-family:'Segoe UI',Arial,sans-serif;margin-right:6px;vertical-align:middle;">{i + 1}</span>{escape(a['title'])}</td>
        </tr>
        <tr>
          <td style="color:#6b7280;font-size:13px;line-height:1.7;font-family:'Segoe UI',Arial,sans-serif;">{bullets_text}</td>
        </tr>
        <tr>
          <td style="padding-top:10px;"><a href="{escape(a['url'])}" style="font-size:12px;color:#4b5563;font-weight:700;text-decoration:underline;font-family:'Segoe UI',Arial,sans-serif;">원문 보기 →</a></td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""
            more_html = f"""
{self._section_label("MORE STORIES")}
{cards}"""
        else:
            more_html = ""

        return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 뉴스 | {date}</title></head>
<body bgcolor="#f5f7fa" style="margin:0;padding:12px;font-family:'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f5f7fa">
  <tr>
    <td align="center" style="padding:12px;">

      <table width="680" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="max-width:680px;">

        <!-- 헤더 -->
        <tr>
          <td bgcolor="#111827" style="padding:24px 28px 18px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td>
                  <div style="font-size:10px;letter-spacing:3px;color:#9ca3af;font-weight:700;margin-bottom:8px;font-family:'Segoe UI',Arial,sans-serif;">DAILY DIGEST</div>
                  <span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#ffffff;font-family:Georgia,'Times New Roman',serif;">AI </span><span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#e5e7eb;font-family:Georgia,'Times New Roman',serif;">NEWS</span>
                </td>
                <td align="right" style="vertical-align:bottom;padding-bottom:4px;">
                  <div style="color:#6b7280;font-size:10px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">VOL. {data.get("issue_no", 1):02d}</div>
                  <div style="color:#9ca3af;font-size:10px;margin-top:2px;font-family:'Segoe UI',Arial,sans-serif;">{date}</div>
                </td>
              </tr>
              <tr>
                <td colspan="2" height="1" bgcolor="#1f2937" style="padding-top:14px;"></td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- 트렌드 배너 -->
        <tr><td>{trends_banner}</td></tr>

        <!-- 콘텐츠 영역 -->
        <tr>
          <td bgcolor="#ffffff" style="padding:22px 28px;">
            {headline_html}
            {more_html}
            {tip_html}
          </td>
        </tr>

        <!-- 푸터 -->
        <tr>
          <td bgcolor="#111827" style="padding:16px 28px;text-align:center;">
            <span style="font-size:16px;font-weight:700;color:#ffffff;font-family:Georgia,'Times New Roman',serif;">AI </span><span style="font-size:16px;font-weight:700;color:#e5e7eb;font-family:Georgia,'Times New Roman',serif;">NEWS</span>
            <div style="color:#4b5563;font-size:10px;letter-spacing:1px;margin-top:4px;font-family:'Segoe UI',Arial,sans-serif;">월·수·금 오전 8시 · AI 뉴스 다이제스트</div>
            <div style="margin-top:8px;"><a href="mailto:{escape(_bare_email(EMAIL_FROM or 'jmyoonkr@gmail.com'))}?subject=수신거부" style="color:#6b7280;font-size:10px;font-family:'Segoe UI',Arial,sans-serif;text-decoration:underline;">수신거부</a></div>
          </td>
        </tr>

      </table>

    </td>
  </tr>
</table>

</body></html>"""

    def generate_txt(self, data: Dict) -> str:
        """텍스트 파일용 리포트 생성."""
        date = data["date"]
        trends = data["trends"]
        articles = data["articles"]

        lines = [f"AI 뉴스 트렌드 | {date}", "---", "", "📈 오늘의 핵심 트렌드", ""]
        lines += [t for t in trends.split("\n") if t.strip()]
        lines += ["", "---"]

        for i, a in enumerate(articles, 1):
            lines.append(f"\n{i}. {a['title']}")
            lines.append(f"   출처: {a.get('label', '')} ({a.get('region', '')})")
            for b in a.get("bullets", []):
                lines.append(f"   - {b}")
            lines.append(f"\n   👉 {a.get('implication', '')}")
            lines.append(f"\n   원문: {a['url']}")
            lines.append("---")

        return "\n".join(lines)
