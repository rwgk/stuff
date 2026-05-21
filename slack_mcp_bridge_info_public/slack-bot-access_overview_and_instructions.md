# slack-bot-access: Slack Posting Reference

This document is a self-contained reference for the `slack-bot-access` Slack app.
It is intentionally independent from any Slack read/search bridge setup.

## Purpose

`slack-bot-access` is a small personal Slack app for posting curated messages from
local scripts or an agent session into Slack with Slack `mrkdwn` rendered
correctly.

The motivating use case is posting messages with labeled links such as:

```text
<https://github.com/example-org/example-repo/pull/1234|PR #1234>
```

Pasting this syntax into Slack's web composer may escape the `|` as `%7C`, even
with "Format messages with markup" enabled. Posting through Slack's Web API with
`mrkdwn: true` renders it correctly.

## Slack App

App name:

```text
slack-bot-access
```

Recommended short description:

```text
Personal bot for posting the user's local automation output to Slack.
```

Create or manage the app at:

```text
https://api.slack.com/apps
```

## Scopes

### Bot Token Scopes

Use these under **OAuth & Permissions** -> **Bot Token Scopes**:

```text
chat:write
chat:write.public
```

`chat:write` allows the bot to post messages.

`chat:write.public` allows the bot to post to public channels without first
being invited to the channel. Without this scope, posting to a public channel
where the bot is not a member fails with:

```text
not_in_channel
```

### User Token Scopes

Use this under **OAuth & Permissions** -> **User Token Scopes**:

```text
chat:write
```

This creates a user token that can post as the installing user. This is useful
when the message should be owned by the user rather than by the bot.

Notes:

- The bot token posts as `slack-bot-access`.
- The user token posts as the authenticated Slack user.
- Slack generally requires the same authenticated actor to edit or delete a
  message through the API.
- After changing scopes, click **Reinstall to Workspace**. A green reinstall
  button or banner means the currently installed app authorization may not yet
  include the new scope.

## Token Storage

Tokens are stored locally in:

```text
$HOME/.slack_mcp_bridge_secrets/slack_bot_access.env
```

Expected contents:

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_USER_WRITE_TOKEN=xoxp-...
```

Recommended permissions:

```text
$HOME/.slack_mcp_bridge_secrets       mode 700
$HOME/.slack_mcp_bridge_secrets/*.env mode 600
```

Do not paste tokens into chat, logs, GitHub, Slack, or other shared text.

## Channel IDs And Thread Timestamps

Example channel:

```text
example-engineering-channel-scrum -> C0123456789
```

Slack permalinks contain the channel ID and message timestamp. For example:

```text
https://example.slack.com/archives/C0123456789/p1779317505990209
```

This maps to:

```text
channel   = C0123456789
thread_ts = 1779317505.990209
```

Conversion rule for the `p...` suffix:

1. Remove the leading `p`.
2. Split the remaining digits into seconds plus six microsecond digits.
3. Insert a dot before the final six digits.

Example:

```text
p1779317505990209 -> 1779317505.990209
```

When posting a reply to a thread, pass the root message timestamp as
`thread_ts`.

## Post A Small Test Message

Post as the bot:

```bash
set -a
. $HOME/.slack_mcp_bridge_secrets/slack_bot_access.env
set +a

curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data "$(jq -n \
    --arg channel 'C0123456789' \
    --arg thread_ts '1779317505.990209' \
    --arg text 'Test threaded mrkdwn link: <https://github.com/example-org/example-repo/pull/1234|PR #1234>' \
    '{channel:$channel,thread_ts:$thread_ts,text:$text,mrkdwn:true,unfurl_links:false,unfurl_media:false}')" \
  | jq '{ok, channel, ts, error}'
```

Post as the user:

```bash
set -a
. $HOME/.slack_mcp_bridge_secrets/slack_bot_access.env
set +a

curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_USER_WRITE_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data "$(jq -n \
    --arg channel 'C0123456789' \
    --arg thread_ts '1779317505.990209' \
    --arg text 'Test threaded mrkdwn link: <https://github.com/example-org/example-repo/pull/1234|PR #1234>' \
    '{channel:$channel,thread_ts:$thread_ts,text:$text,mrkdwn:true,unfurl_links:false,unfurl_media:false}')" \
  | jq '{ok, channel, ts, error}'
```

Expected success response:

```json
{
  "ok": true,
  "channel": "C0123456789",
  "ts": "...",
  "error": null
}
```

## Post A Message From A File

Slack-ready file contents may use Slack `mrkdwn`, including labeled links:

```text
<https://github.com/example-org/example-repo/pull/1234|PR #1234>
```

Post a file as the user:

```bash
set -a
. $HOME/.slack_mcp_bridge_secrets/slack_bot_access.env
set +a

MSG_FILE=/path/to/message.txt

curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_USER_WRITE_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data "$(jq -n \
    --arg channel 'C0123456789' \
    --arg thread_ts '1779317505.990209' \
    --rawfile text "$MSG_FILE" \
    '{channel:$channel,thread_ts:$thread_ts,text:$text,mrkdwn:true,unfurl_links:false,unfurl_media:false}')" \
  | jq '{ok, channel, ts, error}'
```

Post a file as the bot by changing the authorization header to:

```text
Authorization: Bearer $SLACK_BOT_TOKEN
```

## Edit A Message

Use `chat.update`.

Important: use the same token identity that created the message. Bot-authored
messages should be updated with `SLACK_BOT_TOKEN`; user-authored messages should
be updated with `SLACK_USER_WRITE_TOKEN`.

```bash
set -a
. $HOME/.slack_mcp_bridge_secrets/slack_bot_access.env
set +a

MSG_FILE=/path/to/replacement_message.txt

curl -sS -X POST https://slack.com/api/chat.update \
  -H "Authorization: Bearer $SLACK_USER_WRITE_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data "$(jq -n \
    --arg channel 'C0123456789' \
    --arg ts '1779317505.990209' \
    --rawfile text "$MSG_FILE" \
    '{channel:$channel,ts:$ts,text:$text,mrkdwn:true,unfurl_links:false,unfurl_media:false}')" \
  | jq '{ok, channel, ts, error}'
```

If this fails for a manually authored web-UI message, Slack may be enforcing a
client/app ownership rule. In that case, either edit manually in the UI or post
the message through the API initially so the same token can update it later.

## Delete A Message

Use `chat.delete`.

Important: use the same token identity that created the message.

```bash
set -a
. $HOME/.slack_mcp_bridge_secrets/slack_bot_access.env
set +a

curl -sS -X POST https://slack.com/api/chat.delete \
  -H "Authorization: Bearer $SLACK_USER_WRITE_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data "$(jq -n \
    --arg channel 'C0123456789' \
    --arg ts '1779321629.194189' \
    '{channel:$channel,ts:$ts}')" \
  | jq '{ok, channel, ts, error}'
```

For bot-authored messages, use:

```text
Authorization: Bearer $SLACK_BOT_TOKEN
```

## Formatting Notes

Slack Web API messages use Slack `mrkdwn`, not GitHub Markdown.

Useful forms:

```text
<https://example.com|link label>
*bold*
`code`
- bullet
```

Avoid relying on these through the web composer if labeled links matter:

```text
<https://example.com|label>
```

The web composer may escape the pipe character and produce:

```text
https://example.com%7Clabel
```

The Web API path avoids that problem.

## Troubleshooting

`not_in_channel`

- The bot is not a member of the channel and does not have active
  `chat:write.public`, or Slack still requires membership for the attempted
  action.
- Reinstall the app after adding scopes.
- For private channels, invite the bot or use a user token for a user who is in
  the channel.

`missing_scope`

- Add the missing scope under **OAuth & Permissions**.
- Reinstall the app after changing scopes.
- Retry with the current token from the app page.

`invalid_auth`

- Token is missing, malformed, revoked, or copied incorrectly.
- Confirm the env file is sourced and the token starts with the expected prefix:
  `xoxb-` for bot token, `xoxp-` for user token.

`channel_not_found`

- Channel ID is wrong, or the token identity cannot see the channel.
- For private channels, membership is required.

Message posts but links are not labeled

- Confirm the JSON payload includes `"mrkdwn": true`.
- Confirm the text uses Slack syntax:
  `<https://github.com/example-org/example-repo/pull/1234|PR #1234>`.

Unwanted link previews

- Include:
  `"unfurl_links": false, "unfurl_media": false`.

## Minimal Known-Good Example

This exact shape successfully posted a threaded message with a rendered labeled
link:

```bash
set -a
. $HOME/.slack_mcp_bridge_secrets/slack_bot_access.env
set +a

curl -sS -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_USER_WRITE_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data "$(jq -n \
    --arg channel 'C0123456789' \
    --arg thread_ts '1779317505.990209' \
    --arg text 'Test threaded mrkdwn link: <https://github.com/example-org/example-repo/pull/1234|PR #1234>' \
    '{channel:$channel,thread_ts:$thread_ts,text:$text,mrkdwn:true,unfurl_links:false,unfurl_media:false}')" \
  | jq '{ok, channel, ts, error}'
```
