import os
import html
import requests
from datetime import datetime, timezone

OWNER = os.environ.get("OWNER", "saghosh8")

# Edit this list to match your real application repo names
APPS = ["application-one", "application-two"]

# Edit this to match your release branch prefix
RELEASE_PREFIX = os.environ.get("RELEASE_PREFIX", "SG_RELEASE")


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
                "branch": derive_branch(r["tag_name"]),
                "published_at": r["published_at"],
            }
            for r in releases
        ]
    except Exception:
        return []


def derive_branch(tag_name):
    """Tag format: <version>-release-<short-sha>."""
    version = tag_name.split("-release-")[0]
    return f"release/{RELEASE_PREFIX}_{version}"


def fmt_date(iso_str):
    if not iso_str:
        return "-"

    try:
        return datetime.fromisoformat(
            iso_str.replace("Z", "+00:00")
        ).strftime("%d %b %Y")
    except Exception:
        return iso_str


def build_app_card(app_repo, releases, idx):
    safe_repo = html.escape(app_repo)

    if not releases:
        return f"""
        <article class="app-card empty-card">
            <div class="app-card-header">
                <div class="app-icon">⌘</div>
                <div>
                    <h2>{safe_repo}</h2>
                    <span class="status status-muted">No releases</span>
                </div>
            </div>
            <p class="empty">No GitHub releases found for this application.</p>
        </article>
        """

    current = releases[0]
    previous = releases[1] if len(releases) > 1 else None
    panel_id = f"history-{idx}"

    current_version = html.escape(current["version"])
    current_branch = html.escape(current["branch"])

    previous_html = ""
    if previous:
        previous_html = f"""
        <div class="mini-stat">
            <span>Previous version</span>
            <strong>{html.escape(previous["version"])}</strong>
        </div>
        """
    else:
        previous_html = """
        <div class="mini-stat">
            <span>Previous version</span>
            <strong>—</strong>
        </div>
        """

    history_rows = "".join(
        f"""
        <tr>
            <td><span class="version-pill">{html.escape(r["version"])}</span></td>
            <td class="mono">{html.escape(r["branch"])}</td>
            <td>{fmt_date(r["published_at"])}</td>
        </tr>
        """
        for r in releases
    )

    return f"""
    <article class="app-card">
        <div class="app-card-header">
            <div class="app-icon">⌘</div>
            <div class="app-title">
                <h2>{safe_repo}</h2>
                <span class="status"><span class="status-dot"></span> Active release</span>
            </div>
            <div class="release-count">{len(releases)} releases</div>
        </div>

        <div class="current-release">
            <div class="eyebrow">CURRENT RELEASE</div>
            <div class="version">{current_version}</div>

            <div class="branch">
                <span class="branch-icon">⑂</span>
                <span>{current_branch}</span>
            </div>
        </div>

        <div class="mini-grid">
            {previous_html}
            <div class="mini-stat">
                <span>Published</span>
                <strong>{fmt_date(current["published_at"])}</strong>
            </div>
        </div>

        <button class="history-button"
                onclick="toggleHistory('{panel_id}', this)">
            <span>View release history</span>
            <span class="chevron">⌄</span>
        </button>

        <div id="{panel_id}" class="history-panel">
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>VERSION</th>
                            <th>RELEASE BRANCH</th>
                            <th>PUBLISHED</th>
                        </tr>
                    </thead>
                    <tbody>
                        {history_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </article>
    """


def build_html(app_data):
    now = datetime.now(timezone.utc).strftime("%d %b %Y • %H:%M UTC")

    total_apps = len(APPS)
    active_apps = sum(1 for releases in app_data.values() if releases)
    total_releases = sum(len(releases) for releases in app_data.values())

    cards_html = "".join(
        build_app_card(app, app_data.get(app, []), idx)
        for idx, app in enumerate(APPS)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Release Automation Dashboard</title>

<style>
    :root {{
        --bg: #04152d;
        --bg-deep: #021025;
        --panel: rgba(6, 31, 64, 0.82);
        --panel-strong: rgba(7, 37, 76, 0.95);
        --border: rgba(62, 169, 255, 0.20);
        --border-bright: rgba(58, 190, 255, 0.48);
        --text: #eef8ff;
        --muted: #8da9c5;
        --blue: #32c7ff;
        --blue-2: #238cff;
        --cyan: #6de7ff;
        --green: #45e6a2;
        --shadow: rgba(0, 126, 255, 0.16);
    }}

    * {{
        box-sizing: border-box;
    }}

    body {{
        margin: 0;
        min-height: 100vh;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                     BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--text);
        background:
            radial-gradient(circle at 15% 10%, rgba(20, 126, 255, 0.16), transparent 28%),
            radial-gradient(circle at 85% 20%, rgba(0, 208, 255, 0.10), transparent 24%),
            linear-gradient(135deg, var(--bg-deep), var(--bg) 50%, #031b39);
        overflow-x: hidden;
    }}

    body::before {{
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        opacity: 0.28;
        background-image:
            linear-gradient(rgba(67, 184, 255, 0.045) 1px, transparent 1px),
            linear-gradient(90deg, rgba(67, 184, 255, 0.045) 1px, transparent 1px);
        background-size: 48px 48px;
        mask-image: linear-gradient(to bottom, black, transparent 82%);
    }}

    .shell {{
        width: min(1180px, calc(100% - 36px));
        margin: 0 auto;
        padding: 38px 0 56px;
        position: relative;
    }}

    .topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        margin-bottom: 30px;
    }}

    .brand {{
        display: flex;
        align-items: center;
        gap: 16px;
    }}

    .brand-icon {{
        width: 58px;
        height: 58px;
        border-radius: 17px;
        display: grid;
        place-items: center;
        font-size: 28px;
        font-weight: 800;
        color: white;
        background: linear-gradient(145deg, #159cff, #0750ae);
        border: 1px solid rgba(111, 220, 255, 0.55);
        box-shadow:
            0 0 28px rgba(30, 171, 255, 0.25),
            inset 0 1px 0 rgba(255,255,255,0.18);
    }}

    .brand h1 {{
        margin: 0;
        font-size: clamp(1.65rem, 3vw, 2.35rem);
        letter-spacing: 0.03em;
        font-weight: 760;
    }}

    .brand p {{
        margin: 5px 0 0;
        color: var(--muted);
        font-size: 0.88rem;
    }}

    .refresh {{
        color: #a9c7df;
        font-size: 0.78rem;
        padding: 10px 14px;
        border: 1px solid var(--border);
        background: rgba(4, 25, 52, 0.65);
        border-radius: 999px;
        white-space: nowrap;
    }}

    .hero {{
        position: relative;
        padding: 30px;
        border: 1px solid var(--border-bright);
        border-radius: 25px;
        background:
            linear-gradient(145deg, rgba(9, 52, 101, 0.72), rgba(3, 24, 52, 0.78));
        box-shadow:
            0 24px 70px rgba(0, 0, 0, 0.26),
            0 0 55px var(--shadow),
            inset 0 1px 0 rgba(255,255,255,0.07);
        overflow: hidden;
        margin-bottom: 24px;
    }}

    .hero::after {{
        content: "";
        position: absolute;
        width: 280px;
        height: 280px;
        right: -100px;
        top: -140px;
        border-radius: 50%;
        background: rgba(0, 192, 255, 0.12);
        filter: blur(8px);
    }}

    .eyebrow {{
        color: var(--cyan);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.16em;
    }}

    .hero h2 {{
        margin: 8px 0 8px;
        font-size: clamp(1.4rem, 3vw, 2.15rem);
    }}

    .hero p {{
        margin: 0;
        max-width: 720px;
        color: var(--muted);
        line-height: 1.6;
        font-size: 0.92rem;
    }}

    .stats {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-top: 25px;
    }}

    .stat {{
        padding: 18px;
        border-radius: 17px;
        background: rgba(2, 20, 44, 0.62);
        border: 1px solid rgba(83, 184, 255, 0.16);
    }}

    .stat-label {{
        color: var(--muted);
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}

    .stat-value {{
        margin-top: 7px;
        font-size: 1.7rem;
        font-weight: 760;
    }}

    .stat-value.green {{
        color: var(--green);
    }}

    .section-head {{
        display: flex;
        align-items: end;
        justify-content: space-between;
        margin: 28px 2px 14px;
    }}

    .section-head h2 {{
        margin: 0;
        font-size: 1.1rem;
    }}

    .section-head span {{
        color: var(--muted);
        font-size: 0.78rem;
    }}

    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(390px, 1fr));
        gap: 18px;
    }}

    .app-card {{
        border: 1px solid var(--border);
        border-radius: 22px;
        background:
            linear-gradient(150deg, rgba(7, 39, 78, 0.88), rgba(3, 24, 51, 0.92));
        box-shadow:
            0 16px 45px rgba(0, 0, 0, 0.20),
            inset 0 1px 0 rgba(255,255,255,0.04);
        overflow: hidden;
        transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
    }}

    .app-card:hover {{
        transform: translateY(-3px);
        border-color: rgba(72, 193, 255, 0.42);
        box-shadow:
            0 20px 55px rgba(0, 0, 0, 0.25),
            0 0 30px rgba(20, 148, 255, 0.09);
    }}

    .app-card-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 21px 21px 17px;
        border-bottom: 1px solid rgba(74, 169, 232, 0.11);
    }}

    .app-icon {{
        width: 42px;
        height: 42px;
        display: grid;
        place-items: center;
        border-radius: 12px;
        color: var(--cyan);
        font-size: 21px;
        background: rgba(38, 154, 255, 0.12);
        border: 1px solid rgba(69, 191, 255, 0.20);
    }}

    .app-title {{
        min-width: 0;
        flex: 1;
    }}

    .app-title h2 {{
        margin: 0 0 5px;
        font-size: 1rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .status {{
        color: #8fc4df;
        font-size: 0.70rem;
    }}

    .status-dot {{
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--green);
        box-shadow: 0 0 8px rgba(69, 230, 162, 0.65);
        margin-right: 5px;
    }}

    .status-muted {{
        color: var(--muted);
    }}

    .release-count {{
        color: #78a8c8;
        font-size: 0.72rem;
        white-space: nowrap;
    }}

    .current-release {{
        padding: 22px 21px 18px;
    }}

    .version {{
        margin-top: 5px;
        font-size: clamp(2rem, 5vw, 2.65rem);
        line-height: 1;
        font-weight: 780;
        letter-spacing: -0.04em;
    }}

    .branch {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        margin-top: 13px;
        max-width: 100%;
        padding: 7px 10px;
        border-radius: 9px;
        color: #9ed8f7;
        background: rgba(0, 143, 255, 0.09);
        border: 1px solid rgba(74, 184, 255, 0.14);
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.74rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    .branch-icon {{
        color: var(--cyan);
    }}

    .mini-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        padding: 0 21px 18px;
    }}

    .mini-stat {{
        padding: 13px;
        border-radius: 13px;
        background: rgba(1, 17, 38, 0.52);
        border: 1px solid rgba(65, 160, 220, 0.10);
    }}

    .mini-stat span {{
        display: block;
        color: var(--muted);
        font-size: 0.68rem;
        margin-bottom: 5px;
    }}

    .mini-stat strong {{
        font-size: 0.82rem;
        font-weight: 650;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        display: block;
    }}

    .history-button {{
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 21px;
        border: 0;
        border-top: 1px solid rgba(72, 169, 229, 0.11);
        color: #9fdcff;
        background: rgba(1, 16, 35, 0.34);
        cursor: pointer;
        font: inherit;
        font-size: 0.78rem;
        text-align: left;
    }}

    .history-button:hover {{
        background: rgba(26, 126, 210, 0.09);
    }}

    .chevron {{
        font-size: 1rem;
        transition: transform 160ms ease;
    }}

    .history-button.open .chevron {{
        transform: rotate(180deg);
    }}

    .history-panel {{
        display: none;
        padding: 0 21px 20px;
        background: rgba(1, 15, 33, 0.30);
    }}

    .history-panel.open {{
        display: block;
    }}

    .table-wrap {{
        overflow-x: auto;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.72rem;
    }}

    th, td {{
        padding: 10px 7px;
        text-align: left;
        border-bottom: 1px solid rgba(71, 159, 213, 0.10);
        white-space: nowrap;
    }}

    th {{
        color: #6f9bbb;
        font-size: 0.62rem;
        letter-spacing: 0.08em;
    }}

    td {{
        color: #a9c6dc;
    }}

    .mono {{
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}

    .version-pill {{
        display: inline-block;
        padding: 4px 7px;
        border-radius: 7px;
        color: #b6e7ff;
        background: rgba(24, 145, 226, 0.11);
        border: 1px solid rgba(69, 180, 240, 0.13);
    }}

    .empty-card {{
        padding-bottom: 22px;
    }}

    .empty {{
        color: var(--muted);
        margin: 18px 21px 0;
        font-size: 0.82rem;
    }}

    .footer {{
        margin-top: 26px;
        text-align: center;
        color: #587d9d;
        font-size: 0.72rem;
    }}

    @media (max-width: 800px) {{
        .stats {{
            grid-template-columns: repeat(2, 1fr);
        }}

        .topbar {{
            align-items: flex-start;
            flex-direction: column;
        }}

        .refresh {{
            align-self: flex-start;
        }}
    }}

    @media (max-width: 520px) {{
        .shell {{
            width: min(100% - 22px, 1180px);
            padding-top: 22px;
        }}

        .hero {{
            padding: 22px;
        }}

        .grid {{
            grid-template-columns: 1fr;
        }}

        .stats {{
            gap: 9px;
        }}

        .stat {{
            padding: 14px;
        }}

        .stat-value {{
            font-size: 1.4rem;
        }}
    }}
</style>
</head>

<body>
<div class="shell">

    <header class="topbar">
        <div class="brand">
            <div class="brand-icon">↗</div>
            <div>
                <h1>Release Dashboard</h1>
                <p>CI/CD release management dashboard</p>
            </div>
        </div>
        <div class="refresh">Last refreshed · {now}</div>
    </header>

    <section class="hero">
        <div class="eyebrow">RELEASE OPERATIONS</div>
        <h2>Application Release Overview</h2>
        <p>
            Monitor current versions, release branches and recent release
            history across your application repositories.
        </p>

        <div class="stats">
            <div class="stat">
                <div class="stat-label">Applications</div>
                <div class="stat-value">{total_apps}</div>
            </div>

            <div class="stat">
                <div class="stat-label">Active Releases</div>
                <div class="stat-value green">{active_apps}</div>
            </div>

            <div class="stat">
                <div class="stat-label">Release History</div>
                <div class="stat-value">{total_releases}</div>
            </div>

            <div class="stat">
                <div class="stat-label">Branch Prefix</div>
                <div class="stat-value" style="font-size:1.05rem;">{html.escape(RELEASE_PREFIX)}</div>
            </div>
        </div>
    </section>

    <div class="section-head">
        <h2>Applications</h2>
        <span>Latest release first</span>
    </div>

    <main class="grid">
        {cards_html}
    </main>

    <div class="footer">
        Generated automatically from GitHub Releases · {html.escape(OWNER)}
    </div>

</div>

<script>
function toggleHistory(id, button) {{
    const panel = document.getElementById(id);
    const isOpen = panel.classList.toggle("open");
    button.classList.toggle("open", isOpen);
}}
</script>

</body>
</html>
"""


if __name__ == "__main__":
    app_data = {app: get_releases(app) for app in APPS}
    html_output = build_html(app_data)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_output)

    print("Modern index.html generated")
