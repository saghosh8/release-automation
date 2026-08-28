import os
import re
import requests
from datetime import datetime, timezone

OWNER = os.environ.get("OWNER", "saghosh8")

# Edit this list to match your real application repo names
APPS = ["application-one", "application-two"]

# Edit this to match your release branch prefix (e.g. "SG_RELEASE", "AB_RELEASE", etc.)
RELEASE_PREFIX = os.environ.get("RELEASE_PREFIX", "SG_RELEASE")

# A token is optional for public repos but strongly recommended - the
# Actions API has a low unauthenticated rate limit, and private repos
# require it. Set this as a repo/Actions secret named GITHUB_TOKEN.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# Maps the dashboard environment name -> the exact "name:" of the CD
# workflow in each app repo's .github/workflows/*.yml
ENV_WORKFLOWS = {
    "Dev": "CD - Dev",
    "UAT": "CD - UAT",
    "PROD": "CD - Prod",
}

# Used to pull the deployed tag back out of a run's summary (see note in
# get_latest_deployment below). Matches the same tag convention used
# elsewhere in this script: <version>-release-<sha>
TAG_PATTERN = re.compile(r"[\w.]+-release-[0-9a-fA-F]+")

# Maps environment name to the section header in the workflow run summary
SUMMARY_SECTIONS = {
    "Dev": "Deploy to Dev summary",
    "UAT": "Deploy to UAT summary",
    "PROD": "Deploy to Prod summary",
}


def get_releases(app_repo, count=5):
    """Fetch the last `count` releases for an application repo."""
    url = f"https://api.github.com/repos/{OWNER}/{app_repo}/releases"
    try:
        resp = requests.get(url, headers=HEADERS, params={"per_page": count}, timeout=10)
        resp.raise_for_status()
        releases = resp.json()
        return [
            {
                "version": r["tag_name"],
                "branch": derive_branch(r["tag_name"]),
                "published_at": r["published_at"],
            }
            for r in releases
        ]
    except Exception:
        return []


def derive_branch(tag_name):
    """Tag format is <version>-release-<short-sha>; branch is release/<RELEASE_PREFIX>_<version>."""
    version = tag_name.split("-release-")[0]
    return f"release/{RELEASE_PREFIX}_{version}"


def fmt_date(iso_str):
    if not iso_str:
        return "-"
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str


_workflow_id_cache = {}


def get_workflow_id(app_repo, workflow_name):
    """Look up a workflow's numeric id by its display name (name: in the yml), cached per repo."""
    cache_key = (app_repo, workflow_name)
    if cache_key in _workflow_id_cache:
        return _workflow_id_cache[cache_key]

    url = f"https://api.github.com/repos/{OWNER}/{app_repo}/actions/workflows"
    try:
        resp = requests.get(url, headers=HEADERS, params={"per_page": 100}, timeout=10)
        resp.raise_for_status()
        for wf in resp.json().get("workflows", []):
            _workflow_id_cache[(app_repo, wf["name"])] = wf["id"]
    except Exception:
        pass

    return _workflow_id_cache.get(cache_key)


def extract_tag_from_summary(summary_text, env_name):
    """
    Extract the tag from a workflow run summary section.
    
    Looks for the section header [Deploy to <env> summary] and extracts
    the first tag matching the pattern <version>-release-<sha>.
    """
    if not summary_text or not env_name:
        return None
    
    section_header = SUMMARY_SECTIONS.get(env_name)
    if not section_header:
        return None
    
    # Look for the section header (case-insensitive, with or without brackets)
    pattern = rf"\[?{re.escape(section_header)}\]?.*?(?:\n|$)(.*?)(?=\[|$)"
    match = re.search(pattern, summary_text, re.IGNORECASE | re.DOTALL)
    
    if match:
        section_content = match.group(1)
        tag_match = TAG_PATTERN.search(section_content)
        if tag_match:
            return tag_match.group(0)
    
    return None


def get_latest_deployment(app_repo, workflow_name, env_name=None):
    """
    Return the tag deployed by the most recent *successful* run of the given
    CD workflow (e.g. "CD - Dev"), or None if there is no successful run.

    The deployed tag is extracted from the workflow run summary. For this to work,
    each CD workflow should include a step that creates a job summary with a section
    like:
    
        [Deploy to Dev summary]
        Deployed tag: v1.0.0-release-abc123
        
    The env_name parameter maps to the summary section:
    - "Dev" -> "[Deploy to Dev summary]"
    - "UAT" -> "[Deploy to UAT summary]"
    - "PROD" -> "[Deploy to Prod summary]"
    """
    workflow_id = get_workflow_id(app_repo, workflow_name)
    if not workflow_id:
        return None

    url = f"https://api.github.com/repos/{OWNER}/{app_repo}/actions/workflows/{workflow_id}/runs"
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            # only successful runs, most recent first, we just need the latest one
            params={"status": "success", "per_page": 1},
            timeout=10,
        )
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        if not runs:
            return None
        run = runs[0]
    except Exception:
        return None

    # Try to extract tag from summary if env_name is provided
    tag = None
    if env_name:
        summary_text = run.get("body") or ""
        tag = extract_tag_from_summary(summary_text, env_name)
    
    # Fallback: if no tag found in summary, return None or indicate missing data
    if not tag:
        tag = "-"

    return {
        "tag": tag,
        "run_url": run.get("html_url"),
        "deployed_at": run.get("run_started_at") or run.get("created_at"),
    }


def build_env_card(app_repo, env_results):
    """env_results: dict of env_name -> get_latest_deployment(...) result, or None."""
    rows = ""
    for env_name in ENV_WORKFLOWS:
        result = env_results.get(env_name)
        if result:
            rows += f"""
            <div class="row">
                <span class="label">{env_name}</span>
                <span class="env-value">
                    <a class="value badge tag-link" href="{result['run_url']}" target="_blank" rel="noopener">{result['tag']}</a>
                    <span class="deployed-at">{fmt_date(result['deployed_at'])}</span>
                </span>
            </div>"""
        else:
            rows += f"""
            <div class="row">
                <span class="label">{env_name}</span>
                <span class="value empty">No successful deployment</span>
            </div>"""

    return f"""
    <div class="card">
        <h2>{app_repo}</h2>
        {rows}
    </div>
    """


def build_app_card(app_repo, releases, idx):
    if not releases:
        return f"""
        <div class="card">
            <h2>{app_repo}</h2>
            <p class="empty">No releases found.</p>
        </div>
        """

    current = releases[0]
    previous = releases[1] if len(releases) > 1 else None

    previous_html = (
        f"""<div class="row"><span class="label">Previous version</span>
        <span class="value">{previous['version']}</span></div>
        <div class="row"><span class="label">Previous release branch</span>
        <span class="value">{previous['branch']}</span></div>"""
        if previous
        else '<div class="row"><span class="label">Previous version</span><span class="value">-</span></div>'
    )

    history_rows = "".join(
        f"""<tr>
            <td>{r['version']}</td>
            <td>{r['branch']}</td>
            <td>{fmt_date(r['published_at'])}</td>
        </tr>"""
        for r in releases
    )

    panel_id = f"history-{idx}"

    return f"""
    <div class="card">
        <h2>{app_repo}</h2>
        <div class="row"><span class="label">Current version</span>
        <span class="value badge">{current['version']}</span></div>
        <div class="row"><span class="label">Current release branch</span>
        <span class="value">{current['branch']}</span></div>
        {previous_html}
        <button class="toggle-btn" onclick="document.getElementById('{panel_id}').classList.toggle('open')">
            Check previous versions
        </button>
        <div id="{panel_id}" class="history-panel">
            <table>
                <thead>
                    <tr><th>Version</th><th>Release branch</th><th>Published</th></tr>
                </thead>
                <tbody>
                    {history_rows}
                </tbody>
            </table>
        </div>
    </div>
    """


def build_html(env_cards_html, cards_html):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Release Automation Dashboard</title>
<style>
    body {{ font-family: -apple-system, Arial, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 2rem; }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.2rem; }}
    h2 {{ font-size: 1.1rem; margin: 0 0 1rem; }}
    h3.section-title {{ font-size: 1rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.05em;
        margin: 2.5rem 0 1rem; border-bottom: 1px solid #21262d; padding-bottom: 0.5rem; }}
    h3.section-title:first-of-type {{ margin-top: 0; }}
    .caption {{ color: #8b949e; margin-bottom: 2rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.25rem; }}
    .row {{ display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid #21262d; font-size: 0.9rem; }}
    .row:last-of-type {{ border-bottom: none; }}
    .label {{ color: #8b949e; }}
    .value {{ font-family: monospace; }}
    .env-value {{ display: flex; align-items: center; gap: 0.6rem; }}
    .deployed-at {{ color: #8b949e; font-size: 0.78rem; }}
    .tag-link {{ text-decoration: none; }}
    .tag-link:hover {{ text-decoration: underline; }}
    .badge {{ background: #2ea44f22; color: #3fb950; padding: 2px 8px; border-radius: 4px; }}
    .toggle-btn {{ margin-top: 1rem; background: transparent; border: 1px solid #30363d; color: #58a6ff;
        padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }}
    .toggle-btn:hover {{ background: #21262d; }}
    .history-panel {{ display: none; margin-top: 1rem; }}
    .history-panel.open {{ display: block; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    th, td {{ text-align: left; padding: 0.4rem 0.5rem; border-bottom: 1px solid #21262d; }}
    th {{ color: #8b949e; font-weight: 500; }}
    td {{ font-family: monospace; }}
    .empty {{ color: #8b949e; font-size: 0.9rem; }}
</style>
</head>
<body>
    <h1>Release Automation Dashboard</h1>
    <p class="caption">Last refreshed: {now}</p>

    <h3 class="section-title">Environments (Dev / UAT / PROD)</h3>
    <div class="grid">
        {env_cards_html}
    </div>

    <h3 class="section-title">Releases</h3>
    <div class="grid">
        {cards_html}
    </div>
</body>
</html>
"""


if __name__ == "__main__":
    env_cards = ""
    cards = ""

    for i, app in enumerate(APPS):
        env_results = {}
        for env_name, workflow_name in ENV_WORKFLOWS.items():
            env_results[env_name] = get_latest_deployment(app, workflow_name, env_name)
        env_cards += build_env_card(app, env_results)

        releases = get_releases(app)
        cards += build_app_card(app, releases, i)

    html = build_html(env_cards, cards)
    with open("index.html", "w") as f:
        f.write(html)

    print("index.html generated")
