#!/usr/bin/env bash
# Apply branch protection to main. Run ONCE by a repo ADMIN.
set -uo pipefail
REPO="${1:-OrmuzdAhriman/Marli-AI-Assistant}"
command -v gh >/dev/null 2>&1 || { echo "Need gh. Run: marli doctor"; exit 1; }
echo "Applying protection to 'main' on $REPO (requires admin rights)…"
gh api -X PUT "repos/$REPO/branches/main/protection" \
  -H "Accept: application/vnd.github+json" --input - <<'JSON'
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": { "required_approving_review_count": 1 },
  "restrictions": null
}
JSON
rc=$?
if [ $rc -eq 0 ]; then
  echo "✓ main now requires a pull request with 1 approving review."
else
  echo "✗ Failed (rc=$rc). Likely you're not an admin on $REPO, or token lacks 'repo' scope."
fi
