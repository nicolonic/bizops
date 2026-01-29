#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  LI_AT="..." JSESSIONID="ajax:..." ./linkedin/scripts/fetch_linkedin_thread.sh "<voyager URL>" [output_path]
  ./linkedin/scripts/fetch_linkedin_thread.sh --profile jane "<voyager URL>" [output_path]

Notes:
- Uses LinkedIn session cookies (li_at + JSESSIONID) from environment variables.
- Writes the raw JSON response to linkedin/data/raw/ by default.
- Do not commit cookies or paste them in docs/chats.
USAGE
}

PROFILE=""
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done
if ((${#ARGS[@]})); then
  set -- "${ARGS[@]}"
else
  set --
fi

if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${#@} -lt 1 ]]; then
  usage
  exit 0
fi

ENV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ENV_DIR/.env"
if [[ -n "$PROFILE" ]]; then
  ENV_FILE="$ENV_DIR/.env.$PROFILE"
fi
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

if [[ -n "$PROFILE" ]]; then
  UPPER_PROFILE="$(printf '%s' "$PROFILE" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9_' '_')"
  LI_VAR="LI_AT_${UPPER_PROFILE}"
  JS_VAR="JSESSIONID_${UPPER_PROFILE}"
  if [[ -z "${LI_AT:-}" && -n "${!LI_VAR:-}" ]]; then
    LI_AT="${!LI_VAR}"
  fi
  if [[ -z "${JSESSIONID:-}" && -n "${!JS_VAR:-}" ]]; then
    JSESSIONID="${!JS_VAR}"
  fi
fi

if [[ -z "${LI_AT:-}" || -z "${JSESSIONID:-}" ]]; then
  echo "Missing LI_AT or JSESSIONID env vars." >&2
  usage
  exit 1
fi

URL="$1"
OUT_PATH="${2:-}"

if [[ -z "$OUT_PATH" ]]; then
  ts="$(date +%Y-%m-%d_%H%M%S)"
  OUT_PATH="linkedin/data/raw/linkedin_thread_${ts}.json"
fi

mkdir -p "$(dirname "$OUT_PATH")"

# Build x-li-track header (matches browser metadata)
# Extract timezone offset (defaults to -5 for EST)
TZ_OFFSET="${TZ_OFFSET:--5}"
TZ_NAME="${TZ_NAME:-America/New_York}"
MP_VERSION="${MP_VERSION:-1.13.42044}"
LI_TRACK=$(cat <<EOF
{"clientVersion":"${MP_VERSION}","mpVersion":"${MP_VERSION}","osName":"web","timezoneOffset":${TZ_OFFSET},"timezone":"${TZ_NAME}","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":3600,"displayHeight":2338}
EOF
)

curl -s --compressed \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36" \
  -H "Accept: application/graphql" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -H "Referer: https://www.linkedin.com/" \
  -H "x-li-lang: en_US" \
  -H "x-li-track: $LI_TRACK" \
  -H "csrf-token: $JSESSIONID" \
  -H "x-restli-protocol-version: 2.0.0" \
  -H "cookie: li_at=$LI_AT; JSESSIONID=\"$JSESSIONID\"" \
  "$URL" > "$OUT_PATH"

echo "wrote $OUT_PATH"
