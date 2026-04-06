import json
import pytest
from unittest.mock import patch, mock_open


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("READWISE_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("GH_TOKEN_WEBSITE", "gh-tok")
    monkeypatch.setenv("GH_REPO_OWNER", "owner")
    monkeypatch.setenv("GH_REPO_NAME", "repo")


def load_processed_from(data):
    import main
    with patch("builtins.open", mock_open(read_data=json.dumps(data))):
        return main.load_processed()


def test_load_processed_flat_array():
    result = load_processed_from(["id1", "id2"])
    assert result == ["id1", "id2"]


def test_load_processed_migrates_old_state_format():
    result = load_processed_from({"last_fetch": "2026-04-04T10:00:00", "processed_ids": ["id1"]})
    assert result == ["id1"]


def test_load_processed_file_not_found():
    import main
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = main.load_processed()
    assert result == []


def test_since_uses_lookback_hours_env(monkeypatch):
    import main
    monkeypatch.setenv("READWISE_LOOKBACK_HOURS", "48")
    captured = {}

    def fake_get_tagged(tag, since):
        captured["since"] = since
        return []

    with patch("main.Readwise") as MockRW:
        MockRW.return_value.get_tagged_documents.side_effect = fake_get_tagged
        main.main()

    from datetime import datetime, timedelta
    since_dt = datetime.fromisoformat(captured["since"])
    assert since_dt > datetime.now() - timedelta(hours=49)
    assert since_dt < datetime.now() - timedelta(hours=47)


def test_since_defaults_to_48h(monkeypatch):
    import main
    monkeypatch.delenv("READWISE_LOOKBACK_HOURS", raising=False)
    captured = {}

    def fake_get_tagged(tag, since):
        captured["since"] = since
        return []

    with patch("main.Readwise") as MockRW:
        MockRW.return_value.get_tagged_documents.side_effect = fake_get_tagged
        main.main()

    from datetime import datetime, timedelta
    since_dt = datetime.fromisoformat(captured["since"])
    assert since_dt > datetime.now() - timedelta(hours=49)
    assert since_dt < datetime.now() - timedelta(hours=47)


def test_no_commit_when_nothing_published():
    import main
    with patch("main.Readwise") as MockRW, \
         patch("main.save_processed") as mock_save:
        MockRW.return_value.get_tagged_documents.return_value = []
        main.main()
    mock_save.assert_not_called()


def test_already_processed_ids_skipped():
    import main
    doc = {"id": "id-already", "title": "T", "source_url": "https://x.com", "tags": {"hugo-news": {}}}

    with patch("main.load_processed", return_value=["id-already"]), \
         patch("main.save_processed") as mock_save, \
         patch("main.Readwise") as MockRW, \
         patch("main.GitHubClient") as MockGH:
        MockRW.return_value.get_tagged_documents.return_value = [doc]
        main.main()
        MockGH.return_value.create_post.assert_not_called()
        mock_save.assert_not_called()


def test_save_called_only_when_post_published():
    import main
    doc = {"id": "new-id", "title": "T", "source_url": "https://x.com",
           "tags": {"hugo-news": {}}, "notes": ""}

    with patch("main.load_processed", return_value=[]), \
         patch("main.save_processed") as mock_save, \
         patch("main.Readwise") as MockRW, \
         patch("main.GitHubClient") as MockGH, \
         patch("main.generate_post", return_value=("file.md", "content")), \
         patch("main.clean_url", return_value="https://x.com"):
        MockRW.return_value.get_tagged_documents.return_value = [doc]
        MockRW.return_value.get_highlights.return_value = []
        MockGH.return_value.create_post.return_value = True
        main.main()

    mock_save.assert_called_once()
    saved_ids = mock_save.call_args[0][0]
    assert "new-id" in saved_ids
