from html import escape
from typing import Dict


class NewsletterGenerator:
    def generate(self, data: Dict) -> str:
        """HTML 뉴스레터 생성."""
        date = escape(data["date"])
        trends = data["trends"]
        articles = data["articles"]

        articles_html = ""
        for a in articles:
            if a.get("category") == "기타":
                continue
            bullets_html = "".join(f"<li>{escape(b)}</li>" for b in a.get("bullets", []))
            articles_html += f"""
<div style="margin-bottom:24px;padding:16px;border-left:4px solid #4f46e5;">
  <h3 style="margin:0 0 8px;font-size:16px;">{escape(a['title'])}</h3>
  <p style="margin:0 0 4px;font-size:12px;color:#6b7280;">
    [{escape(a.get('category',''))}] {escape(a.get('label',''))} ({escape(a.get('region',''))})
  </p>
  <ul style="margin:8px 0;padding-left:20px;">{bullets_html}</ul>
  <p style="margin:8px 0 4px;font-style:italic;color:#374151;">\U0001f449 {escape(a.get('implication',''))}</p>
  <a href="{escape(a['url'])}" style="font-size:12px;color:#4f46e5;">원문 보기 →</a>
</div>"""

        trends_html = "".join(
            f"<li style='margin-bottom:8px;'>{escape(t.lstrip('• '))}</li>"
            for t in trends.split("\n") if t.strip()
        )

        return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><title>AI 뉴스 | {date}</title></head>
<body style="font-family:sans-serif;max-width:680px;margin:0 auto;padding:24px;color:#1f2937;">
<h1 style="font-size:24px;border-bottom:2px solid #4f46e5;padding-bottom:8px;">
  \U0001f916 AI 뉴스 | {date}
</h1>
<h2 style="font-size:18px;color:#4f46e5;">\U0001f511 오늘의 핵심 트렌드</h2>
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

        for i, a in enumerate(articles):
            if a.get("category") == "기타":
                continue
            lines.append(f"\n{i+1}. {a['title']}")
            lines.append(f"   출처: {a.get('label','')} ({a.get('region','')})")
            for b in a.get("bullets", []):
                lines.append(f"   - {b}")
            lines.append(f"\n   👉 {a.get('implication','')}")
            lines.append(f"\n   원문: {a['url']}")
            lines.append("---")

        return "\n".join(lines)
