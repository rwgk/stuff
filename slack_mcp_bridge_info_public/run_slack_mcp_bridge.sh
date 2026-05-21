#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
default_env_file="$HOME/.slack_mcp_bridge_secrets/slack_mcp_bridge.env"
env_file="${1:-$default_env_file}"

if [[ ! -f "$env_file" ]]; then
    echo "Missing env file: $env_file" >&2
    echo "Create the parent directory if needed, then copy:" >&2
    echo "  mkdir -p \"$(dirname "$env_file")\"" >&2
    echo "  cp \"$script_dir/slack_mcp_bridge.env.example\" \"$env_file\"" >&2
    echo "  chmod 600 \"$env_file\"" >&2
    echo "Then fill in SLACK_USER_TOKEN." >&2
    exit 1
fi

mode="$(stat -c '%a' "$env_file")"
perm_bits=$((8#$mode))
owner_bits=$(((perm_bits >> 6) & 7))
group_world_bits=$((perm_bits & 8#077))

if [[ "$group_world_bits" -ne 0 || ("$owner_bits" -ne 4 && "$owner_bits" -ne 6) ]]; then
    echo "Unsafe env file permissions for $env_file: mode $mode" >&2
    echo "Expected owner-only read/write (600) or owner-only read (400)." >&2
    exit 1
fi

set -a
source "$env_file"
set +a

python_bin="${PYTHON:-python3}"

exec "$python_bin" "$script_dir/slack_mcp_bridge_server.py"
