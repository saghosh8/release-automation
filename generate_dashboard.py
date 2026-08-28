import os
import re
import requests
from datetime import datetime, timezone

OWNER = os.environ.get("OWNER", "saghosh8")

# Edit this list to match your real application repo names
APPS = ["application-one", "application-two"]

# A token is optional for public repos but strongly recommended - the
# Actions API has a low unauthenticated rate limit, and private repos
# require it. Set this as a repo/Actions secret named GITHUB_TOKEN.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# Used to extract tag and branch from the Run details table
IMAGE_TAG_PATTERN = re.compile(r"image_tag\s*\|\s*(\S+)")
BRANCH_PATTERN = re.compile(r"branch\s*\|\s*(\S+)")


def get_workflow_id(app_repo, workflow_file):
    """Look up a workflow's numeric id by its file name."""
    url = f"https://api.github.com/repos/{OWNER}/{app_repo}/actions/workflows/{workflow_file}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception:
        return None


def fmt_date(iso_str):
    if not iso_str:
        return "-"
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str


def extract_deployment_details(summary_text):
    """
    Extract image_tag and branch from the Run details table in the summary.
    Returns dict with 'tag' and 'branch' keys, or None if not found.
    """
    if not summary_text:
        return None
    
    tag_match = IMAGE_TAG_PATTERN.search(summary_text)
    branch_match = BRANCH_PATTERN.search(summary_text)
    
    if tag_match:
        return {
            "tag": tag_match.group(1),
            "branch": branch_match.group(1) if branch_match else "-"
        }
    
    return None


def get_dev_deployments(app_repo):
    """
    Fetch the last 3 successful CD - Dev runs and extract deployment details.
    Returns list of dicts: [{"tag": "...", "branch": "...", "deployed_at": "...", "run_url": "..."}]
    """
    workflow_id = get_workflow_id(app_repo, "cd_dev.yml")
    if not workflow_id:
        return []

    url = f"https://api.github.com/repos/{OWNER}/{app_repo}/actions/workflows/{workflow_id}/runs"
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            params={"status": "success", "per_page": 3},
            timeout=10,
        )
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        
        deployments = []
        for run in runs:
            # Fetch full run details to get the summary/body
            run_url = run.get("url")
            if run_url:
                try:
                    run_detail_resp = requests.get(run_url, headers=HEADERS, timeout=10)
                    run_detail_resp.raise_for_status()
                    run_detail = run_detail_resp.json()
                    summary = run_detail.get("body") or ""
                except Exception:
                    summary = ""
            else:
                summary = ""
            
            details = extract_deployment_details(summary)
            
            if details:
                deployments.append({
                    "tag": details["tag"],
                    "branch": details["branch"],
                    "deployed_at": run.get("run_started_at") or run.get("created_at"),
                    "run_url": run.get("html_url"),
                })
        
        return deployments
    except Exception:
        return []


def build_env_card(app_repo, deployments):
    """Build a card showing current and previous Dev deployments."""
    if not deployments:
        return f"""
    <div class="card">
        <h2>{app_repo}</h2>
        <p class="empty">No successful deployments found.</p>
    </div>
    """

    current = deployments[0]
    previous = deployments[1] if len(deployments) > 1 else None

    previous_html = (
        f"""<div class="row"><span class="label">Previous version</span>
        <span class="value">{previous['tag']}</span></div>
        <div class="row"><span class="label">Previous branch</span>
        <span class="value">{previous['branch']}</span></div>"""
        if previous
        else '<div class="row"><span class="label">Previous version</span><span class="value">-</span></div>'
    )

    history_rows = "".join(
        f"""<tr>
            <td>{d['tag']}</td>
            <td>{d['branch']}</td>
            <td>{fmt_date(d['deployed_at'])}</td>
        </tr>"""
        for d in deployments
    )

    panel_id = f"history-dev-{app_repo.replace('-', '_')}"

    return f"""
    <div class="card">
        <h2>{app_repo}</h2>
        <div class="row"><span class="label">Current version</span>
        <span class="value badge"><a class="value-link" href="{current['run_url']}" target="_blank" rel="noopener">{current['tag']}</a></span></div>
        <div class="row"><span class="label">Current branch</span>
        <span class="value">{current['branch']}</span></div>
        <div class="row"><span class="label">Deployed</span>
        <span class="value">{fmt_date(current['deployed_at'])}</span></div>
        {previous_html}
        <button class="toggle-btn" onclick="document.getElementById('{panel_id}').classList.toggle('open')">
            Check previous versions
        </button>
        <div id="{panel_id}" class="history-panel">
            <table>
                <thead>
                    <tr><th>Version</th><th>Branch</th><th>Deployed</th></tr>
                </thead>
                <tbody>
                    {history_rows}
                </tbody>
            </table>
        </div>
    </div>
    """


def build_html(cards_html):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Dev Deployment Dashboard</title>
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
    .value-link {{ text-decoration: none; color: inherit; }}
    .value-link:hover {{ text-decoration: underline; }}
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
    <h1>Dev Deployment Dashboard</h1>
    <p class="caption">Last refreshed: {now}</p>

    <h3 class="section-title">Deployments</h3>
    <div class="grid">
        {cards_html}
    </div>
</body>
</html>
"""


if __name__ == "__main__":
    cards = ""

    for app in APPS:
        deployments = get_dev_deployments(app)
        cards += build_env_card(app, deployments)

    html = build_html(cards)
    with open("index.html", "w") as f:
        f.write(html)

    print("index.html generated")
