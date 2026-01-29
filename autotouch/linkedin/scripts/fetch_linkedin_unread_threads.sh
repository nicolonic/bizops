#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  LI_AT="..." JSESSIONID="ajax:..." \
    ./linkedin/scripts/fetch_linkedin_unread_threads.sh "<messengerConversations URL>" [out_dir]
  ./linkedin/scripts/fetch_linkedin_unread_threads.sh --profile jane "<messengerConversations URL>" [out_dir]

Environment:
  LI_MESSAGE_QUERY_ID   Optional. Default: messengerMessages.5846eeb71c981f11e0134cb6626cc314
  MAX_THREADS           Optional. 0 = all (default)
  INBOX_URL             Optional. If set, you can omit the URL arg.

Notes:
- The conversations URL should already include read:false (Unread filter).
- Uses LinkedIn session cookies (li_at + JSESSIONID).
- Writes inbox list JSON + one JSON per thread to linkedin/data/raw/.
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

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
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
  INBOX_VAR="INBOX_URL_${UPPER_PROFILE}"
  if [[ -z "${LI_AT:-}" && -n "${!LI_VAR:-}" ]]; then
    LI_AT="${!LI_VAR}"
  fi
  if [[ -z "${JSESSIONID:-}" && -n "${!JS_VAR:-}" ]]; then
    JSESSIONID="${!JS_VAR}"
  fi
  if [[ -z "${INBOX_URL:-}" && -n "${!INBOX_VAR:-}" ]]; then
    INBOX_URL="${!INBOX_VAR}"
  fi
fi

if [[ -z "${LI_AT:-}" || -z "${JSESSIONID:-}" ]]; then
  echo "Missing LI_AT or JSESSIONID env vars." >&2
  usage
  exit 1
fi

INBOX_URL="${1:-${INBOX_URL:-}}"
if [[ -z "$INBOX_URL" ]]; then
  echo "Missing inbox URL. Pass it as an argument or set INBOX_URL." >&2
  usage
  exit 1
fi
OUT_DIR="${2:-linkedin/data/raw/threads}"
LI_MESSAGE_QUERY_ID="${LI_MESSAGE_QUERY_ID:-messengerMessages.5846eeb71c981f11e0134cb6626cc314}"
MAX_THREADS="${MAX_THREADS:-0}"

mkdir -p "$OUT_DIR"

# Build x-li-track header (matches browser metadata)
TZ_OFFSET="${TZ_OFFSET:--5}"
TZ_NAME="${TZ_NAME:-America/New_York}"
MP_VERSION="${MP_VERSION:-1.13.42044}"
LI_TRACK=$(cat <<EOF
{"clientVersion":"${MP_VERSION}","mpVersion":"${MP_VERSION}","osName":"web","timezoneOffset":${TZ_OFFSET},"timezone":"${TZ_NAME}","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":3600,"displayHeight":2338}
EOF
)

TS="$(date +%Y-%m-%d_%H%M%S)"
LIST_OUT="linkedin/data/raw/linkedin_unread_inbox_${TS}.json"

curl -s --compressed \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36" \
  -H "Accept: application/json" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -H "Referer: https://www.linkedin.com/" \
  -H "x-li-lang: en_US" \
  -H "x-li-track: $LI_TRACK" \
  -H "csrf-token: $JSESSIONID" \
  -H "x-restli-protocol-version: 2.0.0" \
  -H "cookie: li_at=$LI_AT; JSESSIONID=\"$JSESSIONID\"" \
  "$INBOX_URL" > "$LIST_OUT"

# Extract conversation URNs from the inbox list JSON.
URN_LIST=$(python3 - <<'PY' "$LIST_OUT"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text())
urns = set()

def walk(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            walk(v)
    elif isinstance(obj, list):
        for v in obj:
            walk(v)
    elif isinstance(obj, str) and obj.startswith("urn:li:msg_conversation:"):
        urns.add(obj)

walk(data)
for u in sorted(urns):
    print(u)
PY
)

if [[ -z "$URN_LIST" ]]; then
  echo "No conversation URNs found in $LIST_OUT"
  exit 0
fi

count=0
while IFS= read -r urn; do
  if [[ -z "$urn" ]]; then
    continue
  fi
  if [[ "$MAX_THREADS" != "0" && "$count" -ge "$MAX_THREADS" ]]; then
    break
  fi

  enc_urn=$(python3 - <<'PY' "$urn"
import sys, urllib.parse
print(urllib.parse.quote(sys.argv[1], safe=""))
PY
)

  msg_url="https://www.linkedin.com/voyager/api/voyagerMessagingGraphQL/graphql?queryId=${LI_MESSAGE_QUERY_ID}&variables=(conversationUrn:${enc_urn})"

  slug=$(echo "$urn" | tr -c 'A-Za-z0-9' '_')
  out_file="$OUT_DIR/thread_${slug}.json"

  curl -s --compressed \
    -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36" \
    -H "Accept: application/graphql" \
    -H "Accept-Language: en-US,en;q=0.9" \
    -H "Referer: https://www.linkedin.com/messaging/" \
    -H "x-li-lang: en_US" \
    -H "x-li-track: $LI_TRACK" \
    -H "csrf-token: $JSESSIONID" \
    -H "x-restli-protocol-version: 2.0.0" \
    -H "cookie: li_at=$LI_AT; JSESSIONID=\"$JSESSIONID\"" \
    "$msg_url" > "$out_file"

  count=$((count+1))
  echo "wrote $out_file"

done <<< "$URN_LIST"

echo "wrote $LIST_OUT"
