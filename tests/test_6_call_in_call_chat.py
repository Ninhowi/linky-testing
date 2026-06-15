"""In-call chat cases (smoke array; Excel sheet ``call_chat`` later).

Các case chat khi đang in_call — mảng smoke; sheet Excel ``call_chat`` sau.
Desktop opens the chat sheet; mobile navigates to ``/call/chat``.
"""

from __future__ import annotations

import pytest

from helpers.call.chat_excel import call_chat_case_id, load_call_chat_cases
from helpers.call.chat_flow import run_call_chat_exchange
from helpers.excel.load import TestRow
from pages.video_chat import VideoChatPage

pytestmark = [
    pytest.mark.call,
    pytest.mark.call_in_call_chat,
    pytest.mark.xdist_group("call"),
]

CALL_CHAT_CASES = load_call_chat_cases()


@pytest.mark.parametrize(
    "call_chat_case",
    CALL_CHAT_CASES,
    ids=[call_chat_case_id(i, row) for i, row in enumerate(CALL_CHAT_CASES)],
)
def test_in_call_chat_exchange(
    in_call_chat_pair: tuple[VideoChatPage, VideoChatPage],
    call_chat_case: TestRow,
    chat_viewport_users: tuple[str, str],
) -> None:
    """Each row: sender opens chat, sends text; receiver sees it (same matched call).

    Mỗi dòng: người gửi mở chat, gửi tin; người nhận thấy tin (cùng cuộc gọi đã ghép).
    """
    page_a, page_b = in_call_chat_pair
    user1_viewport, user2_viewport = chat_viewport_users
    assert page_a.is_mobile_viewport() == (user1_viewport == "mobile")
    assert page_b.is_mobile_viewport() == (user2_viewport == "mobile")
    run_call_chat_exchange(page_a, page_b, call_chat_case)
