# SPDX-License-Identifier: Apache-2.0

"""Local stdio MCP server that talks directly to Slack Web API."""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from slack_mcp_bridge_client import SlackBridgeClient, SlackBridgeError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _fail(message: str):
    return {"success": False, "data": None, "error": message}


class SlackBridgeServer:
    def __init__(self, client: SlackBridgeClient) -> None:
        self._client = client

    def register(self, mcp: FastMCP) -> None:
        mcp.tool()(self.slack_health_check)
        mcp.tool()(self.slack_get_my_info)
        mcp.tool()(self.slack_lookup_user_by_email)
        mcp.tool()(self.slack_list_user_channels)
        mcp.tool()(self.slack_search_messages)
        mcp.tool()(self.slack_get_conversation_history)
        mcp.tool()(self.slack_get_thread_replies)

    def slack_health_check(self):
        """Validate token health with auth.test."""
        try:
            return _ok(self._client.health_check())
        except SlackBridgeError as exc:
            return _fail(str(exc))

    def slack_get_my_info(self):
        """Return the authenticated Slack user profile."""
        try:
            return _ok(self._client.get_my_info())
        except SlackBridgeError as exc:
            return _fail(str(exc))

    def slack_lookup_user_by_email(self, email: str):
        """Look up a Slack user by email address."""
        try:
            return _ok(self._client.lookup_user_by_email(email=email))
        except SlackBridgeError as exc:
            return _fail(str(exc))

    def slack_list_user_channels(
        self,
        limit: int = 200,
        cursor: str | None = None,
        exclude_archived: bool = False,
        types: str = "public_channel,private_channel",
        user: str | None = None,
        team_id: str | None = None,
    ):
        """List the channels visible to the authenticated user."""
        try:
            return _ok(
                self._client.list_user_channels(
                    limit=limit,
                    cursor=cursor,
                    exclude_archived=exclude_archived,
                    types=types,
                    user=user,
                    team_id=team_id,
                )
            )
        except SlackBridgeError as exc:
            return _fail(str(exc))

    def slack_search_messages(
        self,
        query: str,
        count: int = 20,
        page: int = 1,
        highlight: bool = False,
        sort: str | None = None,
        sort_dir: str | None = None,
    ):
        """Search Slack messages using Slack's native search syntax."""
        try:
            return _ok(
                self._client.search_messages(
                    query=query,
                    count=count,
                    page=page,
                    highlight=highlight,
                    sort=sort,
                    sort_dir=sort_dir,
                )
            )
        except SlackBridgeError as exc:
            return _fail(str(exc))

    def slack_get_conversation_history(
        self,
        channel: str,
        limit: int = 100,
        cursor: str | None = None,
        oldest_datetime_with_tz: str | None = None,
        latest_datetime_with_tz: str | None = None,
        inclusive: bool = False,
    ):
        """Read messages from a channel, private channel, DM, or MPIM."""
        try:
            return _ok(
                self._client.get_conversation_history(
                    channel=channel,
                    limit=limit,
                    cursor=cursor,
                    oldest_datetime_with_tz=oldest_datetime_with_tz,
                    latest_datetime_with_tz=latest_datetime_with_tz,
                    inclusive=inclusive,
                )
            )
        except SlackBridgeError as exc:
            return _fail(str(exc))

    def slack_get_thread_replies(
        self,
        channel: str,
        ts: str,
        limit: int = 100,
        cursor: str | None = None,
        oldest_datetime_with_tz: str | None = None,
        latest_datetime_with_tz: str | None = None,
        inclusive: bool = False,
    ):
        """Read a Slack thread by channel ID/permalink and root timestamp."""
        try:
            return _ok(
                self._client.get_thread_replies(
                    channel=channel,
                    ts=ts,
                    limit=limit,
                    cursor=cursor,
                    oldest_datetime_with_tz=oldest_datetime_with_tz,
                    latest_datetime_with_tz=latest_datetime_with_tz,
                    inclusive=inclusive,
                )
            )
        except SlackBridgeError as exc:
            return _fail(str(exc))


def main() -> None:
    client = SlackBridgeClient.from_env()
    mcp = FastMCP(name="slack-mcp-bridge")
    SlackBridgeServer(client).register(mcp)
    logger.info("Starting local Slack MCP bridge.")
    mcp.run()


if __name__ == "__main__":
    main()
