import requests
from datetime import datetime, timezone

OWNER = "saghosh8"
REPO = "release-automation"

WORKFLOWS = {
    "Onboarding": "create-app-repos.yml",
    "Release Branch": "create-release-branch.yml",
    "CI & Tagging": "prod_ci.yml",
    "Release Notes": "publish-release-notes.yml",
    "Prod Deployment": "prod_cd.yml",
}

STATUS_COLOR = {
    "success": "#2ea44f",
    "failure": "#d73a49",
    "in_progress": "#dbab09",
    "queued": "#dbab09",
    "cancelled": "#8b949e",
    "unknown": "#8b949e",
}


def get_latest_run(workflow_file):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{workflow_file}/runs"
    try:
        resp = requests.get(url, params={"per_page": 1}, timeout=10)
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        if not runs:
            return {"status": "unknown", "html_url": None, "branch": None}
        run = runs[0]
        status = run["conclusion"] or run["status"]
        return {
            "status": status,
            "html_url": run["html_url"],
            "branch": run["head_branch"],
        }
    except Exception:
        return {"status": "unknown", "html_url": None, "branch": None}


def build_html(results):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cards = ""
    for stage, data in results.items():
        color = STATUS_COLOR.get(data["status"], "#8b949e")
        branch = f"<p class='branch'>Branch: {data['branch']}</p>" if data["branch"] else ""
        link = f"<a href='{data['html_url']}' target='_blank'>View run</a>" if data["html_url"] else ""
        cards += f"""
        <div class="card">
          <h3>{stage}</h3>
          <div class="status" style="color:{color}">&#9679; {data['status']}</div>
          {branch}
          {link}
        </div>
        """

    success_count = sum(1 for r in results.values() if r["status"] == "success")
    failure_count = sum(1 for r in results.values() if r["status"] == "failure")
    other_count = len(results) - success_count - failure_count

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Release Automation Dashboard</title>
<style>
  body {{ font-family: -apple-system, Arial, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.2rem; }}
  .caption {{ color: #8b949e; margin-bottom: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem; }}
  .card h3 {{ margin: 0 0 0.5rem; font-size: 0.95rem; }}
  .status {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 0.4rem; }}
  .branch {{ font-size: 0.8rem; color: #8b949e; margin: 0.2rem 0; }}
  a {{ color: #58a6ff; font-size: 0.85rem; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .summary {{ margin-top: 2rem; display: flex; gap: 2rem; }}
  .metric {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem 1.5rem; }}
  .metric .num {{ font-size: 1.5rem; font-weight: 600; }}
  .metric .label {{ font-size: 0.8rem; color: #8b949e; }}
</style>
</head>
<body>
  <h1>Release Automation Dashboard</h1>
  <p class="caption">Repo: {OWNER}/{REPO} &middot; Last refreshed: {now}</p>

  <div class="grid">
    {cards}
  </div>

  <div class="summary">
    <div class="metric"><div class="num" style="color:#2ea44f">{success_count}</div><div class="label">Passing</div></div>
    <div class="metric"><div class="num" style="color:#d73a49">{failure_count}</div><div class="label">Failing</div></div>
    <div class="metric"><div class="num" style="color:#dbab09">{other_count}</div><div class="label">In progress / unknown</div></div>
  </div>
</body>
</html>
"""


if __name__ == "__main__":
    results = {stage: get_latest_run(wf) for stage, wf in WORKFLOWS.items()}
    html = build_html(results)
    with open("index.html", "w") as f:
        f.write(html)
    print("index.html generated")
