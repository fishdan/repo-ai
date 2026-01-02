#!/usr/bin/env python3
"""
Generate a JWT token for GitHub App authentication.

This script reads the GitHub App ID and private key from the secrets folder
and generates a JWT token signed with RS256 that can be used to authenticate
as the GitHub App.

Usage:
    python3 scripts/github-app-generate-jwt.py

Output:
    Prints the JWT token to stdout (suitable for use in shell scripts).
"""

import jwt
import time
import sys
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


if __name__ == '__main__':
    try:
        jwt_token = generate_jwt()
        print(jwt_token)
    except Exception as e:
        print(f"Error generating JWT: {e}", file=sys.stderr)
        sys.exit(1)


