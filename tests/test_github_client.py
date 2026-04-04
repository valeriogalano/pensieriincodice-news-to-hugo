import base64
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN_WEBSITE", "test-gh-token")
    monkeypatch.setenv("GITHUB_REPO_OWNER", "testowner")
    monkeypatch.setenv("GITHUB_REPO_NAME", "testrepo")


def mock_response(status):
    m = MagicMock()
    m.status_code = status
    m.raise_for_status = MagicMock()
    return m


def no_existing_file():
    m = mock_response(404)
    m.json.return_value = {}
    return m


def existing_file(sha="abc123"):
    m = mock_response(200)
    m.json.return_value = {"sha": sha}
    return m


def test_create_post_returns_true_on_new_file():
    from github_client import GitHubClient
    gh = GitHubClient()
    with patch("requests.get", return_value=no_existing_file()):
        with patch("requests.put", return_value=mock_response(201)):
            result = gh.create_post("2026-04-04-test.md", "content", "news: test")
    assert result is True


def test_create_post_returns_true_on_update():
    from github_client import GitHubClient
    gh = GitHubClient()
    with patch("requests.get", return_value=existing_file("sha-xyz")):
        with patch("requests.put", return_value=mock_response(200)):
            result = gh.create_post("existing.md", "content", "msg")
    assert result is True


def test_update_includes_sha_in_payload():
    from github_client import GitHubClient
    gh = GitHubClient()
    with patch("requests.get", return_value=existing_file("sha-xyz")):
        with patch("requests.put", return_value=mock_response(200)) as mock_put:
            gh.create_post("existing.md", "content", "msg")
    payload = mock_put.call_args[1]["json"]
    assert payload["sha"] == "sha-xyz"


def test_create_does_not_include_sha_for_new_file():
    from github_client import GitHubClient
    gh = GitHubClient()
    with patch("requests.get", return_value=no_existing_file()):
        with patch("requests.put", return_value=mock_response(201)) as mock_put:
            gh.create_post("new.md", "content", "msg")
    payload = mock_put.call_args[1]["json"]
    assert "sha" not in payload


def test_create_post_raises_on_api_error():
    from github_client import GitHubClient
    gh = GitHubClient()
    m = mock_response(500)
    m.raise_for_status.side_effect = Exception("Server error")
    with patch("requests.get", return_value=no_existing_file()):
        with patch("requests.put", return_value=m):
            with pytest.raises(Exception, match="Server error"):
                gh.create_post("file.md", "content", "msg")


def test_file_path_is_in_content_blog():
    from github_client import GitHubClient
    gh = GitHubClient()
    with patch("requests.get", return_value=no_existing_file()):
        with patch("requests.put", return_value=mock_response(201)) as mock_put:
            gh.create_post("2026-04-04-my-post.md", "content", "msg")
    url = mock_put.call_args[0][0]
    assert "content/blog/2026-04-04-my-post.md" in url


def test_content_is_base64_encoded():
    from github_client import GitHubClient
    gh = GitHubClient()
    test_content = "# Hello\n\nThis is a test post."
    with patch("requests.get", return_value=no_existing_file()):
        with patch("requests.put", return_value=mock_response(201)) as mock_put:
            gh.create_post("test.md", test_content, "msg")
    payload = mock_put.call_args[1]["json"]
    decoded = base64.b64decode(payload["content"]).decode("utf-8")
    assert decoded == test_content


def test_correct_repo_in_url():
    from github_client import GitHubClient
    gh = GitHubClient()
    with patch("requests.get", return_value=no_existing_file()):
        with patch("requests.put", return_value=mock_response(201)) as mock_put:
            gh.create_post("file.md", "content", "msg")
    url = mock_put.call_args[0][0]
    assert "testowner/testrepo" in url


def test_authorization_header_sent():
    from github_client import GitHubClient
    gh = GitHubClient()
    with patch("requests.get", return_value=no_existing_file()):
        with patch("requests.put", return_value=mock_response(201)) as mock_put:
            gh.create_post("file.md", "content", "msg")
    headers = mock_put.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer test-gh-token"


def test_commit_message_in_payload():
    from github_client import GitHubClient
    gh = GitHubClient()
    with patch("requests.get", return_value=no_existing_file()):
        with patch("requests.put", return_value=mock_response(201)) as mock_put:
            gh.create_post("file.md", "content", "news: My Article")
    payload = mock_put.call_args[1]["json"]
    assert payload["message"] == "news: My Article"
