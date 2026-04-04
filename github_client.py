import base64
import logging
import os

import requests

logger = logging.getLogger("github_client")


class GitHubClient:
    def __init__(self):
        self.token = os.environ["GITHUB_TOKEN_WEBSITE"]
        self.owner = os.environ["GITHUB_REPO_OWNER"]
        self.repo = os.environ["GITHUB_REPO_NAME"]
        self.api_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_post(self, filename, content, commit_message):
        path = f"content/blog/{filename}"
        url = f"{self.api_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        payload = {"message": commit_message, "content": encoded}
        sha = self._get_file_sha(path)
        if sha:
            payload["sha"] = sha
            logger.debug(f"File esistente, aggiorno: {path}")
        response = requests.put(url, json=payload, headers=self.headers)
        if response.status_code in (200, 201):
            logger.debug(f"File {'aggiornato' if sha else 'creato'}: {path}")
            return True
        response.raise_for_status()

    def _get_file_sha(self, path):
        url = f"{self.api_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("sha")
        return None
