import json
import logging
import os
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from github_client import GitHubClient
from hugo_post import generate_post
from readwise import Readwise
from url_cleaner import clean_url

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")

READWISE_JSON = "readwise.json"
FALLBACK_DAYS = 7


def load_state():
    try:
        with open(READWISE_JSON, "rb") as f:
            data = json.loads(f.read())
        if isinstance(data, list):
            # migrazione dal vecchio formato (array piatto)
            return {"last_fetch": None, "processed_ids": data}
        return data
    except FileNotFoundError:
        logger.debug(f"File '{READWISE_JSON}' non trovato, si parte da zero.")
        return {"last_fetch": None, "processed_ids": []}


def save_state(state):
    with open(READWISE_JSON, "wb") as f:
        f.write(json.dumps(state, indent=4).encode())


def main():
    tag = os.environ.get("READWISE_TAG", "hugo-news")

    state = load_state()
    since = state["last_fetch"] or (datetime.now() - timedelta(days=FALLBACK_DAYS)).isoformat()
    fetch_started_at = datetime.now().isoformat()

    rw = Readwise()
    documents = rw.get_tagged_documents(tag, since)

    state["last_fetch"] = fetch_started_at

    if not documents:
        logger.debug(f"Nessun documento con tag '{tag}' trovato.")
        save_state(state)
        return

    new_docs = [d for d in documents if d["id"] not in state["processed_ids"]]

    if not new_docs:
        logger.debug("Tutti i documenti trovati sono già stati processati.")
        save_state(state)
        return

    gh = GitHubClient()

    for document in new_docs:
        doc_id = document["id"]
        title = document["title"]
        source_url = clean_url(document.get("source_url") or "")
        doc_tags = list((document.get("tags") or {}).keys())

        logger.debug(f"Elaborazione: {title!r}")

        highlights = rw.get_highlights(source_url, title)

        filename, content = generate_post(document, highlights, source_url, doc_tags)
        commit_msg = f"news: {title}"

        try:
            gh.create_post(filename, content, commit_msg)
            state["processed_ids"].append(doc_id)
            save_state(state)
            logger.debug(f"Post pubblicato: {filename}")
        except Exception as e:
            logger.error(f"Errore per '{title}': {e}")
            raise

    logger.debug("Bye!")


if __name__ == "__main__":
    main()
