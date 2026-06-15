"""In-call chat cases (smoke array now; Excel sheet ``call_chat`` later).

Các case chat trong cuộc gọi (mảng smoke hiện tại; sheet Excel ``call_chat`` sau).
"""

from __future__ import annotations

from pathlib import Path

from helpers.call.chat_validation import CHAT_MESSAGE_MAX_LENGTH
from helpers.excel.cells import DATA_XLSX, cell_value
from helpers.excel.load import TestRow, load_excel

CALL_CHAT_SHEET = "call_chat"

_BOUNDARY_TAG = "boundary|"
_A200 = _BOUNDARY_TAG + ("a" * (CHAT_MESSAGE_MAX_LENGTH - len(_BOUNDARY_TAG)))
_B201 = _BOUNDARY_TAG + ("b" * (CHAT_MESSAGE_MAX_LENGTH + 1 - len(_BOUNDARY_TAG)))
_C400 = _BOUNDARY_TAG + ("c" * (CHAT_MESSAGE_MAX_LENGTH * 2 - len(_BOUNDARY_TAG)))
_D401 = _BOUNDARY_TAG + ("d" * (CHAT_MESSAGE_MAX_LENGTH * 2 + 1 - len(_BOUNDARY_TAG)))

CALL_CHAT_SMOKE_CASES: list[TestRow] = [
    # --- smoke: basic bidirectional delivery ---
    {
        "category": "smoke",
        "sender": "user1",
        "receiver": "user2",
        "message": "hello-from-user1",
        "outcome": "deliver",
    },
    {
        "category": "smoke",
        "sender": "user2",
        "receiver": "user1",
        "message": "hello-from-user2",
        "outcome": "deliver",
    },
    {
        "category": "smoke",
        "sender": "user_a",
        "receiver": "user_b",
        "message": "alias-user-a-to-b",
        "outcome": "deliver",
    },
    # --- boundary: length limits ---
    {
        "category": "boundary",
        "sender": "user1",
        "receiver": "user2",
        "message": "a",
        "outcome": "deliver",
    },
    {
        "category": "boundary",
        "sender": "user2",
        "receiver": "user1",
        "message": _A200,
        "outcome": "deliver",
    },
    {
        "category": "boundary",
        "sender": "user1",
        "receiver": "user2",
        "message": _B201,
        "outcome": "deliver",
    },
    {
        "category": "boundary",
        "sender": "user2",
        "receiver": "user1",
        "message": _C400,
        "outcome": "deliver",
    },
    {
        "category": "boundary",
        "sender": "user1",
        "receiver": "user2",
        "message": _D401,
        "outcome": "deliver",
    },
    # --- boundary: trim / whitespace preservation ---
    {
        "category": "boundary",
        "sender": "user2",
        "receiver": "user1",
        "message": "  trimmed message  ",
        "received": "trimmed message",
        "outcome": "deliver",
    },
    {
        "category": "boundary",
        "sender": "user1",
        "receiver": "user2",
        "message": "\n\t leading-trailing ws \n",
        "received": "leading-trailing ws",
        "outcome": "deliver",
    },
    {
        "category": "boundary",
        "sender": "user2",
        "receiver": "user1",
        "message": "word one  word   two",
        "outcome": "deliver",
    },
    {
        "category": "boundary",
        "sender": "user1",
        "receiver": "user2",
        "message": "tab\tseparated\tvalues",
        "outcome": "deliver",
    },
    # --- validation: empty / whitespace-only rejected ---
    {
        "category": "validation",
        "sender": "user1",
        "receiver": "user2",
        "message": "",
        "outcome": "reject",
    },
    {
        "category": "validation",
        "sender": "user2",
        "receiver": "user1",
        "message": "   ",
        "outcome": "reject",
    },
    {
        "category": "validation",
        "sender": "user1",
        "receiver": "user2",
        "message": "\n\t  \n",
        "outcome": "reject",
    },
    # --- unicode / i18n ---
    {
        "category": "unicode",
        "sender": "user2",
        "receiver": "user1",
        "message": "Hello 👋 from user2",
        "outcome": "deliver",
    },
    {
        "category": "unicode",
        "sender": "user1",
        "receiver": "user2",
        "message": "Xin chào từ user1",
        "outcome": "deliver",
    },
    {
        "category": "unicode",
        "sender": "user2",
        "receiver": "user1",
        "message": "你好世界",
        "outcome": "deliver",
    },
    {
        "category": "unicode",
        "sender": "user1",
        "receiver": "user2",
        "message": "مرحبا hello mixed-script",
        "outcome": "deliver",
    },
    # --- special characters / injection-safe literals ---
    {
        "category": "special",
        "sender": "user2",
        "receiver": "user1",
        "message": '<script>alert("xss")</script>',
        "outcome": "deliver",
    },
    {
        "category": "special",
        "sender": "user1",
        "receiver": "user2",
        "message": "https://example.com/path?q=1&x=2",
        "outcome": "deliver",
    },
    {
        "category": "special",
        "sender": "user2",
        "receiver": "user1",
        "message": '{"key":"value","nested":{"n":1}}',
        "outcome": "deliver",
    },
    {
        "category": "special",
        "sender": "user1",
        "receiver": "user2",
        "message": 'He said "hello" and \'bye\'',
        "outcome": "deliver",
    },
    {
        "category": "special",
        "sender": "user2",
        "receiver": "user1",
        "message": "path\\to\\file",
        "outcome": "deliver",
    },
    {
        "category": "special",
        "sender": "user1",
        "receiver": "user2",
        "message": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
        "outcome": "deliver",
    },
    {
        "category": "special",
        "sender": "user2",
        "receiver": "user1",
        "message": "1234567890",
        "outcome": "deliver",
    },
]


def load_call_chat_cases(*, path: Path = DATA_XLSX) -> list[TestRow]:
    if path.is_file():
        workbook = load_excel(path)
        sheet_cases = workbook.get(CALL_CHAT_SHEET)
        if sheet_cases:
            return sheet_cases
    return list(CALL_CHAT_SMOKE_CASES)


def call_chat_case_id(index: int, case: TestRow) -> str:
    category = cell_value(case.get("category")) or "smoke"
    sender = cell_value(case.get("sender")) or "sender"
    receiver = cell_value(case.get("receiver")) or "receiver"
    outcome = cell_value(case.get("outcome")) or "deliver"
    message = cell_value(case.get("message")) or f"row-{index + 1}"
    slug = message.lower().replace(" ", "-")[:32]
    if len(message) > 32:
        slug = f"{slug}-len{len(message)}"
    return f"{category}-{outcome}-{sender}-to-{receiver}-{slug}"
