from html import escape
from typing import Dict


class NewsletterGenerator:
    def generate(self, data: Dict) -> str:
        """에디토리얼 매거진 스타일 HTML 뉴스레터 생성 (v2: 모노크롬 + Georgia)."""
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
                f'<span style="font-weight:400;color:rgba(229,231,235,0.85);font-size:11px;letter-spacing:0;">• {escape(t)}</span>'
                for t in trend_items
            )
            trends_banner = f"""
<div style="background:#374151;padding:10px 28px;">
  <div style="font-size:9px;font-weight:900;letter-spacing:2px;color:#e5e7eb;font-family:'Segoe UI',Arial,sans-serif;line-height:1.8;word-break:keep-all;">
    🔑 TODAY&#x27;S TRENDS<br>
    {trends_lines}
  </div>
</div>"""
        else:
            trends_banner = ""

        # 기사 분류
        valid = [a for a in articles if a.get("category") != "기타"]
        headline_article = max(valid, key=lambda a: a.get("score", 0)) if valid else None
        more_articles = [a for a in valid if a is not headline_article][:5]

        # HEADLINE 섹션
        if headline_article:
            a = headline_article
            bullets_html = "".join(
                f"<li style='margin-bottom:4px;'>{escape(b)}</li>"
                for b in a.get("bullets", [])
            )
            headline_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;font-family:'Segoe UI',Arial,sans-serif;">HEADLINE</span>
</div>
<div style="margin-bottom:22px;padding:16px;background:#f8fafc;border-radius:4px;border-left:4px solid #4b5563;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap;">
    <span style="background:#111827;color:#d1d5db;font-size:8px;font-weight:700;padding:2px 8px;border-radius:2px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('category', ''))}</span>
    <span style="color:#9ca3af;font-size:9px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('label', ''))} · {escape(a.get('region', ''))}</span>
  </div>
  <div style="font-size:14px;font-weight:700;color:#111827;line-height:1.4;margin-bottom:12px;font-family:Georgia,'Times New Roman',serif;">{escape(a['title'])}</div>
  <ul style="margin:0 0 8px;padding-left:16px;color:#374151;font-size:11px;line-height:1.8;font-family:'Segoe UI',Arial,sans-serif;">{bullets_html}</ul>
  <div style="font-size:10px;color:#6b7280;font-style:italic;margin-bottom:10px;font-family:'Segoe UI',Arial,sans-serif;">👉 {escape(a.get('implication', ''))}</div>
  <a href="{escape(a['url'])}" style="font-size:10px;color:#4b5563;font-weight:700;text-decoration:underline;font-family:'Segoe UI',Arial,sans-serif;">원문 보기 →</a>
</div>"""
        else:
            headline_html = ""

        # AI 팁 섹션
        if tip.get("task"):
            task_text = escape(tip["task"])

            tools_html = ""
            if tip.get("tools"):
                tags = "".join(
                    f'<span style="background:#e5e7eb;color:#374151;font-size:9px;font-weight:700;padding:3px 10px;border-radius:12px;font-family:\'Segoe UI\',Arial,sans-serif;">{escape(t)}</span> '
                    for t in tip["tools"]
                )
                tools_html = f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;">{tags}</div>'

            steps_html = ""
            if tip.get("steps"):
                step_nums = ["①", "②", "③", "④", "⑤"]
                rows = ""
                for i, step in enumerate(tip["steps"][:5]):
                    num = step_nums[i]
                    arrow = ""
                    if i < len(tip["steps"]) - 1:
                        arrow = '<div style="text-align:center;color:#9ca3af;font-size:12px;line-height:1;margin:2px 0 2px 22px;">↓</div>'
                    rows += f"""
<div style="display:flex;align-items:flex-start;gap:10px;">
  <span style="flex-shrink:0;width:22px;height:22px;background:#111827;color:#fff;font-size:11px;font-weight:700;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-family:'Segoe UI',Arial,sans-serif;">{num}</span>
  <span style="font-size:11px;color:#374151;line-height:1.6;padding-top:3px;font-family:'Segoe UI',Arial,sans-serif;">{escape(step)}</span>
</div>
{arrow}"""
                steps_html = f"""
<div style="margin-bottom:14px;">
  <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:8px;font-family:'Segoe UI',Arial,sans-serif;">🪜 이렇게 따라하세요</div>
  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:4px;padding:12px 14px;">
    {rows}
  </div>
</div>"""

            prompt_html = ""
            if tip.get("prompt"):
                prompt_html = f"""
<div>
  <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:6px;font-family:'Segoe UI',Arial,sans-serif;">📋 복붙 프롬프트 — 그대로 붙여넣고 [ ] 부분만 수정하세요</div>
  <div style="background:#111827;border-radius:4px;padding:14px 16px;font-family:'Courier New',Courier,monospace;font-size:11px;color:#e5e7eb;line-height:1.8;word-break:keep-all;white-space:pre-wrap;">{escape(tip['prompt'])}</div>
</div>"""

            tip_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;font-family:'Segoe UI',Arial,sans-serif;">💡 오늘 바로 써먹는 AI 팁</span>
</div>
<div style="margin-bottom:22px;padding:16px;background:#f9fafb;border-radius:4px;border-left:4px solid #6b7280;">
  <div style="margin-bottom:12px;">
    <div style="font-size:8px;font-weight:900;letter-spacing:1px;color:#6b7280;margin-bottom:4px;font-family:'Segoe UI',Arial,sans-serif;">✦ 오늘의 자동화 TASK</div>
    <div style="font-size:11px;color:#374151;line-height:1.8;font-family:'Segoe UI',Arial,sans-serif;">{task_text}</div>
  </div>
  {tools_html}
  {steps_html}
  {prompt_html}
</div>"""
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
<div style="margin-bottom:12px;padding:14px;background:#f8fafc;border-left:3px solid #d1d5db;border-radius:4px;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px;flex-wrap:wrap;">
    <span style="background:#f3f4f6;color:#374151;font-size:8px;font-weight:700;padding:2px 8px;border-radius:2px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('category', ''))}</span>
    <span style="color:#9ca3af;font-size:9px;font-family:'Segoe UI',Arial,sans-serif;">{escape(a.get('label', ''))} · {escape(a.get('region', ''))}</span>
  </div>
  <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:6px;line-height:1.4;font-family:Georgia,'Times New Roman',serif;">{i + 1}. {escape(a['title'])}</div>
  <div style="color:#6b7280;font-size:10px;line-height:1.7;font-family:'Segoe UI',Arial,sans-serif;">{bullets_text}</div>
  <div style="margin-top:10px;"><a href="{escape(a['url'])}" style="font-size:10px;color:#4b5563;font-weight:700;text-decoration:underline;font-family:'Segoe UI',Arial,sans-serif;">원문 보기 →</a></div>
</div>"""
            more_html = f"""
<div style="border-bottom:2px solid #111827;padding-bottom:4px;margin-bottom:14px;">
  <span style="font-size:9px;font-weight:900;letter-spacing:2px;color:#111827;font-family:'Segoe UI',Arial,sans-serif;">MORE STORIES</span>
</div>
{cards}"""
        else:
            more_html = ""

        return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 뉴스 | {date}</title></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f1f5f9;margin:0;padding:12px;">
<div style="max-width:680px;margin:0 auto;background:#fff;border-radius:4px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

  <!-- 헤더 -->
  <div style="background:#111827;padding:24px 28px 18px;">
    <div style="display:flex;align-items:flex-end;flex-wrap:wrap;gap:8px;margin-bottom:4px;">
      <div>
        <span style="font-size:9px;letter-spacing:3px;color:#9ca3af;font-weight:700;display:block;margin-bottom:8px;font-family:'Segoe UI',Arial,sans-serif;">DAILY DIGEST</span>
        <span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#fff;font-family:Georgia,'Times New Roman',serif;">AI </span><span style="font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1;color:#e5e7eb;font-family:Georgia,'Times New Roman',serif;">NEWS</span>
      </div>
      <div style="margin-left:auto;text-align:right;padding-bottom:4px;">
        <div style="color:#6b7280;font-size:9px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">VOL. 01</div>
        <div style="color:#9ca3af;font-size:9px;margin-top:2px;font-family:'Segoe UI',Arial,sans-serif;">{date}</div>
      </div>
    </div>
    <div style="height:1px;background:rgba(255,255,255,0.12);margin-top:14px;"></div>
  </div>

  <!-- 트렌드 배너 -->
  {trends_banner}

  <!-- 기사 섹션 -->
  <div style="padding:22px 28px;">
    {headline_html}
    {more_html}
    {tip_html}
  </div>

  <!-- 푸터 -->
  <div style="background:#111827;padding:16px 28px;text-align:center;">
    <div style="margin-bottom:4px;">
      <span style="font-size:16px;font-weight:900;color:#fff;font-family:Georgia,'Times New Roman',serif;">AI </span><span style="font-size:16px;font-weight:900;color:#e5e7eb;font-family:Georgia,'Times New Roman',serif;">NEWS</span>
    </div>
    <div style="color:#4b5563;font-size:8px;letter-spacing:1px;font-family:'Segoe UI',Arial,sans-serif;">매일 오전 8시 · AI 뉴스 다이제스트</div>
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
            lines.append(f"   출처: {a.get('label', '')} ({a.get('region', '')})")
            for b in a.get("bullets", []):
                lines.append(f"   - {b}")
            lines.append(f"\n   👉 {a.get('implication', '')}")
            lines.append(f"\n   원문: {a['url']}")
            lines.append("---")

        return "\n".join(lines)
