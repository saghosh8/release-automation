import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Release Automation Dashboard", layout="wide")

OWNER = "saghosh8"
REPO = "release-automation"

# Maps each pipeline stage to its actual workflow file in the repo
WORKFLOWS = {
    "Onboarding": "create-app-repos.yml",
    "Release Branch": "create-release-branch.yml",
    "CI & Tagging": "prod_ci.yml",
    "Release Notes": "publish-release-notes.yml",
    "Prod Deployment": "prod_cd.yml",
}

STATUS_ICON = {
    "success": "🟢",
    "failure": "🔴",
    "in_progress": "🟡",
    "queued": "🟡",
    "cancelled": "⚪",
    "unknown": "⚪",
}


@st.cache_data(ttl=60)
def get_latest_run(workflow_file):
    """Fetch the most recent run for a workflow file from the GitHub API."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{workflow_file}/runs"
    try:
        resp = requests.get(url, params={"per_page": 1}, timeout=10)
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        if not runs:
            return {"status": "unknown", "updated_at": None, "html_url": None, "branch": None}
        run = runs[0]
        status = run["conclusion"] or run["status"]  # e.g. "success" / "in_progress"
        return {
            "status": status,
            "updated_at": run["updated_at"],
            "html_url": run["html_url"],
            "branch": run["head_branch"],
        }
    except Exception:
        return {"status": "unknown", "updated_at": None, "html_url": None, "branch": None}


# ---- Header ----
st.title("Release Automation Dashboard")
st.caption(f"Repo: {OWNER}/{REPO} - Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ---- Status table ----
st.subheader("Pipeline Stage Status")

results = {stage: get_latest_run(wf) for stage, wf in WORKFLOWS.items()}

cols = st.columns(len(WORKFLOWS))
for col, (stage, data) in zip(cols, results.items()):
    icon = STATUS_ICON.get(data["status"], "⚪")
    with col:
        st.markdown(f"**{stage}**")
        st.markdown(f"### {icon} {data['status']}")
        if data["branch"]:
            st.caption(f"Branch: `{data['branch']}`")
        if data["html_url"]:
            st.markdown(f"[View run]({data['html_url']})")

# ---- Summary metrics ----
st.divider()
st.subheader("Summary")

statuses = [r["status"] for r in results.values()]
success_count = statuses.count("success")
failure_count = statuses.count("failure")
other_count = len(statuses) - success_count - failure_count

c1, c2, c3 = st.columns(3)
c1.metric("Stages passing", success_count)
c2.metric("Stages failing", failure_count)
c3.metric("In progress / unknown", other_count)

st.info(
    "Pulls the latest run per workflow from the GitHub Actions API "
    f"for {OWNER}/{REPO}. Public repo, no token needed, but GitHub "
    "rate-limits unauthenticated requests to 60/hour. Set a "
    "GITHUB_TOKEN env var and pass it as a header if you hit that limit."
)
