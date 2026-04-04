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


def load_processed():
    try:
        with open(READWISE_JSON, "rb") as f:
            return json.loads(f.read())
    except FileNotFoundError:
        logger.debug(f"File '{READWISE_JSON}' non trovato, si parte da zero.")
        return []


def save_processed(processed):
    with open(READWISE_JSON, "wb") as f:
        f.write(json.dumps(processed, indent=4).encode())


def main():
    tag = os.environ.get("READWISE_TAG", "hugo-news")

    since = (datetime.now() - timedelta(hours=24)).isoformat()

    rw = Readwise()
    documents = rw.get_tagged_documents(tag, since)

    if not documents:
        logger.debug(f"Nessun documento con tag '{tag}' trovato.")
        return

    processed = load_processed()
    new_docs = [d for d in documents if d["id"] not in processed]

    if not new_docs:
        logger.debug("Tutti i documenti trovati sono già stati processati.")
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
            processed.append(doc_id)
            save_processed(processed)
            logger.debug(f"Post pubblicato: {filename}")
        except Exception as e:
            logger.error(f"Errore per '{title}': {e}")
            raise

    logger.debug("Bye!")


if __name__ == "__main__":
    main()
