from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("READWISE_ACCESS_TOKEN", "test-token")


def mock_response(data, status=200):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = data
    m.headers = {}
    m.raise_for_status = MagicMock()
    return m


def mock_429(retry_after=None):
    m = MagicMock()
    m.status_code = 429
    m.headers = {"Retry-After": str(retry_after)} if retry_after is not None else {}
    m.raise_for_status = MagicMock()
    return m


def docs_page(results, cursor=None):
    return {"results": results, "nextPageCursor": cursor}


def books_page(results, next_url=None):
    return {"results": results, "next": next_url}


def highlights_page(results, next_url=None):
    return {"results": results, "next": next_url}


# --- get_tagged_documents ---

def test_filters_by_tag():
    from readwise import Readwise
    rw = Readwise()
    data = docs_page([
        {"id": "1", "tags": {"hugo-news": {}, "python": {}}},
        {"id": "2", "tags": {"publish": {}}},
        {"id": "3", "tags": None},
        {"id": "4", "tags": {}},
    ])
    with patch("requests.get", return_value=mock_response(data)):
        result = rw.get_tagged_documents("hugo-news", "2026-01-01")
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_returns_empty_when_no_tagged_docs():
    from readwise import Readwise
    rw = Readwise()
    with patch("requests.get", return_value=mock_response(docs_page([]))):
        result = rw.get_tagged_documents("hugo-news", "2026-01-01")
    assert result == []


def test_paginates_documents():
    from readwise import Readwise
    rw = Readwise()
    page1 = docs_page([{"id": "1", "tags": {"hugo-news": {}}}], cursor="cursor-abc")
    page2 = docs_page([{"id": "2", "tags": {"hugo-news": {}}}])
    with patch("requests.get", side_effect=[mock_response(page1), mock_response(page2)]):
        result = rw.get_tagged_documents("hugo-news", "2026-01-01")
    assert len(result) == 2


# --- get_highlights ---

def test_returns_empty_when_book_not_found():
    from readwise import Readwise
    rw = Readwise()
    with patch("requests.get", return_value=mock_response(books_page([]))):
        result = rw.get_highlights("https://example.com", "Some Title")
    assert result == []


def test_matches_book_by_source_url():
    from readwise import Readwise
    rw = Readwise()
    books = books_page([{"id": 42, "title": "X", "source_url": "https://example.com"}])
    highlights = highlights_page([{"id": 1, "text": "highlight text", "note": ""}])
    with patch("requests.get", side_effect=[mock_response(books), mock_response(highlights)]):
        result = rw.get_highlights("https://example.com", "X")
    assert len(result) == 1
    assert result[0]["text"] == "highlight text"


def test_falls_back_to_title_match():
    from readwise import Readwise
    rw = Readwise()
    books = books_page([{"id": 99, "title": "Exact Title", "source_url": "https://other.com"}])
    highlights = highlights_page([{"id": 2, "text": "some text", "note": "note"}])
    with patch("requests.get", side_effect=[mock_response(books), mock_response(highlights)]):
        result = rw.get_highlights("https://example.com", "Exact Title")
    assert len(result) == 1


def test_source_url_match_takes_priority_over_title():
    from readwise import Readwise
    rw = Readwise()
    books = books_page([
        {"id": 1, "title": "Exact Title", "source_url": "https://wrong.com"},
        {"id": 2, "title": "Different Title", "source_url": "https://example.com"},
    ])
    highlights = highlights_page([{"id": 10, "text": "correct", "note": ""}])
    with patch("requests.get", side_effect=[mock_response(books), mock_response(highlights)]) as mock_get:
        result = rw.get_highlights("https://example.com", "Exact Title")
    # Should have used book id=2 (url match)
    highlights_call = mock_get.call_args_list[1]
    assert highlights_call[1]["params"]["book_id"] == 2


def test_paginates_highlights():
    from readwise import Readwise
    rw = Readwise()
    books = books_page([{"id": 5, "title": "T", "source_url": "https://example.com"}])
    h_page1 = highlights_page([{"id": 1, "text": "h1", "note": ""}], next_url="page2")
    h_page2 = highlights_page([{"id": 2, "text": "h2", "note": ""}])
    with patch("requests.get", side_effect=[mock_response(books), mock_response(h_page1), mock_response(h_page2)]):
        result = rw.get_highlights("https://example.com", "T")
    assert len(result) == 2


# --- retry su 429 ---

def test_retries_on_429_then_succeeds():
    from readwise import Readwise
    rw = Readwise()
    data = docs_page([{"id": "1", "tags": {"hugo-news": {}}}])
    with patch("requests.get", side_effect=[mock_429(retry_after=0), mock_response(data)]):
        with patch("time.sleep") as mock_sleep:
            result = rw.get_tagged_documents("hugo-news", "2026-01-01")
    mock_sleep.assert_called_once_with(0)
    assert len(result) == 1


def test_uses_retry_after_header():
    from readwise import Readwise
    rw = Readwise()
    data = docs_page([])
    with patch("requests.get", side_effect=[mock_429(retry_after=30), mock_response(data)]):
        with patch("time.sleep") as mock_sleep:
            rw.get_tagged_documents("hugo-news", "2026-01-01")
    mock_sleep.assert_called_once_with(30)


def test_raises_after_max_retries():
    from readwise import Readwise
    rw = Readwise()
    with patch("requests.get", return_value=mock_429()):
        with patch("time.sleep"):
            with pytest.raises(Exception, match="Rate limit persistente"):
                rw.get_tagged_documents("hugo-news", "2026-01-01")
