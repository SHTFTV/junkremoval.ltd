#!/usr/bin/env bash
set -euo pipefail
[[ "${GITHUB_ACTIONS:-}" == "true" && "${GITHUB_REPOSITORY:-}" == "SHTFTV/junkremoval.ltd" && -n "${GITHUB_SHA:-}" ]] || { echo 'NATIVE_REPOSITORY_CONTEXT_REQUIRED' >&2; exit 1; }
case "${1:-}" in
 worker-lease) role=worker; message='Acquire JunkRemoval source queue lease'; files=(operations/source-state.json) ;;
 worker) role=worker; message='Record JunkRemoval source queue and retained retries'; files=(operations/source-state.json operations/source-monitor-status.json) ;;
 visual) role=visual; message='Record actual JunkRemoval desktop and phone render observations'; files=(operations/visual-status.json operations/visual/) ;;
 supervisor) role=supervisor; message='Record JunkRemoval supervisor observations'; files=(operations/supervisor-status.json) ;;
 *) echo 'PERSIST_SCOPE_INVALID' >&2; exit 1 ;;
esac
python3 operations/check-inputs.py "$role"
git config user.name "junkremoval-${role}[bot]"
git config user.email "junkremoval-${role}@users.noreply.github.com"
git add -- "${files[@]}"
git diff --cached --quiet && exit 0
git commit -m "$message"
for attempt in 1 2 3; do
 git fetch origin main
 git rebase origin/main
 python3 operations/check-inputs.py "$role"
 if git push origin HEAD:main; then exit 0; fi
 if [[ "$attempt" != 3 ]]; then sleep "$((attempt * 2))"; fi
done
echo 'PERSIST_RETRY_LIMIT_REACHED; actual artifacts retained by workflow' >&2
exit 1
