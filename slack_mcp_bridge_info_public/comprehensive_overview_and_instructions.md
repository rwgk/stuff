# Comprehensive Overview and Instructions

This document explains:

- why `managed Slack MCP bridge` did not work for the target Slack searches,
- why `slack-mcp-bridge` is the best solution for full Slack access in
  Cursor on this workstation, and
- how to create the Slack app and obtain the correct Slack user token for the
  local bridge.

## Why `managed Slack MCP bridge` did not work for searching

At first, `managed Slack MCP bridge` looked healthy:

- the MCP server could be discovered,
- `slack_health_check()` succeeded,
- `slack_get_my_info()` succeeded,
- `slack_my_messages(query="to:me")` succeeded, and
- `slack_search_messages(query="from:me")` succeeded.

This showed that the general Cursor/MCP/OAuth wiring was working.

However, searching the target engineering channels failed. The key failure was
not a generic authentication outage, but an access-control restriction imposed
by the workspace's AI retrieval policy layer.

### The decisive evidence

The search attempts against `#example-engineering-channel` and related content led to an
error from the Slack MCP server indicating that the search was blocked by
enterprise compliance / exclusion policy.

The exclusion list on `the enterprise exclusion review page` then confirmed that both

- `#example-engineering-channel`
- `#example-engineering-channel-scrum`

were marked as active exclusions with this reason:

`Opt-in by a Channel Manager is required for AI Access enablement`

That explains the mismatch:

- native Slack web UI search works because it uses the user's own Slack access,
- `managed Slack MCP bridge` search does not work because it goes through the AI retrieval
  layer, and
- excluded channels are blocked from AI retrieval even when the user can
  normally see them in Slack.

### Practical conclusion

`managed Slack MCP bridge` was not broken. It was behaving as designed under the organization's AI access-control / exclusion rules.

For excluded channels, `managed Slack MCP bridge` cannot be expected to match normal Slack
web UI behavior unless those channels are opted in by a channel manager.

## Why `slack-mcp-bridge` is the best solution

The local bridge avoids the AI retrieval mediation layer completely.

Instead of going through `managed Slack MCP bridge`, it:

- runs locally as a stdio MCP server,
- is launched by Cursor from `~/.cursor/mcp.json`,
- talks directly to Slack Web API over HTTPS,
- uses the user's own Slack user token (`xoxp-...`), and
- therefore searches the same Slack corpus the user can access in native Slack.

### Why this is better than `managed Slack MCP bridge` for this use case

The goal here is not generic enterprise retrieval, but Slack parity:

- search the channels and threads the user already has access to,
- including channels blocked from AI retrieval,
- from a headless workstation where Cursor runs.

For that goal, the local bridge is better because it:

1. uses direct Slack account access instead of AI retrieval access,
2. avoids exclusion restrictions that apply to `managed Slack MCP bridge`,
3. stays local and read-only, which keeps the design simple,
4. does not require Socket Mode, bot events, or Slack posting permissions, and
5. matches Slack web UI behavior much more closely than `managed Slack MCP bridge` for search
   and history access.

### What was validated

The local bridge was tested directly on this workstation and succeeded for:

- health checks,
- account identity lookup,
- `from:me` searches,
- `in:example-engineering-channel Event` searches, and
- end-to-end use from a fresh Cursor agent session.

That last point is important: the bridge was not only tested at the raw Python
client layer, but also through Cursor as an MCP server.

### Why this design was chosen

Several implementation paths were considered. The chosen path was:

- minimal,
- read-only,
- fresh implementation,
- no reuse of Slack bot / Socket Mode machinery,
- no dependency on Claude-specific infrastructure, and
- no write/post/reply capabilities in v1.

This produced a small, auditable, personal tool rather than a more complex
multi-user Slack bot.

## Local bridge layout in this repo

The local bridge lives under `mcp/` in this repo:

- `mcp/slack_mcp_bridge_client.py`
- `mcp/slack_mcp_bridge_server.py`
- `mcp/run_slack_mcp_bridge.sh`
- `mcp/slack_mcp_bridge.env.example`
- `mcp/README_slack_mcp_bridge.md`
- `mcp/requirements_slack_mcp_bridge.txt`
- `mcp/test_slack_mcp_bridge_client.py`

The helper script for creating the dedicated venv is:

- `bin/create_slack_mcp_bridge_venv.sh`

## How to get the Slack token

The local bridge requires a Slack **User OAuth Token**, not a bot token and not
an app-level token.

The correct token starts with:

- `xoxp-...`

The wrong tokens for this bridge are:

- `xoxb-...` (bot token)
- `xapp-...` (app-level token)

### High-level flow

1. Create a Slack app.
2. Add the required **User Token Scopes**.
3. Request / complete workspace installation.
4. Copy the **User OAuth Token** (`xoxp-...`).
5. Store it in `~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env`.

### Detailed steps

#### 1. Create the app

Go to:

- <https://api.slack.com/apps>

Then:

1. Click `Create an App`
2. Choose `From scratch`
3. Use a private app name such as:
   - `slack-mcp-bridge`
4. Select the target Slack workspace

The app can stay very minimal. It does not need public distribution, event
subscriptions, Socket Mode, PKCE, or token rotation for this use case.

#### 2. Add User Token Scopes

Go to:

- `OAuth & Permissions`

Under **User Token Scopes**, add at least:

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

These scopes are sufficient for the current read-only bridge features:

- search messages,
- read channel history,
- read thread replies,
- list channels,
- inspect the authenticated user,
- and look up users by email.

#### 3. Install to workspace

Still under `OAuth & Permissions`, click:

- `Request to Workspace Install`

If approval is required, the first click may only submit the request.

After approval is granted, return to the same page and click:

- `Install to the workspace`

This second step is the one that completes installation and generates the OAuth
tokens for the app.

#### 4. Copy the correct token

After installation completes, stay on `OAuth & Permissions` and find:

- `OAuth Tokens for Your Workspace`

Copy the **User OAuth Token**:

- `xoxp-...`

That value becomes:

- `SLACK_USER_TOKEN`

#### 5. Store the token securely

Copy the example env file:

```bash
mkdir -p ~/.slack_mcp_bridge_secrets
cp /path/to/slack_mcp_bridge_repo/mcp/slack_mcp_bridge.env.example ~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env
```

Lock down permissions:

```bash
chmod 600 ~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env
```

Then edit:

```bash
SLACK_USER_TOKEN=xoxp-...
PYTHON=/wrk/slack-mcp-bridge-venv/bin/python
```

### Important notes about token handling

- Do not put the token into `~/.cursor/mcp.json`
- Do not use a bot token instead of a user token
- Do not use an app-level token
- Keep `~/.slack_mcp_bridge_secrets/slack_mcp_bridge.env` private
- The launcher enforces that the env file must be owner-only (`600` or `400`)

## Venv setup

Create the dedicated virtual environment with:

```bash
/path/to/slack_mcp_bridge_repo/bin/create_slack_mcp_bridge_venv.sh /wrk
```

This creates:

```text
/wrk/slack-mcp-bridge-venv
```

and installs the Python dependencies from:

- `mcp/requirements_slack_mcp_bridge.txt`

## Cursor configuration

Add the local bridge to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "slack-mcp-bridge": {
      "command": "/path/to/slack_mcp_bridge_repo/mcp/run_slack_mcp_bridge.sh"
    }
  }
}
```

The token stays in the env file. Cursor should only launch the local bridge.

## Where it appears in Slack

The local bridge itself does not appear as a visible feature in the normal
Slack web UI.

This is expected because the bridge is:

- a local MCP server running on the workstation,
- launched by Cursor,
- using Slack Web API directly, and
- not configured as a Slack bot with App Home, message posting, slash commands,
  Socket Mode, or event subscriptions.

Because of that, there is usually nothing to see in the regular Slack client
such as:

- a bot DM,
- an App Home view,
- slash commands,
- or app messages in channels.

What does exist is the Slack app configuration that was created in order to
obtain the `xoxp-...` user token.

That app can be inspected here:

- <https://api.slack.com/apps>

Useful sections there include:

- `Basic Information`
- `OAuth & Permissions`
- the installed user token and scopes

In short:

- the Slack app exists in Slack developer/app management,
- the local bridge consumes that token outside Slack,
- and the bridge itself is not meant to be a user-facing Slack app experience.

## Validation steps

Recommended validation order:

1. `slack_health_check()`
2. `slack_get_my_info()`
3. `slack_search_messages(query="from:me", count=3, page=1)`
4. `slack_search_messages(query="in:example-engineering-channel Event", count=5, page=1)`

These checks were already demonstrated to work successfully with the local
bridge on this machine.

## Final recommendation

For excluded engineering channels such as `#example-engineering-channel`, the local bridge
is the right solution when the goal is to make Cursor behave more like native
Slack search.

`managed Slack MCP bridge` remains useful in general, but it cannot override AI access-control exclusions. The local user-token bridge is therefore the practical path
to full search access for personal engineering workflows on this workstation.
