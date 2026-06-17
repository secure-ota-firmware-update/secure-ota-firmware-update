import argparse
import json
import sys

import requests


GITHUB_API_BASE = "https://api.github.com"
DEFAULT_REPO = "secure-ota-firmware-update/secure-ota-firmware-update"


def get_latest_release(repo: str) -> dict:
    """
    Fetch the latest release from GitHub's public API.

    Args:
        repo: GitHub repository in owner/repo format

    Returns:
        dict: full release object from GitHub API

    Raises:
        requests.RequestException: if API request fails
        SystemExit: if no releases found
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/releases/latest"

    response = requests.get(
        url,
        headers={"Accept": "application/vnd.github+json"},
        timeout=10
    )

    if response.status_code == 404:
        print(f"[ERROR] No releases found for repo: {repo}")
        print("[ERROR] Push a release tag first (e.g. git tag v1.0.0 && git push origin v1.0.0)")
        sys.exit(1)

    response.raise_for_status()
    return response.json()


def extract_asset_urls(release: dict) -> dict:
    """
    Extract download URLs for firmware assets from a release object.

    Args:
        release: GitHub release API response dict

    Returns:
        dict: mapping of filename to download URL
    """
    assets = {}
    for asset in release.get("assets", []):
        assets[asset["name"]] = asset["browser_download_url"]
    return assets


def main():
    parser = argparse.ArgumentParser(
        description="Fetch latest GitHub Release firmware asset URLs"
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=DEFAULT_REPO,
        help=f"GitHub repo in owner/repo format (default: {DEFAULT_REPO})"
    )

    args = parser.parse_args()

    print(f"[*] Fetching latest release from: {args.repo}")

    release = get_latest_release(args.repo)
    assets = extract_asset_urls(release)

    print(f"[+] Latest release: {release['tag_name']}")
    print(f"[+] Published: {release['published_at']}")
    print(f"[+] Assets ({len(assets)} files):")

    for name, url in assets.items():
        print(f"    {name}: {url}")

    print()
    print("[*] Set this as GITHUB_RELEASE_BASE_URL for the edge agent:")
    repo_url = f"https://github.com/{args.repo}"
    print(f"    export GITHUB_RELEASE_BASE_URL={repo_url}")


if __name__ == "__main__":
    main()
