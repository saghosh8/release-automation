import os
import requests
from datetime import datetime, timezone

OWNER = os.environ.get("OWNER", "saghosh8")

# Edit this list to match your real application repo names
APPS = ["application-one", "application-two"]


def get_releases(app_repo, count=5):
    """Fetch the last `count` releases for an application repo."""
    url = f"https://api.github.com/repos/{OWNER}/{app_repo}/releases"
    try:
        resp = requests.get(url, params={"per_page": count}, timeout=10)
        resp.raise_for_status()
        releases = resp.json()
        return [
            {
                "version": r["tag_name"],
                "branch": r["target_commitish"],
                "published_at": r["published_at"],
            }
            for r in releases
        ]
    except Exception:
        return []


def fmt_date(iso_str):
    if not iso_str:
        return "-"
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return iso_str


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


def build_html(cards_html):
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
  .caption {{ color: #8b949e; margin-bottom: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.25rem; }}
  .row {{ display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #21262d; font-size: 0.9rem; }}
  .row:last-of-type {{ border-bottom: none; }}
  .label {{ color: #8b949e; }}
  .value {{ font-family: monospace; }}
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
  <div class="grid">
    {cards_html}
  </div>
</body>
</html>
"""


if __name__ == "__main__":
    cards = ""
    for i, app in enumerate(APPS):
        releases = get_releases(app)
        cards += build_app_card(app, releases, i)

    html = build_html(cards)
    with open("index.html", "w") as f:
        f.write(html)
    print("index.html generated")
