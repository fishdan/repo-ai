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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Validating GitHub App identity..."
JWT=$(python3 "$SCRIPT_DIR/github-app-generate-jwt.py")
APP_JSON=$(curl -sS -H "Authorization: Bearer $JWT" -H "Accept: application/vnd.github+json" https://api.github.com/app)
APP_SLUG=$(echo "$APP_JSON" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('slug',''))")
APP_ID=$(echo "$APP_JSON" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('id',''))")
if [ -z "$APP_SLUG" ] || [ -z "$APP_ID" ]; then
  echo "Failed to validate GitHub App identity from /app response."
  exit 1
fi

echo "Generating installation token for required repositories..."
TOKEN_DATA=$(python3 "$SCRIPT_DIR/github-app-get-installation-token.py")
INSTALL_TOKEN=$(echo "$TOKEN_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
EXPIRES_AT=$(echo "$TOKEN_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['expires_at'])")
REQUIRED_REPOS=$(echo "$TOKEN_DATA" | python3 -c "import sys, json; print(', '.join(json.load(sys.stdin).get('required_repositories', [])))")

# Configure git user identity
echo "Configuring git user identity..."
git config user.name "${APP_SLUG}[bot]"
git config user.email "${APP_ID}+${APP_SLUG}[bot]@users.noreply.github.com"

# Create GIT_ASKPASS script
echo "Creating GIT_ASKPASS script..."
cat > /tmp/git-askpass.sh <<EOF
#!/bin/bash
case "\$1" in
  *Username*) echo "x-access-token" ;;
  *) echo "$INSTALL_TOKEN" ;;
esac
EOF
chmod 755 /tmp/git-askpass.sh

echo ""
echo "✅ GitHub App authentication configured successfully"
echo "   Git user: $(git config user.name)"
echo "   Git email: $(git config user.email)"
echo "   Required repos validated: $REQUIRED_REPOS"
echo "   Token expires at: $EXPIRES_AT"
echo ""
echo "To push, use:"
echo "  GIT_ASKPASS=/tmp/git-askpass.sh GIT_TERMINAL_PROMPT=0 git push origin <branch>"
