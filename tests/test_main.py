import json
import os
import pytest
from unittest.mock import patch, mock_open


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("READWISE_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("GITHUB_TOKEN_WEBSITE", "gh-tok")
    monkeypatch.setenv("GITHUB_REPO_OWNER", "owner")
    monkeypatch.setenv("GITHUB_REPO_NAME", "repo")


def load_state_from(data):
    import main
    with patch("builtins.open", mock_open(read_data=json.dumps(data).encode())):
        return main.load_state()


def test_load_state_new_format():
    import main
    state = {"last_fetch": "2026-04-04T10:00:00", "processed_ids": ["id1"]}
    result = load_state_from(state)
    assert result["last_fetch"] == "2026-04-04T10:00:00"
    assert result["processed_ids"] == ["id1"]


def test_load_state_migrates_old_array_format():
    import main
    result = load_state_from(["id1", "id2"])
    assert result["last_fetch"] is None
    assert result["processed_ids"] == ["id1", "id2"]


def test_load_state_file_not_found():
    import main
    with patch("builtins.open", side_effect=FileNotFoundError):
        state = main.load_state()
    assert state["last_fetch"] is None
    assert state["processed_ids"] == []


def test_since_uses_last_fetch_when_available():
    import main
    state = {"last_fetch": "2026-04-03T10:00:00", "processed_ids": []}
    captured = {}

    def fake_get_tagged(tag, since):
        captured["since"] = since
        return []

    with patch.object(main, "load_state", return_value=state), \
         patch.object(main, "save_state"), \
         patch("main.Readwise") as MockRW:
        MockRW.return_value.get_tagged_documents.side_effect = fake_get_tagged
        main.main()

    assert captured["since"] == "2026-04-03T10:00:00"


def test_since_uses_fallback_when_no_last_fetch():
    import main
    from datetime import datetime, timedelta
    state = {"last_fetch": None, "processed_ids": []}
    captured = {}

    def fake_get_tagged(tag, since):
        captured["since"] = since
        return []

    with patch.object(main, "load_state", return_value=state), \
         patch.object(main, "save_state"), \
         patch("main.Readwise") as MockRW:
        MockRW.return_value.get_tagged_documents.side_effect = fake_get_tagged
        main.main()

    since_dt = datetime.fromisoformat(captured["since"])
    assert since_dt < datetime.now() - timedelta(days=6)


def test_last_fetch_updated_after_run():
    import main
    state = {"last_fetch": None, "processed_ids": []}
    saved = {}

    with patch.object(main, "load_state", return_value=state), \
         patch.object(main, "save_state", side_effect=lambda s: saved.update(s)), \
         patch("main.Readwise") as MockRW:
        MockRW.return_value.get_tagged_documents.return_value = []
        main.main()

    assert saved.get("last_fetch") is not None


def test_already_processed_ids_skipped():
    import main
    state = {"last_fetch": "2026-04-03T10:00:00", "processed_ids": ["id-already"]}
    doc = {"id": "id-already", "title": "T", "source_url": "https://x.com", "tags": {"hugo-news": {}}}

    with patch.object(main, "load_state", return_value=state), \
         patch.object(main, "save_state"), \
         patch("main.Readwise") as MockRW, \
         patch("main.GitHubClient") as MockGH:
        MockRW.return_value.get_tagged_documents.return_value = [doc]
        main.main()
        MockGH.return_value.create_post.assert_not_called()
