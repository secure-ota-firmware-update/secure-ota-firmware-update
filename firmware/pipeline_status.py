import argparse
import sys
import requests


GITHUB_API_BASE = "https://api.github.com"
DEFAULT_REPO = "secure-ota-firmware-update/secure-ota-firmware-update"
DEFAULT_WORKFLOW = "sign-and-release.yml"


def get_workflow_runs(repo: str, workflow: str) -> list:
    """
    Fetch recent workflow runs from GitHub API.

    Args:
        repo: GitHub repo in owner/repo format
        workflow: workflow filename e.g. sign-and-release.yml

    Returns:
        list: workflow run objects sorted by newest first
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/actions/workflows/{workflow}/runs"

    response = requests.get(
        url,
        headers={"Accept": "application/vnd.github+json"},
        timeout=10,
        params={"per_page": 5}
    )

    if response.status_code == 404:
        print(f"[ERROR] Workflow not found: {workflow}")
        print("[ERROR] Make sure sign-and-release.yml exists in .github/workflows/")
        sys.exit(1)

    response.raise_for_status()
    return response.json().get("workflow_runs", [])


def format_status(run: dict) -> str:
    """
    Format a workflow run status with emoji indicator.

    Args:
        run: workflow run object from GitHub API

    Returns:
        str: formatted status string
    """
    conclusion = run.get("conclusion")
    status = run.get("status")

    if status == "in_progress":
        indicator = "🔄 RUNNING"
    elif conclusion == "success":
        indicator = "✅ PASSED"
    elif conclusion == "failure":
        indicator = "❌ FAILED"
    elif conclusion == "cancelled":
        indicator = "⚪ CANCELLED"
    else:
        indicator = f"❓ {status}/{conclusion}"

    return indicator


def main():
    parser = argparse.ArgumentParser(
        description="Check GitHub Actions pipeline status"
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=DEFAULT_REPO,
        help=f"GitHub repo (default: {DEFAULT_REPO})"
    )
    parser.add_argument(
        "--workflow",
        type=str,
        default=DEFAULT_WORKFLOW,
        help=f"Workflow filename (default: {DEFAULT_WORKFLOW})"
    )

    args = parser.parse_args()

    print(f"[*] Checking pipeline status for: {args.repo}")
    print(f"[*] Workflow: {args.workflow}")
    print()

    runs = get_workflow_runs(args.repo, args.workflow)

    if not runs:
        print("[INFO] No workflow runs found yet")
        print("[INFO] Push a tag (e.g. git tag v1.0.0 && git push origin v1.0.0) to trigger the pipeline")
        return

    print(f"{'Run':<6} {'Tag/Branch':<20} {'Status':<20} {'Started':<25}")
    print("-" * 75)

    for i, run in enumerate(runs, 1):
        tag = run.get("head_branch") or run.get("display_title", "unknown")[:20]
        status = format_status(run)
        started = run.get("created_at", "unknown")[:19].replace("T", " ")
        print(f"{i:<6} {tag:<20} {status:<20} {started:<25}")

    print()
    latest = runs[0]
    conclusion = latest.get("conclusion")

    if conclusion == "success":
        print("[+] Latest pipeline run PASSED")
        print(f"[+] View run: {latest['html_url']}")
    elif latest.get("status") == "in_progress":
        print("[*] Pipeline is currently running...")
        print(f"[*] Watch: {latest['html_url']}")
    else:
        print(f"[!] Latest pipeline run status: {conclusion}")
        print(f"[!] Check logs: {latest['html_url']}")


if __name__ == "__main__":
    main()