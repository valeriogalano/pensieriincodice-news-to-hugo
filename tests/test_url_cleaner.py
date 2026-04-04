from url_cleaner import clean_url


def test_removes_utm_source():
    assert clean_url("https://example.com/a?utm_source=newsletter") == "https://example.com/a"


def test_removes_all_utm_params():
    url = "https://example.com/a?utm_source=x&utm_medium=email&utm_campaign=y&utm_term=z&utm_content=w"
    assert clean_url(url) == "https://example.com/a"


def test_removes_fbclid():
    assert clean_url("https://example.com/a?fbclid=abc123") == "https://example.com/a"


def test_removes_gclid():
    assert clean_url("https://example.com/a?gclid=xyz") == "https://example.com/a"


def test_removes_ga_param():
    assert clean_url("https://example.com/a?_ga=2.123456") == "https://example.com/a"


def test_removes_mc_params():
    url = "https://example.com/a?mc_cid=abc&mc_eid=def"
    assert clean_url(url) == "https://example.com/a"


def test_keeps_legitimate_params():
    url = "https://example.com/search?q=python&page=2"
    result = clean_url(url)
    assert "q=python" in result
    assert "page=2" in result


def test_mixed_params_keeps_legit_removes_tracking():
    url = "https://example.com/a?id=42&utm_source=twitter&fbclid=xyz"
    result = clean_url(url)
    assert "id=42" in result
    assert "utm_source" not in result
    assert "fbclid" not in result


def test_empty_string():
    assert clean_url("") == ""


def test_none_returns_none():
    assert clean_url(None) is None


def test_url_without_params():
    url = "https://example.com/article/my-post"
    assert clean_url(url) == url


def test_trailing_question_mark_cleaned():
    url = "https://example.com/a?utm_source=x"
    result = clean_url(url)
    assert result == "https://example.com/a"
