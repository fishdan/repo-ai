#!/bin/bash
# Setup GitHub App authentication for git operations.
#
# This script:
# 1. Generates a JWT and exchanges it for an installation token
# 2. Configures git to commit as the GitHub App bot
# 3. Creates a GIT_ASKPASS script for push operations
#
# Usage:
#     ./scripts/github-app-setup-git-auth.sh
#
# After running this, git push operations should use:
#     GIT_ASKPASS=/tmp/git-askpass.sh GIT_TERMINAL_PROMPT=0 git push origin <branch>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Get installation token
echo "Generating installation token..."
TOKEN_DATA=$(python3 "$SCRIPT_DIR/github-app-get-installation-token.py")
INSTALL_TOKEN=$(echo "$TOKEN_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
EXPIRES_AT=$(echo "$TOKEN_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['expires_at'])")

# Read config for app details
APP_ID=$(grep GITHUB_APP_ID "$PROJECT_ROOT/secrets/config.txt" | cut -d'=' -f2)
APP_SLUG="ai-codex-dan"  # From validation, could be read from API if needed

# Configure git user identity
echo "Configuring git user identity..."
git config user.name "${APP_SLUG}[bot]"
git config user.email "${APP_ID}+${APP_SLUG}[bot]@users.noreply.github.com"

# Create GIT_ASKPASS script
echo "Creating GIT_ASKPASS script..."
cat > /tmp/git-askpass.sh <<EOF
#!/bin/bash
echo "$INSTALL_TOKEN"
EOF
chmod 755 /tmp/git-askpass.sh

echo ""
echo "✅ GitHub App authentication configured successfully"
echo "   Git user: $(git config user.name)"
echo "   Git email: $(git config user.email)"
echo "   Token expires at: $EXPIRES_AT"
echo ""
echo "To push, use:"
echo "  GIT_ASKPASS=/tmp/git-askpass.sh GIT_TERMINAL_PROMPT=0 git push origin <branch>"


