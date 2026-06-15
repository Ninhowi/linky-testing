"""In-call chat case outcome helpers (delivery, trim, rejection).

Các hàm hỗ trợ kết quả case chat trong cuộc gọi (gửi thành công, trim, từ chối).
"""

from __future__ import annotations

from helpers.excel.cells import cell_value
from helpers.excel.load import TestRow

CHAT_MESSAGE_MAX_LENGTH = 200

_OUTCOME_DELIVER = frozenset({"deliver", "delivered", "success", "ok", "1"})
_OUTCOME_REJECT = frozenset({"reject", "rejected", "blocked", "invalid", "0"})


def call_chat_category(case: TestRow) -> str:
    return (cell_value(case.get("category")) or "smoke").strip().lower()


def call_chat_outcome(case: TestRow) -> str:
    raw = (cell_value(case.get("outcome")) or "deliver").strip().lower()
    if raw in _OUTCOME_REJECT:
        return "reject"
    return "deliver"


def call_chat_expects_delivery(case: TestRow) -> bool:
    return call_chat_outcome(case) == "deliver"


def call_chat_received_text(case: TestRow) -> str | None:
    explicit = cell_value(case.get("received"))
    if explicit is not None:
        return explicit

    message = cell_value(case.get("message"))
    if message is None or not call_chat_expects_delivery(case):
        return None
    return message.strip()


def call_chat_chunk_count(text: str) -> int:
    return len(call_chat_message_chunks(text))


def call_chat_message_chunks(text: str) -> list[str]:
    trimmed = text.strip()
    if not trimmed:
        return []
    return [
        trimmed[index : index + CHAT_MESSAGE_MAX_LENGTH]
        for index in range(0, len(trimmed), CHAT_MESSAGE_MAX_LENGTH)
    ]
