#!/usr/bin/env bash
# SMP-1369: no internal reusable workflow is reachable from this public tap.
set -euo pipefail
: "${TITLE:?}" "${AUTHOR:?}"
if [[ "$AUTHOR" == 'dependabot[bot]' ]]; then
  echo 'Dependabot PR — title convention exempt.'
  exit 0
fi
pattern='^(feat|fix|docs|test|refactor|chore|perf|ci|build|revert)(\([a-zA-Z0-9 ._/-]+\))?!?: .+'
if printf '%s' "$TITLE" | grep -Eq "$pattern"; then
  printf 'Accepted PR title: %s\n' "$TITLE"
else
  echo '::error::PR title must use a supported conventional type and summary' >&2
  exit 1
fi
