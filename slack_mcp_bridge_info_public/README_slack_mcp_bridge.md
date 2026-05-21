# Slack MCP Bridge

This is a small read-only MCP server for Cursor that talks directly to the
Slack Web API with your own Slack user token.

It exists to provide better parity with native Slack search/history than
`managed Slack MCP bridge` in cases where managed bridge is blocked by AI Access Control.

## Tool surface

The bridge exposes these tools:

- `slack_health_check`
- `slack_get_my_info`
- `slack_lookup_user_by_email`
- `slack_list_user_channels`
- `slack_search_messages`
- `slack_get_conversation_history`
- `slack_get_thread_replies`

The return shape is intentionally similar to `managed Slack MCP bridge`: every tool returns
an object with `success`, `data`, and `error`.

## Slack token and scopes

Use a Slack **user token** (`xoxp-...`), not a bot token.

For the current tool set, the token should have at least:

- `search:read`
- `channels:history`
- `groups:history`
- `im:history`
- `mpim:history`
- `channels:read`
- `groups:read`
- `im:read`
- `mpim:read`
- `users:read`
- `users:read.email`

## Setup

1. Create a Python environment with the required packages:

```bash
/path/to/slack_mcp_bridge_repo/bin/create_slack_mcp_bridge_venv.sh /wrk
```

This creates:

```text
/wrk/slack-mcp-bridge-venv
```

Then set this in `~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env`:

```bash
PYTHON=/wrk/slack-mcp-bridge-venv/bin/python
```

2. Create the runtime env file under `~/.slack_mcp_bridge_secrets/` and make it user-readable only:

```bash
mkdir -p ~/.slack_mcp_bridge_secrets
cp mcp/slack_mcp_bridge.env.example ~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env
chmod 600 ~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env
```

3. Edit `~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env` and fill in `SLACK_USER_TOKEN`.

4. Make the launcher executable:

```bash
chmod +x mcp/run_slack_mcp_bridge.sh
```

## Cursor configuration

Add a local MCP entry to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "slack-mcp-bridge": {
      "command": "/path/to/slack_mcp_bridge_repo/mcp/run_slack_mcp_bridge.sh"
    }
  }
}
```

By default, the launcher reads:

```text
~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env
```

If you want to keep the env file somewhere else, pass it as the first argument:

```json
{
  "mcpServers": {
    "slack-mcp-bridge": {
      "command": "/path/to/slack_mcp_bridge_repo/mcp/run_slack_mcp_bridge.sh",
      "args": ["/path/to/private/slack_mcp_bridge.env"]
    }
  }
}
```

## Validation

Start with:

- `slack_health_check()`
- `slack_get_my_info()`
- `slack_search_messages(query="from:me", count=5, page=1)`

Then compare one or two queries against Slack web UI, e.g.:

- `slack_search_messages(query="in:example-engineering-channel Event", count=5, page=1)`

## Security notes

- Keep `~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env` private (`chmod 600` or `chmod 400`).
- The launcher refuses to start if the env file has any group/world permissions.
- Do not put the Slack token inline in `~/.cursor/mcp.json`.
- This bridge is intentionally read-only in v1.
