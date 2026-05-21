# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from slack_mcp_bridge_client import (
    SlackBridgeClient,
    SlackBridgeError,
    parse_datetime_with_tz,
    parse_slack_ref,
)


def test_parse_datetime_with_offset():
    result = parse_datetime_with_tz("2026-05-20T08:00:00-07:00")
    assert result is not None
    assert float(result) > 0


def test_parse_datetime_rejects_bad_input():
    with pytest.raises(SlackBridgeError):
        parse_datetime_with_tz("not-a-datetime")


def test_parse_slack_ref_permalink():
    channel, ts = parse_slack_ref(
        "https://example.slack.com/archives/C0123456789/p1774285195355159"
    )
    assert channel == "C0123456789"
    assert ts == "1774285195.355159"


def test_parse_slack_ref_p_prefixed_ts():
    channel, ts = parse_slack_ref("C0123456789", "p1774285195355159")
    assert channel == "C0123456789"
    assert ts == "1774285195.355159"


def test_search_messages_trims_matches():
    fake_client = MagicMock()
    fake_client.search_messages.return_value.data = {
        "ok": True,
        "query": "from:me",
        "messages": {
            "total": 1,
            "pagination": {"page": 1},
            "paging": {"count": 1},
            "matches": [
                {
                    "channel": {"id": "D1", "name": "dm"},
                    "type": "im",
                    "user": "U1",
                    "username": "me",
                    "ts": "123.456",
                    "text": "hello",
                    "permalink": "https://example.invalid",
                    "extra_field": "ignored",
                }
            ],
        },
    }
    bridge = SlackBridgeClient(token="xoxp-test", client=fake_client)

    result = bridge.search_messages(query="from:me", count=5)

    assert result["messages"]["total"] == 1
    assert result["messages"]["matches"][0]["text"] == "hello"
    assert "extra_field" not in result["messages"]["matches"][0]


def test_get_conversation_history_uses_history_api():
    fake_client = MagicMock()
    fake_client.conversations_history.return_value.data = {
        "ok": True,
        "messages": [{"text": "hello", "ts": "123.456", "user": "U1"}],
        "response_metadata": {"next_cursor": ""},
    }
    bridge = SlackBridgeClient(token="xoxp-test", client=fake_client)

    result = bridge.get_conversation_history(channel="C123", limit=20)

    assert result["messages"][0]["text"] == "hello"
    fake_client.conversations_history.assert_called_once()
