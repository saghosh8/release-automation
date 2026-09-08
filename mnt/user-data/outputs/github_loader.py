"""
devops_assistant/rag/github_loader.py

Pulls real content from GitHub repos (README, workflow YAMLs, PR titles/bodies,
commit messages) for RAG ingestion — replaces sample/dummy data.

Usage:
    from devops_assistant.rag.github_loader import load_github_sources
    docs = load_github_sources(["saghosh8/release-automation",
                                 "saghosh8/application-one",
                                 "saghosh8/application-two"])
    # docs -> List[Dict]: {"text": ..., "source": ..., "repo": ...}
"""

import os
import base64
import requests

GITHUB_API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")  # set as repo/action secret

HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
}


def _get(url, params=None):
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _get_readme(repo: str):
    try:
        data = _get(f"{GITHUB_API}/repos/{repo}/readme")
        content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        return [{"text": content, "source": f"{repo}/README.md", "repo": repo}]
    except requests.HTTPError:
        return []


def _get_workflow_yamls(repo: str):
    docs = []
    try:
        contents = _get(f"{GITHUB_API}/repos/{repo}/contents/.github/workflows")
    except requests.HTTPError:
        return docs
    for item in contents:
        if item["type"] != "file" or not item["name"].endswith((".yml", ".yaml")):
            continue
        try:
            file_data = _get(item["url"])
            text = base64.b64decode(file_data["content"]).decode("utf-8", errors="ignore")
            docs.append({
                "text": text,
                "source": f"{repo}/.github/workflows/{item['name']}",
                "repo": repo,
            })
        except requests.HTTPError:
            continue
    return docs


def _get_pull_requests(repo: str, limit: int = 20):
    docs = []
    try:
        prs = _get(f"{GITHUB_API}/repos/{repo}/pulls",
                    params={"state": "all", "per_page": limit})
    except requests.HTTPError:
        return docs
    for pr in prs:
        body = pr.get("body") or ""
        text = f"PR #{pr['number']}: {pr['title']}\n\n{body}"
        docs.append({
            "text": text,
            "source": f"{repo}/pull/{pr['number']}",
            "repo": repo,
        })
    return docs


def _get_commits(repo: str, limit: int = 30):
    docs = []
    try:
        commits = _get(f"{GITHUB_API}/repos/{repo}/commits",
                        params={"per_page": limit})
    except requests.HTTPError:
        return docs
    for c in commits:
        msg = c.get("commit", {}).get("message", "")
        sha = c.get("sha", "")[:7]
        docs.append({
            "text": msg,
            "source": f"{repo}/commit/{sha}",
            "repo": repo,
        })
    return docs


def load_github_sources(repos: list[str]) -> list[dict]:
    """Fetch README, workflow YAMLs, PRs, and commits from each repo."""
    all_docs = []
    for repo in repos:
        all_docs.extend(_get_readme(repo))
        all_docs.extend(_get_workflow_yamls(repo))
        all_docs.extend(_get_pull_requests(repo))
        all_docs.extend(_get_commits(repo))
    return all_docs


if __name__ == "__main__":
    repos = [
        "saghosh8/release-automation",
        "saghosh8/application-one",
        "saghosh8/application-two",
    ]
    docs = load_github_sources(repos)
    print(f"Loaded {len(docs)} documents")
    for d in docs[:5]:
        print("-", d["source"])
