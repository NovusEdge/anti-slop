#!/bin/sh
# Remove Claude and Anthropic Co-Authored-By trailers from a commit message.
# pre-commit passes the message file as the first argument.
tmp=$(mktemp)
grep -vE '^Co-Authored-By:.*([Cc]laude|[Aa]nthropic|noreply@anthropic)' "$1" > "$tmp" || true
mv "$tmp" "$1"
