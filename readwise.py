import logging
import os
import time

import requests

logger = logging.getLogger("readwise")

_RETRY_ATTEMPTS = 5
_RETRY_FALLBACK_WAIT = 60


class Readwise:
    def __init__(self):
        self.api_key = os.environ["READWISE_ACCESS_TOKEN"]
        self.v3_url = "https://readwise.io/api/v3/"
        self.v2_url = "https://readwise.io/api/v2/"
        self.headers = {"Authorization": f"Token {self.api_key}"}
        logger.debug("Readwise inizializzato!")

    def get_tagged_documents(self, tag, updated_after):
        documents = self._list_documents(updated_after)
        tagged = [d for d in documents if d.get("tags") and tag in d["tags"]]
        logger.debug(f"Documenti con tag '{tag}': {len(tagged)}")
        return tagged

    def _list_documents(self, updated_after):
        url = f"{self.v3_url}list/"
        params = {"updatedAfter": updated_after}
        results = []
        while True:
            data = self._get(url, params)
            results.extend(data.get("results", []))
            cursor = data.get("nextPageCursor")
            if not cursor:
                break
            params = {"pageCursor": cursor}
        logger.debug(f"Documenti totali recuperati: {len(results)}")
        return results

    def get_highlights(self, source_url, title):
        book = self._find_book(source_url, title)
        if not book:
            logger.debug(f"Nessun libro v2 trovato per: {title!r}")
            return []
        highlights = self._list_highlights(book["id"])
        logger.debug(f"Highlights trovate per '{title}': {len(highlights)}")
        return highlights

    def _find_book(self, source_url, title):
        url = f"{self.v2_url}books/"
        params = {"category": "articles", "page_size": 100}
        title_match = None
        while True:
            data = self._get(url, params)
            for book in data.get("results", []):
                if source_url and book.get("source_url") == source_url:
                    return book
                if title_match is None and book.get("title", "").strip() == title.strip():
                    title_match = book
            if not data.get("next"):
                break
            params["page"] = params.get("page", 1) + 1
        return title_match

    def _list_highlights(self, book_id):
        url = f"{self.v2_url}highlights/"
        params = {"book_id": book_id, "page_size": 100}
        results = []
        while True:
            data = self._get(url, params)
            results.extend(data.get("results", []))
            if not data.get("next"):
                break
            params["page"] = params.get("page", 1) + 1
        return results

    def _get(self, url, params):
        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", _RETRY_FALLBACK_WAIT))
                logger.debug(f"Rate limit (429), attendo {wait}s (tentativo {attempt}/{_RETRY_ATTEMPTS})...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        raise Exception(f"Rate limit persistente dopo {_RETRY_ATTEMPTS} tentativi: {url}")
