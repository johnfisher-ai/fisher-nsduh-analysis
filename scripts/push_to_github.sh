#!/usr/bin/env bash
# Commit and push this project. Run this yourself; Claude does not push.
#
#   bash scripts/push_to_github.sh                  # push existing commits
#   bash scripts/push_to_github.sh "commit message" # stage all, commit, then push
set -euo pipefail
cd "$(dirname "$0")/.."

REMOTE_URL="REPLACE_WITH_REPO_URL"

if [ "$REMOTE_URL" = "REPLACE_WITH_REPO_URL" ]; then
  if git remote get-url origin >/dev/null 2>&1; then
    REMOTE_URL="$(git remote get-url origin)"
  else
    echo "No remote set. Create the repo first:" >&2
    echo "  gh repo create johnfisher-ai/$(basename "$PWD") --public --source=. --remote=origin --push" >&2
    exit 1
  fi
fi

git rev-parse --verify main >/dev/null 2>&1 || git branch -M main
git checkout -q main 2>/dev/null || true

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

if [ "${1:-}" != "" ]; then
  git add -A
  if git diff --cached --quiet; then
    echo "No new changes to commit; pushing existing commits."
  else
    git -c user.name="John Fisher" -c user.email="johnrfisher@gmail.com" commit -m "$1"
  fi
fi

echo "Pushing to $REMOTE_URL (branch main) ..."
git push -u origin main
echo "Pushed. Pages build progress is on the repo's Actions tab."
