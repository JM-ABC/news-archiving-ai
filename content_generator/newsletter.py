from html import escape
from urllib.parse import quote
from typing import Dict


class NewsletterGenerator:
    def generate(self, data: Dict) -> str:
        """에디토리얼 매거진 스타일 HTML 뉴스레터 생성."""
        date = escape(data["date"])
        trends_raw = data.get("trends", "")
        articles = data["articles"]
        tip = data.get("tip", "")
        email_from = data.get("email_from", "")

        # 트렌드 배너
        if trends_raw.strip():
            trend_items = [
                t.lstrip("• ").strip()
                for t in trends_raw.split("\n")
                if t.strip()
            ]
            trends_inline = escape(" · ".join(trend_items))
            trends_banner = f"""
<div style="background:#10b981;padding:10px 32px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#fff;">🔑 TODAY'S TRENDS &nbsp;·&nbsp; </span>
  <span style="color:rgba(255,255,255,0.75);font-size:9px;">{trends_inline}</span>
</div>"""
        else:
            trends_banner = ""

        # 기사 분류
        valid = [a for a in articles if a.get("category") != "기타"]
        headline_article = valid[0] if valid else None
        more_articles = valid[1:] if len(valid) > 1 else []

        # HEADLINE 섹션
        if headline_article:
            a = headline_article
            bullets_html = "".join(
                f"<li style='margin-bottom:4px;'>{escape(b)}</li>"
                for b in a.get("bullets", [])
            )
            headline_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;">HEADLINE</span>
</div>
<div style="margin-bottom:20px;padding:16px;background:#f8fafc;border-radius:4px;border-left:4px solid #10b981;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
    <span style="background:#111827;color:#10b981;font-size:8px;font-weight:700;padding:2px 8px;border-radius:2px;letter-spacing:1px;">{escape(a.get('category',''))}</span>
    <span style="color:#9ca3af;font-size:9px;">{escape(a.get('label',''))} · {escape(a.get('region',''))}</span>
  </div>
  <div style="font-size:14px;font-weight:800;color:#111827;line-height:1.3;margin-bottom:8px;">{escape(a['title'])}</div>
  <ul style="margin:0 0 8px;padding-left:16px;color:#374151;font-size:11px;line-height:1.7;">{bullets_html}</ul>
  <div style="font-size:10px;color:#6b7280;font-style:italic;margin-bottom:8px;">👉 {escape(a.get('implication',''))}</div>
  <a href="{escape(a['url'])}" style="font-size:10px;color:#10b981;font-weight:700;text-decoration:none;">원문 보기 →</a>
</div>"""
        else:
            headline_html = ""

        # AI 팁 섹션
        if tip.strip():
            tip_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;">💡 오늘 바로 써먹는 AI 팁</span>
</div>
<div style="margin-bottom:20px;padding:16px;background:#fffbeb;border-radius:4px;border-left:4px solid #f59e0b;">
  <p style="margin:0;font-size:12px;color:#374151;line-height:1.7;">{escape(tip)}</p>
</div>"""
        else:
            tip_html = ""

        # MORE STORIES 섹션
        if more_articles:
            cards = ""
            for i, a in enumerate(more_articles):
                is_last = i == len(more_articles) - 1
                border = "" if is_last else "border-bottom:1px solid #e5e7eb;"
                bullets_text = "<br>".join(
                    f"• {escape(b)}" for b in a.get("bullets", [])[:2]
                )
                vote_link = ""
                if email_from:
                    vote_link = (
                        f'<a href="mailto:{escape(email_from)}'
                        f'?subject={quote("AI뉴스 투표 " + data["date"])}'
                        f'&body={quote(str(i+1) + "번 기사 선택")}"'
                        f' style="font-size:10px;color:#10b981;font-weight:700;text-decoration:none;">👍 이 기사 선택</a>'
                    )
                cards += f"""
<div style="margin-bottom:14px;padding-bottom:14px;{border}">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px;">
    <span style="background:#f3f4f6;color:#374151;font-size:8px;font-weight:700;padding:2px 8px;border-radius:2px;letter-spacing:1px;">{escape(a.get('category',''))}</span>
    <span style="color:#9ca3af;font-size:9px;">{escape(a.get('label',''))} · {escape(a.get('region',''))}</span>
  </div>
  <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:6px;line-height:1.3;">{i+1}. {escape(a['title'])}</div>
  <div style="color:#6b7280;font-size:10px;line-height:1.6;">{bullets_text}</div>
  {"<div style='margin-top:6px;'>" + vote_link + "</div>" if vote_link else ""}
</div>"""
            more_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;">MORE STORIES</span>
</div>
{cards}"""
        else:
            more_html = ""

        return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><title>AI 뉴스 | {date}</title></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:4px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

  <!-- 헤더 -->
  <div style="background:#111827;padding:28px 32px 20px;">
    <div style="margin-bottom:4px;">
      <span style="font-size:9px;letter-spacing:3px;color:#6ee7b7;font-weight:700;display:block;margin-bottom:8px;">DAILY DIGEST</span>
      <span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#fff;">AI </span><span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#10b981;">NEWS</span>
    </div>
    <div style="text-align:right;margin-top:-28px;">
      <div style="color:#6b7280;font-size:9px;letter-spacing:1px;">VOL. 01</div>
      <div style="color:#9ca3af;font-size:9px;margin-top:2px;">{date}</div>
    </div>
    <div style="height:2px;background:linear-gradient(to right,#10b981,#059669,transparent);margin-top:14px;"></div>
  </div>

  <!-- 트렌드 배너 -->
  {trends_banner}

  <!-- 기사 섹션 -->
  <div style="padding:24px 32px;">
    {headline_html}
    {tip_html}
    {more_html}
  </div>

  <!-- 푸터 -->
  <div style="background:#111827;padding:16px 32px;text-align:center;">
    <div style="margin-bottom:4px;">
      <span style="font-size:16px;font-weight:900;color:#fff;">AI </span><span style="font-size:16px;font-weight:900;color:#10b981;">NEWS</span>
    </div>
    <div style="color:#4b5563;font-size:8px;letter-spacing:1px;">매일 오전 8시 · AI 뉴스 다이제스트</div>
  </div>

</div>
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
