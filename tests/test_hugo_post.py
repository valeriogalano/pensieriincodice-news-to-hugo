from datetime import datetime, timezone, timedelta

from hugo_post import generate_post, slugify

ROME = timezone(timedelta(hours=2))
FIXED_DATE = datetime(2026, 4, 4, 10, 0, 0, tzinfo=ROME)


def doc(title="Test Article", notes="Some notes", source_url="https://example.com/article"):
    return {"title": title, "notes": notes, "source_url": source_url}


# --- slugify ---

def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_italian_accents():
    assert slugify("Caffè e codice") == "caffe-e-codice"
    assert slugify("Città del futuro") == "citta-del-futuro"


def test_slugify_strips_special_chars():
    assert slugify("C'è qualcosa?") == "ce-qualcosa"


def test_slugify_collapses_multiple_hyphens():
    assert slugify("hello   world") == "hello-world"


def test_slugify_max_length():
    assert len(slugify("a" * 200)) <= 80


# --- filename ---

def test_filename_format():
    filename, _ = generate_post(doc(), [], "https://example.com", [], date=FIXED_DATE)
    assert filename == "2026-04-04-test-article.md"


def test_filename_uses_title_slug():
    filename, _ = generate_post(doc(title="Il mio articolo"), [], "https://example.com", [], date=FIXED_DATE)
    assert filename == "2026-04-04-il-mio-articolo.md"


# --- front matter ---

def test_front_matter_title():
    _, content = generate_post(doc(title="My Article"), [], "https://example.com", [], date=FIXED_DATE)
    assert 'title: "My Article"' in content


def test_title_with_quotes_escaped():
    _, content = generate_post(doc(title='Say "Hello"'), [], "https://example.com", [], date=FIXED_DATE)
    assert r'title: "Say \"Hello\""' in content


def test_draft_is_false():
    _, content = generate_post(doc(), [], "https://example.com", [], date=FIXED_DATE)
    assert "draft: false" in content


def test_featureImage_present():
    _, content = generate_post(doc(), [], "https://example.com", [], date=FIXED_DATE)
    assert "featureImage: /images/pensieriincodice-locandina.png" in content


def test_category_is_news():
    _, content = generate_post(doc(), [], "https://example.com", [], date=FIXED_DATE)
    assert "  - News" in content


def test_type_is_blog():
    _, content = generate_post(doc(), [], "https://example.com", [], date=FIXED_DATE)
    assert "type: blog" in content


def test_source_url_in_front_matter():
    _, content = generate_post(doc(), [], "https://example.com/article", [], date=FIXED_DATE)
    assert "source_url: https://example.com/article" in content


# --- tags ---

def test_news_tag_always_added():
    _, content = generate_post(doc(), [], "https://example.com", [], date=FIXED_DATE)
    assert "  - news" in content


def test_repost_tag_always_added():
    _, content = generate_post(doc(), [], "https://example.com", [], date=FIXED_DATE)
    assert "  - repost" in content


def test_hugo_news_tag_excluded():
    _, content = generate_post(doc(), [], "https://example.com", ["hugo-news"], date=FIXED_DATE)
    assert "hugo-news" not in content


def test_extra_tags_included():
    _, content = generate_post(doc(), [], "https://example.com", ["hugo-news", "python", "ai"], date=FIXED_DATE)
    assert "  - python" in content
    assert "  - ai" in content


def test_news_tag_is_first():
    _, content = generate_post(doc(), [], "https://example.com", ["hugo-news", "python"], date=FIXED_DATE)
    tags_block = content.split("tags:")[1].split("type:")[0]
    lines = [l.strip() for l in tags_block.strip().splitlines() if l.strip()]
    assert lines[0] == "- news"


# --- body ---

def test_source_link_in_body():
    _, content = generate_post(doc(), [], "https://example.com/article", [], date=FIXED_DATE)
    assert "[https://example.com/article](https://example.com/article)" in content


def test_notes_in_body():
    _, content = generate_post(doc(notes="My important note"), [], "https://example.com", [], date=FIXED_DATE)
    assert "My important note" in content


def test_empty_notes_no_extra_content():
    _, content = generate_post(doc(notes=""), [], "https://example.com", [], date=FIXED_DATE)
    front_matter, _, body = content.partition("---\n\n")
    body = body.strip()
    # Only the source link should be present
    assert body.startswith("*Fonte:")


def test_highlights_as_blockquotes():
    highlights = [{"text": "Important quote", "note": ""}]
    _, content = generate_post(doc(), highlights, "https://example.com", [], date=FIXED_DATE)
    assert "> Important quote" in content
    assert "## Passaggi in evidenza" not in content


def test_highlight_comment_present():
    highlights = [{"text": "A quote", "note": "My comment on this"}]
    _, content = generate_post(doc(), highlights, "https://example.com", [], date=FIXED_DATE)
    assert "My comment on this" in content


def test_highlight_without_comment():
    highlights = [{"text": "A quote", "note": ""}]
    _, content = generate_post(doc(), highlights, "https://example.com", [], date=FIXED_DATE)
    assert "> A quote" in content


def test_no_highlights_no_blockquotes():
    _, content = generate_post(doc(), [], "https://example.com", [], date=FIXED_DATE)
    assert "## Passaggi in evidenza" not in content
    assert ">" not in content


def test_empty_highlight_text_skipped():
    highlights = [{"text": "", "note": "a note"}, {"text": "Valid", "note": ""}]
    _, content = generate_post(doc(), highlights, "https://example.com", [], date=FIXED_DATE)
    assert "> Valid" in content
    # Empty highlight should not produce a blockquote line
    blockquotes = [l for l in content.splitlines() if l.startswith("> ") and not l.strip("> ")]
    assert len(blockquotes) == 0


def test_multiline_highlight_formatted_as_blockquote():
    highlights = [{"text": "Line one\nLine two", "note": ""}]
    _, content = generate_post(doc(), highlights, "https://example.com", [], date=FIXED_DATE)
    assert "> Line one" in content
    assert "> Line two" in content
