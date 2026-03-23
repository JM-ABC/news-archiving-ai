from content_generator.newsletter import NewsletterGenerator

SAMPLE = {
    "date": "2026-03-24",
    "trends": "• AI 모델 경쟁 심화\n• 멀티모달 발전",
    "articles": [
        {
            "title": "GPT-5 출시",
            "category": "모델 출시",
            "bullets": ["성능 대폭 향상", "멀티모달 지원"],
            "implication": "AI 경쟁 격화",
            "url": "https://example.com/1",
            "label": "TechCrunch AI",
            "region": "GL",
        }
    ]
}

def test_generate_html_contains_title():
    gen = NewsletterGenerator()
    html = gen.generate(SAMPLE)
    assert "GPT-5 출시" in html
    assert "2026-03-24" in html

def test_generate_html_contains_trends():
    gen = NewsletterGenerator()
    html = gen.generate(SAMPLE)
    assert "AI 모델 경쟁 심화" in html

def test_generate_html_contains_article_bullets():
    gen = NewsletterGenerator()
    html = gen.generate(SAMPLE)
    assert "성능 대폭 향상" in html
    assert "AI 경쟁 격화" in html

def test_generate_html_contains_link():
    gen = NewsletterGenerator()
    html = gen.generate(SAMPLE)
    assert "https://example.com/1" in html

def test_generate_txt_contains_trends():
    gen = NewsletterGenerator()
    txt = gen.generate_txt(SAMPLE)
    assert "핵심 트렌드" in txt
    assert "AI 모델 경쟁 심화" in txt

def test_generate_txt_contains_article():
    gen = NewsletterGenerator()
    txt = gen.generate_txt(SAMPLE)
    assert "GPT-5 출시" in txt
    assert "https://example.com/1" in txt

def test_generate_html_escapes_special_chars():
    gen = NewsletterGenerator()
    data = {
        "date": "2026-03-24",
        "trends": "• <script>alert(1)</script>",
        "articles": [{
            "title": '<b>XSS & Test</b>',
            "category": "기타",
            "bullets": ["<test>"],
            "implication": "imp",
            "url": "https://example.com/1",
            "label": "Test",
            "region": "GL",
        }]
    }
    html = gen.generate(data)
    assert "<script>" not in html
    assert "&lt;b&gt;" in html or "&lt;script&gt;" in html
