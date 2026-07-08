from content_generator.newsletter import NewsletterGenerator

SAMPLE = {
    "date": "2026-03-26",
    "trends": "• AI 모델 경쟁 심화\n• 멀티모달 발전",
    "tip": {
        "task": "회의록을 AI로 정리할 수 있어요. 참석자별 액션 아이템이 자동으로 만들어져요.",
        "tools": ["Claude", "ChatGPT"],
        "prompt": "아래 회의록을 액션 아이템으로 정리해줘. 형식: [담당자] - [할 일]",
    },
    "articles": [
        {
            "title": "GPT-5 출시",
            "category": "모델 출시",
            "bullets": ["성능이 대폭 향상됐어요", "멀티모달을 지원해요", "가격이 인하됐어요"],
            "implication": "AI 경쟁이 더욱 심화됐어요",
            "url": "https://example.com/1",
            "label": "TechCrunch",
            "region": "GL",
            "score": 7,
        },
        {
            "title": "EU AI법 시행",
            "category": "규제",
            "bullets": ["고위험 AI 등록이 의무화됐어요", "과징금이 3%로 설정됐어요"],
            "implication": "기업 부담이 증가했어요",
            "url": "https://example.com/2",
            "label": "ZDNet",
            "region": "KR",
            "score": 5,
        },
    ]
}


def test_header_contains_ai_news():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "AI" in html
    assert "NEWS" in html
    assert "2026-03-26" in html
    assert "DAILY DIGEST" in html


def test_header_uses_georgia_font():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "Georgia" in html


def test_header_is_monochrome():
    """헤더에 에메랄드 그린(#10b981)이 없어야 함."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "#10b981" not in html


def test_trends_banner_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "TODAY" in html and "TRENDS" in html
    assert "AI 모델 경쟁 심화" in html


def test_trends_banner_dark_background():
    """트렌드 배너 배경이 #374151이어야 함."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "#374151" in html


def test_trends_banner_skipped_when_empty():
    data = {**SAMPLE, "trends": ""}
    html = NewsletterGenerator().generate(data)
    assert "TODAY" not in html or "TRENDS" not in html


def test_headline_section_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "HEADLINE" in html
    assert "GPT-5 출시" in html
    assert "성능이 대폭 향상됐어요" in html
    assert "AI 경쟁이 더욱 심화됐어요" in html
    assert "https://example.com/1" in html


def test_headline_uses_georgia_font():
    html = NewsletterGenerator().generate(SAMPLE)
    # HEADLINE 섹션 안에 Georgia 폰트 적용 확인
    assert html.count("Georgia") >= 2  # 헤더 + 기사 제목 최소 2곳


def test_more_stories_section_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "MORE STORIES" in html
    assert "EU AI법 시행" in html
    assert "고위험 AI 등록이 의무화됐어요" in html


def test_more_stories_has_url_link():
    """MORE STORIES에 원문 보기 링크가 있어야 함."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "https://example.com/2" in html


def test_more_stories_no_vote_link():
    """투표 mailto 링크가 없어야 함 (푸터의 수신거부 mailto 1개만 허용)."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "subject=투표" not in html
    assert html.count("mailto:") == 1  # 수신거부 링크만
    assert "수신거부" in html


def test_more_stories_max_5_articles():
    """MORE STORIES는 최대 5개만 표시."""
    articles = [SAMPLE["articles"][0]] + [
        {"title": f"기사{i}", "category": "규제", "bullets": [f"불릿{i}"],
         "implication": "시사점", "url": f"https://example.com/{i}", "label": "X", "region": "GL"}
        for i in range(2, 9)  # 7개 추가 → 총 8개 비-기타
    ]
    data = {**SAMPLE, "articles": articles}
    html = NewsletterGenerator().generate(data)
    # 6번째 이후 기사 제목이 없어야 함 (기사7, 기사8은 잘려야 함)
    assert "기사7" not in html
    assert "기사8" not in html


def test_tip_section_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "오늘의 자동화 TASK" in html
    assert "회의록을 AI로 정리할 수 있어요" in html
    assert "Claude" in html
    assert "ChatGPT" in html  # 툴 태그 렌더링
    assert "복붙 프롬프트" in html
    assert "아래 회의록을 액션 아이템으로 정리해줘" in html


def test_tip_section_skipped_when_empty_dict():
    data = {**SAMPLE, "tip": {}}
    html = NewsletterGenerator().generate(data)
    assert "오늘의 자동화 TASK" not in html


def test_tip_section_skipped_when_none():
    data = {**SAMPLE, "tip": None}
    html = NewsletterGenerator().generate(data)
    assert "오늘의 자동화 TASK" not in html


def test_tip_tools_skipped_when_empty():
    data = {**SAMPLE, "tip": {"task": "팁이에요.", "tools": [], "prompt": "프롬프트"}}
    html = NewsletterGenerator().generate(data)
    assert "추천 툴" not in html


def test_tip_prompt_skipped_when_empty():
    data = {**SAMPLE, "tip": {"task": "팁이에요.", "tools": ["Claude"], "prompt": ""}}
    html = NewsletterGenerator().generate(data)
    assert "복붙 프롬프트" not in html


def test_all_categories_other_skips_headline_and_more():
    data = {**SAMPLE, "articles": [
        {"title": "기타 기사", "category": "기타", "bullets": [],
         "implication": "", "url": "https://example.com/3", "label": "X", "region": "GL"}
    ]}
    html = NewsletterGenerator().generate(data)
    assert "HEADLINE" not in html
    assert "MORE STORIES" not in html


def test_xss_escaping():
    data = {
        **SAMPLE,
        "tip": {"task": "<script>alert(1)</script>", "tools": ["Claude"], "prompt": "ok"},
        "articles": [{
            "title": "<b>XSS</b>", "category": "모델 출시",
            "bullets": ["<test>"], "implication": "imp",
            "url": "https://example.com/safe", "label": "T", "region": "GL"
        }]
    }
    html = NewsletterGenerator().generate(data)
    assert "<script>" not in html
    assert "&lt;" in html


def test_mobile_viewport_meta():
    """모바일 viewport meta 태그 포함 확인."""
    html = NewsletterGenerator().generate(SAMPLE)
    assert "viewport" in html


def test_label_region_fallback():
    """label/region 없어도 오류 없이 렌더링."""
    data = {**SAMPLE, "articles": [
        {"title": "테스트", "category": "규제", "bullets": ["b1"],
         "implication": "imp", "url": "https://x.com"}  # label/region 없음
    ]}
    html = NewsletterGenerator().generate(data)
    assert "테스트" in html


def test_headline_is_highest_score():
    """가장 높은 score 기사가 헤드라인으로 선정되어야 함."""
    articles = [
        {
            "title": "낮은점수기사",
            "category": "규제",
            "bullets": ["b1"],
            "implication": "imp",
            "url": "https://example.com/low",
            "label": "A",
            "region": "KR",
            "score": 3,
        },
        {
            "title": "높은점수기사",
            "category": "모델 출시",
            "bullets": ["b2"],
            "implication": "imp",
            "url": "https://example.com/high",
            "label": "B",
            "region": "GL",
            "score": 9,
        },
    ]
    data = {**SAMPLE, "articles": articles}
    html = NewsletterGenerator().generate(data)
    headline_pos = html.index("높은점수기사")
    more_pos = html.index("낮은점수기사")
    assert headline_pos < more_pos  # 헤드라인이 MORE STORIES보다 먼저 등장


def test_headline_not_in_more_stories():
    """헤드라인 기사가 MORE STORIES에 중복 노출되지 않아야 함."""
    articles = [
        {
            "title": "최고기사",
            "category": "모델 출시",
            "bullets": ["b"],
            "implication": "imp",
            "url": "https://example.com/best",
            "label": "X",
            "region": "GL",
            "score": 10,
        },
        {
            "title": "보통기사",
            "category": "규제",
            "bullets": ["b"],
            "implication": "imp",
            "url": "https://example.com/ok",
            "label": "Y",
            "region": "KR",
            "score": 5,
        },
    ]