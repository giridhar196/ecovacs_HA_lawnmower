#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   export GH_TOKEN=ghp_...
#   ./scripts/create_github_repo.sh [owner_optional]
#
# Creates public repo ha-ecovacs-open and pushes this branch.

REPO_NAME="ha-ecovacs-open"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "Set GH_TOKEN to a GitHub PAT with 'repo' scope first."
  exit 1
fi

export GH_TOKEN
gh auth status

OWNER="${1:-$(gh api user --jq .login)}"
FULL="${OWNER}/${REPO_NAME}"

# Update README badges with real owner
sed -i "s/REPO_OWNER/${OWNER}/g" README.md

if gh repo view "$FULL" >/dev/null 2>&1; then
  echo "Repo $FULL already exists"
  if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "https://github.com/${FULL}.git"
  fi
else
  gh repo create "$FULL" --public --source=. --remote=origin --description "Home Assistant integration for Ecovacs lawn mowers via open.ecovacs.com"
fi

git checkout -B main
git add README.md hacs.json scripts/create_github_repo.sh
git -c user.email="${GIT_AUTHOR_EMAIL:-giridhar196@gmail.com}" \
    -c user.name="${GIT_AUTHOR_NAME:-Giridhar Addagalla}" \
    commit -m "Add HACS Add-to-HA badges and publish script" || true

git push -u origin main

echo ""
echo "Public repo: https://github.com/${FULL}"
echo "Add to HACS: https://my.home-assistant.io/redirect/hacs_repository/?owner=${OWNER}&repository=${REPO_NAME}&category=integration"
echo "Add integration: https://my.home-assistant.io/redirect/config_flow_start/?domain=ecovacs_open"
