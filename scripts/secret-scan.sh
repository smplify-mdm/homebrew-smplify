#!/usr/bin/env bash
# SMP-2270: a failed scanner or unreadable report is never a clean scan.
set -euo pipefail
: "${RUNNER_TEMP:?}" "${GITHUB_OUTPUT:?}" "${MODE:?}"
report="$RUNNER_TEMP/gitleaks-report.json"
: > "$report" # A previous artifact must not turn a missing new report into a pass.
args=(detect --source . --config .gitleaks.toml --redact --exit-code 0
      --report-format json --report-path "$report")
case "$MODE" in
  diff) args+=(--log-opts "${LOG_OPTS:?missing PR scan range}") ;;
  full) ;;
  *) echo '::error::unknown secret scan scope' >&2; exit 1 ;;
esac
if ! "$RUNNER_TEMP/gitleaks" "${args[@]}"; then
  echo '::error::secret scanner failed; findings are unknown' >&2
  exit 1
fi
if [[ ! -s "$report" ]]; then
  echo '::error::secret scanner did not produce a report' >&2
  exit 1
fi
if ! count=$(jq -er 'if type == "array" then length else error("invalid report") end' "$report"); then
  echo '::error::secret scanner report is invalid; findings are unknown' >&2
  exit 1
fi
printf 'count=%s\n' "$count" >> "$GITHUB_OUTPUT"
