# SPDX-License-Identifier: Apache-2.0

"""Direct Slack Web API client for the local Cursor MCP bridge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from os import environ
from typing import Any
from urllib.parse import parse_qs, urlparse

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackBridgeError(RuntimeError):
    """Raised for user-facing Slack MCP bridge errors."""


def _local_timezone():
    return datetime.now().astimezone().tzinfo


def parse_datetime_with_tz(value: str | None) -> str | None:
    """Convert an ISO-like datetime string to Slack's epoch string."""

    if not value:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    if stripped.replace(".", "", 1).isdigit():
        return stripped
    if stripped.endswith("Z"):
        stripped = stripped[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(stripped)
    except ValueError as exc:
        raise SlackBridgeError(
            f"Invalid datetime string {value!r}. Use ISO-8601, e.g. 2026-05-20T08:00:00-07:00."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_local_timezone())
    return str(parsed.timestamp())


def parse_slack_ref(channel: str, ts: str = "") -> tuple[str, str]:
    """Parse a Slack permalink URL or channel+timestamp pair."""

    if channel.startswith("http"):
        parsed = urlparse(channel)
        parts = parsed.path.rstrip("/").split("/")
        if len(parts) < 2:
            raise SlackBridgeError(f"Could not parse Slack permalink: {channel}")
        channel = parts[-2]
        query = parse_qs(parsed.query)
        if "thread_ts" in query:
            ts = query["thread_ts"][0]
        else:
            raw_ts = parts[-1].lstrip("p")
            ts = raw_ts[:-6] + "." + raw_ts[-6:]
    elif ts.startswith("p"):
        raw_ts = ts[1:]
        ts = raw_ts[:-6] + "." + raw_ts[-6:]
    return channel, ts


def _trim_message_match(match: dict[str, Any]) -> dict[str, Any]:
    return {
        "channel": match.get("channel", {}),
        "type": match.get("type"),
        "user": match.get("user"),
        "username": match.get("username"),
        "ts": match.get("ts"),
        "text": match.get("text", ""),
        "permalink": match.get("permalink"),
        "blocks": match.get("blocks"),
        "attachments": match.get("attachments"),
        "thread_ts": match.get("thread_ts"),
    }


def _trim_history_message(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": message.get("type"),
        "user": message.get("user"),
        "bot_id": message.get("bot_id"),
        "text": message.get("text", ""),
        "ts": message.get("ts"),
        "thread_ts": message.get("thread_ts"),
        "reply_count": message.get("reply_count"),
        "subtype": message.get("subtype"),
        "blocks": message.get("blocks"),
        "attachments": message.get("attachments"),
    }


@dataclass
class SlackBridgeClient:
    """Thin wrapper around a Slack Web API user token."""

    token: str
    team_id: str = ""
    client: WebClient | None = None

    def __post_init__(self) -> None:
        if not self.token:
            raise SlackBridgeError(
                "Missing SLACK_USER_TOKEN. Configure it in the bridge env file."
            )
        if self.client is None:
            self.client = WebClient(token=self.token)

    @classmethod
    def from_env(cls) -> "SlackBridgeClient":
        return cls(
            token=environ.get("SLACK_USER_TOKEN", ""),
            team_id=environ.get("SLACK_TEAM_ID", ""),
        )

    def _call(self, method_name: str, **kwargs: Any) -> dict[str, Any]:
        assert self.client is not None
        method = getattr(self.client, method_name)
        try:
            response = method(**kwargs)
        except SlackApiError as exc:
            error_code = exc.response.get("error", "unknown_error")
            status_code = getattr(exc.response, "status_code", "unknown")
            raise SlackBridgeError(
                f"Slack API error calling {method_name}: {error_code} (HTTP {status_code})"
            ) from exc
        return dict(response.data)

    def health_check(self) -> dict[str, Any]:
        auth = self.auth_test()
        return {
            "status": "healthy",
            "server": "slack-mcp-bridge",
            "auth_type": "Slack user token",
            "message": "Slack user token is accepted by auth.test",
            "auth_info": auth,
        }

    def auth_test(self) -> dict[str, Any]:
        return self._call("auth_test")

    def get_my_info(self) -> dict[str, Any]:
        auth = self.auth_test()
        user_id = auth["user_id"]
        user_info = self._call("users_info", user=user_id)
        return {
            "auth_info": auth,
            "user": user_info.get("user"),
        }

    def lookup_user_by_email(self, email: str) -> dict[str, Any]:
        if not email.strip():
            raise SlackBridgeError("email must not be empty")
        return self._call("users_lookupByEmail", email=email.strip())

    def list_user_channels(
        self,
        limit: int = 200,
        cursor: str | None = None,
        exclude_archived: bool = False,
        types: str = "public_channel,private_channel",
        user: str | None = None,
        team_id: str | None = None,
    ) -> dict[str, Any]:
        response = self._call(
            "users_conversations",
            limit=min(max(limit, 1), 999),
            cursor=cursor,
            exclude_archived=exclude_archived,
            types=types,
            user=user,
            team_id=team_id or self.team_id or None,
        )
        return {
            "ok": response.get("ok", True),
            "channels": response.get("channels", []),
            "response_metadata": response.get("response_metadata", {}),
        }

    def search_messages(
        self,
        query: str,
        count: int = 20,
        page: int = 1,
        highlight: bool = False,
        sort: str | None = None,
        sort_dir: str | None = None,
    ) -> dict[str, Any]:
        if not query.strip():
            raise SlackBridgeError("query must not be empty")
        response = self._call(
            "search_messages",
            query=query,
            count=min(max(count, 1), 100),
            page=max(page, 1),
            highlight=highlight,
            sort=sort,
            sort_dir=sort_dir,
        )
        messages = response.get("messages", {})
        return {
            "ok": response.get("ok", True),
            "query": response.get("query", query),
            "messages": {
                "total": messages.get("total", 0),
                "pagination": messages.get("pagination", {}),
                "paging": messages.get("paging", {}),
                "matches": [
                    _trim_message_match(match) for match in messages.get("matches", [])
                ],
            },
            "users": response.get("users", {}),
            "teams": response.get("teams", {}),
            "bots": response.get("bots", {}),
        }

    def get_conversation_history(
        self,
        channel: str,
        limit: int = 100,
        cursor: str | None = None,
        oldest_datetime_with_tz: str | None = None,
        latest_datetime_with_tz: str | None = None,
        inclusive: bool = False,
    ) -> dict[str, Any]:
        channel_id, oldest = parse_slack_ref(
            channel, parse_datetime_with_tz(oldest_datetime_with_tz) or ""
        )
        latest = parse_datetime_with_tz(latest_datetime_with_tz)
        response = self._call(
            "conversations_history",
            channel=channel_id,
            limit=min(max(limit, 1), 1000),
            cursor=cursor,
            oldest=oldest or None,
            latest=latest,
            inclusive=inclusive,
        )
        return {
            "ok": response.get("ok", True),
            "messages": [
                _trim_history_message(message)
                for message in response.get("messages", [])
            ],
            "has_more": response.get("has_more", False),
            "pin_count": response.get("pin_count"),
            "response_metadata": response.get("response_metadata", {}),
        }

    def get_thread_replies(
        self,
        channel: str,
        ts: str,
        limit: int = 100,
        cursor: str | None = None,
        oldest_datetime_with_tz: str | None = None,
        latest_datetime_with_tz: str | None = None,
        inclusive: bool = False,
    ) -> dict[str, Any]:
        if not ts.strip():
            raise SlackBridgeError("ts must not be empty")
        channel_id, thread_ts = parse_slack_ref(channel, ts)
        response = self._call(
            "conversations_replies",
            channel=channel_id,
            ts=thread_ts,
            limit=min(max(limit, 1), 1000),
            cursor=cursor,
            oldest=parse_datetime_with_tz(oldest_datetime_with_tz),
            latest=parse_datetime_with_tz(latest_datetime_with_tz),
            inclusive=inclusive,
        )
        return {
            "ok": response.get("ok", True),
            "messages": [
                _trim_history_message(message)
                for message in response.get("messages", [])
            ],
            "has_more": response.get("has_more", False),
            "response_metadata": response.get("response_metadata", {}),
        }
