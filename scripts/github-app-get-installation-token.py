#!/usr/bin/env python3
"""
Get a GitHub App installation access token.

This script generates a JWT, exchanges it for an installation access token,
and outputs the token and expiration time.

Usage:
    python3 scripts/github-app-get-installation-token.py

Output:
    Prints JSON with 'token' and 'expires_at' fields to stdout.
"""

import json
import jwt
import subprocess
import sys
import time
from pathlib import Path

# Get the project root directory (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
SECRETS_DIR = PROJECT_ROOT / "secrets"
CONFIG_FILE = SECRETS_DIR / "config.txt"
PRIVATE_KEY_FILE = SECRETS_DIR / "ai-codex-dan.2025-12-12.private-key.pem"


def read_config():
    """Read GitHub App ID and Installation ID from config.txt."""
    config = {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    except FileNotFoundError:
        print(f"Error: Config file not found: {CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)
    return config


def read_private_key():
    """Read the GitHub App private key."""
    try:
        with open(PRIVATE_KEY_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Private key file not found: {PRIVATE_KEY_FILE}", file=sys.stderr)
        sys.exit(1)


def run_command(args, cwd=None):
    """Run a command and return stdout, or empty string on failure."""
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def parse_github_full_name(remote_url):
    """Parse owner/repo from a GitHub remote URL."""
    if not remote_url:
        return ""

    normalized = remote_url.strip()
    if normalized.startswith("git@github.com:"):
        path = normalized.split("git@github.com:", 1)[1]
    elif normalized.startswith("https://github.com/"):
        path = normalized.split("https://github.com/", 1)[1]
    elif normalized.startswith("ssh://git@github.com/"):
        path = normalized.split("ssh://git@github.com/", 1)[1]
    else:
        return ""

    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")
    if len(parts) < 2:
        return ""
    return f"{parts[0]}/{parts[1]}"


def git_remote_full_name(repo_dir):
    """Return owner/repo for remote.origin.url in repo_dir."""
    remote_url = run_command(["git", "config", "--get", "remote.origin.url"], cwd=repo_dir)
    return parse_github_full_name(remote_url)


def derive_required_repositories():
    """
    Build required repositories list:
    1) .repo_ai repo
    2) fishdan-terraform (same owner as parent repo, fallback to .repo_ai owner)
    3) parent repo that vendors .repo_ai
    """
    repo_ai_full = git_remote_full_name(PROJECT_ROOT)
    parent_full = git_remote_full_name(PROJECT_ROOT.parent)

    owner = ""
    if parent_full and "/" in parent_full:
        owner = parent_full.split("/", 1)[0]
    elif repo_ai_full and "/" in repo_ai_full:
        owner = repo_ai_full.split("/", 1)[0]

    if not owner:
        print(
            "Error: Unable to derive GitHub owner from .repo_ai or parent repository remotes",
            file=sys.stderr,
        )
        sys.exit(1)

    terraform_full = f"{owner}/fishdan-terraform"
    required = [repo_ai_full, terraform_full, parent_full]

    deduped = []
    for repo in required:
        if repo and repo not in deduped:
            deduped.append(repo)
    return deduped


def generate_jwt():
    """Generate a JWT token for GitHub App authentication."""
    config = read_config()
    app_id = config.get('GITHUB_APP_ID')
    
    if not app_id:
        print("Error: GITHUB_APP_ID not found in config.txt", file=sys.stderr)
        sys.exit(1)
    
    private_key = read_private_key()
    
    # Generate JWT payload
    now = int(time.time())
    payload = {
        'iss': app_id,
        'iat': now - 60,  # Issued 60 seconds ago (clock skew tolerance)
        'exp': now + 600  # Expires in 10 minutes
    }
    
    # Sign and encode the JWT
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token


def get_installation_token(jwt_token, installation_id, repository_names):
    """Exchange JWT for installation access token."""
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

    payload = json.dumps({"repositories": repository_names})

    result = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            url,
            "-H",
            f"Authorization: Bearer {jwt_token}",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "Content-Type: application/json",
            "-d",
            payload,
        ],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"Error calling GitHub API: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    try:
        data = json.loads(result.stdout)
        if "token" not in data:
            print(f"Error: No token in API response: {result.stdout}", file=sys.stderr)
            sys.exit(1)
        return data
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}", file=sys.stderr)
        print(f"Response: {result.stdout}", file=sys.stderr)
        sys.exit(1)


def list_installation_repositories(installation_token):
    """List repositories visible to this installation token."""
    result = subprocess.run(
        [
            "curl",
            "-s",
            "https://api.github.com/installation/repositories",
            "-H",
            f"Authorization: token {installation_token}",
            "-H",
            "Accept: application/vnd.github+json",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error calling GitHub API: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}", file=sys.stderr)
        print(f"Response: {result.stdout}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    try:
        config = read_config()
        installation_id = config.get('GITHUB_INSTALLATION_ID')
        
        if not installation_id:
            print("Error: GITHUB_INSTALLATION_ID not found in config.txt", file=sys.stderr)
            sys.exit(1)
        
        required_repositories = derive_required_repositories()
        repository_names = [repo.split("/", 1)[1] for repo in required_repositories]

        jwt_token = generate_jwt()
        result = get_installation_token(jwt_token, installation_id, repository_names)

        visible = list_installation_repositories(result["token"])
        visible_full_names = {
            repo.get("full_name", "")
            for repo in visible.get("repositories", [])
        }
        missing = [repo for repo in required_repositories if repo not in visible_full_names]
        if missing:
            print(
                "Error: Installation token is missing required repositories: "
                + ", ".join(missing),
                file=sys.stderr,
            )
            sys.exit(1)

        # Output JSON with token and expiration
        output = {
            "token": result["token"],
            "expires_at": result.get("expires_at", ""),
            "required_repositories": required_repositories,
            "validated_repository_count": visible.get("total_count", 0),
        }
        print(json.dumps(output))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

