from content_generator.newsletter import NewsletterGenerator

SAMPLE = {
    "date": "2026-03-26",
    "trends": "• AI 모델 경쟁 심화\n• 멀티모달 발전",
    "tip": "Claude 오토 모드를 링크드인 프로필 요약에 써보세요.",
    "email_from": "test@example.com",
    "articles": [
        {
            "title": "GPT-5 출시",
            "category": "모델 출시",
            "bullets": ["성능 대폭 향상", "멀티모달 지원", "가격 인하"],
            "implication": "AI 경쟁 격화",
            "url": "https://example.com/1",
            "label": "TechCrunch",
            "region": "GL",
        },
        {
            "title": "EU AI법 시행",
            "category": "규제",
            "bullets": ["고위험 AI 등록 의무", "과징금 3%"],
            "implication": "기업 부담 증가",
            "url": "https://example.com/2",
            "label": "ZDNet",
            "region": "KR",
        },
    ]
}

def test_header_contains_ai_news():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "AI" in html
    assert "NEWS" in html
    assert "2026-03-26" in html
    assert "DAILY DIGEST" in html

def test_trends_banner_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "TODAY&#x27;S TRENDS" in html or "TODAY'S TRENDS" in html
    assert "AI 모델 경쟁 심화" in html

def test_trends_banner_skipped_when_empty():
    data = {**SAMPLE, "trends": ""}
    html = NewsletterGenerator().generate(data)
    assert "TODAY&#x27;S TRENDS" not in html and "TODAY'S TRENDS" not in html

def test_headline_section_first_article():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "HEADLINE" in html
    assert "GPT-5 출시" in html
    assert "성능 대폭 향상" in html
    assert "AI 경쟁 격화" in html  # implication in HEADLINE
    assert "https://example.com/1" in html  # url in HEADLINE

def test_more_stories_section():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "MORE STORIES" in html
    assert "EU AI법 시행" in html
    assert "고위험 AI 등록 의무" in html

def test_more_stories_no_implication_or_url():
    html = NewsletterGenerator().generate(SAMPLE)
    # MORE STORIES에는 두 번째 기사 url·implication이 없어야 함
    assert "https://example.com/2" not in html
    assert "기업 부담 증가" not in html  # 두 번째 기사의 implication

def test_tip_section_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "Claude 오토 모드를 링크드인 프로필 요약에 써보세요." in html

def test_tip_section_skipped_when_empty():
    data = {**SAMPLE, "tip": ""}
    html = NewsletterGenerator().generate(data)
    assert "Claude 오토 모드" not in html

def test_vote_link_rendered():
    html = NewsletterGenerator().generate(SAMPLE)
    assert "mailto:test@example.com" in html

def test_vote_link_skipped_when_no_email_from():
    data = {**SAMPLE, "email_from": ""}
    html = NewsletterGenerator().generate(data)
    assert "mailto:" not in html

def test_all_categories_other_skips_headline_and_more():
    data = {**SAMPLE, "articles": [
        {"title": "기타 기사", "category": "기타", "bullets": [], "implication": "", "url": "https://example.com/3", "label": "X", "region": "GL"}
    ]}
    html = NewsletterGenerator().generate(data)
    assert "HEADLINE" not in html
    assert "MORE STORIES" not in html

def test_xss_escaping():
    data = {**SAMPLE, "tip": "<script>alert(1)</script>", "articles": [{
        "title": "<b>XSS</b>", "category": "모델 출시",
        "bullets": ["<test>"], "implication": "imp",
        "url": "https://example.com/safe", "label": "T", "region": "GL"
    }]}
    html = NewsletterGenerator().generate(data)
    assert "<script>" not in html
    assert "&lt;b&gt;" in html or "&lt;script&gt;" in html
