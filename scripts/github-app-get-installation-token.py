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

import jwt
import time
import sys
import json
import subprocess
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


def get_installation_token(jwt_token, installation_id):
    """Exchange JWT for installation access token."""
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    
    result = subprocess.run([
        'curl', '-s', '-X', 'POST', url,
        '-H', f'Authorization: Bearer {jwt_token}',
        '-H', 'Accept: application/vnd.github+json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error calling GitHub API: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    try:
        data = json.loads(result.stdout)
        if 'token' not in data:
            print(f"Error: No token in API response: {result.stdout}", file=sys.stderr)
            sys.exit(1)
        return data
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
        
        jwt_token = generate_jwt()
        result = get_installation_token(jwt_token, installation_id)
        
        # Output JSON with token and expiration
        output = {
            'token': result['token'],
            'expires_at': result.get('expires_at', '')
        }
        print(json.dumps(output))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


