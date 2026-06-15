"""In-call chat case outcome helpers (delivery, trim, rejection).

Các hàm hỗ trợ kết quả case chat trong cuộc gọi (gửi thành công, trim, từ chối).
"""

from __future__ import annotations

from helpers.excel.cells import cell_value
from helpers.excel.load import TestRow

CHAT_MESSAGE_MAX_LENGTH = 200

_OUTCOME_DELIVER = frozenset({"deliver", "delivered", "success", "ok", "1"})
_OUTCOME_REJECT = frozenset({"reject", "rejected", "blocked", "invalid", "0"})
_BOUNDARY_PREFIX = "boundary|"


def _has_non_ascii(text: str) -> bool:
    return any(ord(char) > 127 for char in text)


def _is_special_message(text: str) -> bool:
    if text.startswith("http://") or text.startswith("https://"):
        return True
    if text.startswith("{") and "}" in text:
        return True
    if "<" in text and ">" in text:
        return True
    if "\\" in text:
        return True
    if text.isdigit():
        return True
    if text.startswith("!@") or text.startswith("!#"):
        return True
    if '"' in text and "'" in text:
        return True
    return False


def infer_call_chat_category(case: TestRow) -> str:
    if call_chat_outcome(case) == "reject":
        return "validation"

    message = cell_value(case.get("message")) or ""
    received = cell_value(case.get("received"))
    trimmed = message.strip()

    if message.startswith(_BOUNDARY_PREFIX):
        return "boundary"
    if received is not None and received != trimmed:
        return "boundary"
    if len(trimmed) == 1:
        return "boundary"
    if len(trimmed) >= CHAT_MESSAGE_MAX_LENGTH:
        return "boundary"
    if trimmed != message:
        return "boundary"
    if "  " in message:
        return "boundary"
    if "\t" in message:
        return "boundary"

    if _has_non_ascii(message):
        return "unicode"

    if _is_special_message(message):
        return "special"

    return "smoke"


def call_chat_viewport_layout(case: TestRow) -> str:
    from helpers.browser.viewport import DEFAULT_CHAT_VIEWPORT, normalize_viewport

    explicit = cell_value(case.get("_viewport_layout"))
    if explicit:
        return normalize_viewport(explicit)
    return normalize_viewport(case.get("viewport") or DEFAULT_CHAT_VIEWPORT)


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
