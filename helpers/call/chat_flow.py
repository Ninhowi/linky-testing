"""Run in-call chat exchanges without rematching.

Thực hiện trao đổi chat trong cuộc gọi mà không ghép cặp lại.
"""

from __future__ import annotations

from helpers.browser.waits import DEFAULT_TIMEOUT_SEC
from helpers.call.chat_validation import (
    call_chat_chunk_count,
    call_chat_expects_delivery,
    call_chat_received_text,
)
from helpers.excel.cells import cell_value
from helpers.excel.load import TestRow
from pages.video_chat import VideoChatPage

_USER1_ALIASES = frozenset({"user1", "user_a", "a", "1"})
_USER2_ALIASES = frozenset({"user2", "user_b", "b", "2"})


def _normalize_role(value: object, *, field: str) -> str:
    role = (cell_value(value) or "").strip().lower()
    if not role:
        raise ValueError(f"Missing {field} in call chat case")
    return role


def _page_for_role(
    role: str,
    page_a: VideoChatPage,
    page_b: VideoChatPage,
    *,
    field: str,
) -> VideoChatPage:
    if role in _USER1_ALIASES:
        return page_a
    if role in _USER2_ALIASES:
        return page_b
    raise ValueError(f"Unknown {field} role: {role!r} (use user1 or user2)")


def _message_wait_timeout(text: str) -> float:
    chunks = call_chat_chunk_count(text)
    if chunks <= 1:
        return DEFAULT_TIMEOUT_SEC
    return DEFAULT_TIMEOUT_SEC + (chunks - 1) * 5.0


def ensure_in_call_pair(page_a: VideoChatPage, page_b: VideoChatPage) -> None:
    page_a.ensure_in_call()
    page_b.ensure_in_call()


def run_call_chat_exchange(
    page_a: VideoChatPage,
    page_b: VideoChatPage,
    case: TestRow,
) -> None:
    ensure_in_call_pair(page_a, page_b)

    if "message" not in case:
        raise ValueError("Missing message in call chat case")

    message = cell_value(case.get("message"))
    if message is None and call_chat_expects_delivery(case):
        raise ValueError("Missing message in call chat case")

    sender_role = _normalize_role(case.get("sender"), field="sender")
    receiver_role = _normalize_role(case.get("receiver"), field="receiver")

    sender = _page_for_role(sender_role, page_a, page_b, field="sender")
    receiver = _page_for_role(receiver_role, page_a, page_b, field="receiver")

    sender.ensure_chat_open()

    if call_chat_expects_delivery(case):
        assert message is not None
        sender.send_message(message)
        expected = call_chat_received_text(case)
        assert expected is not None
        receiver.wait_message_text(
            expected,
            timeout=_message_wait_timeout(expected),
        )
        return

    sender.fill_chat_input(message or "")
    assert not sender.is_send_enabled(), (
        "Expected send button disabled for rejected chat message"
    )
    receiver.assert_message_not_visible(message or "")
