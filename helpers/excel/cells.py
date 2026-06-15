"""Shared Excel cell parsing and workbook case loading.

Phân tích ô Excel dùng chung và nạp case từ workbook.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from helpers.excel.load import TestRow, load_excel

ROOT = Path(__file__).resolve().parents[2]
DATA_XLSX = ROOT / "test_data" / "data.xlsx"


def load_sheet_cases(sheet: str, *, path: Path = DATA_XLSX) -> list[TestRow]:
    """Load test rows for one sheet from the default or given Excel workbook.

    Nạp các dòng test cho một sheet từ workbook Excel mặc định hoặc chỉ định.
    """
    workbook = load_excel(path)
    cases = workbook.get(sheet)
    if cases is None:
        available = ", ".join(workbook) or "(none)"
        raise ValueError(
            f"Sheet {sheet!r} not found in {path.name}. "
            f"Available sheets: {available}"
        )
    return cases


def cell_input(value: object) -> str:
    """Cell content as string; leading/trailing spaces are kept for form input.

    Nội dung ô dưới dạng chuỗi; giữ nguyên khoảng trắng đầu/cuối khi nhập form.
    """
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value)


def cell_text(value: object) -> str:
    """Trimmed cell text for messages, flags, and other non-input fields.

    Văn bản ô đã cắt khoảng trắng, dùng cho thông báo, cờ và các trường không phải nhập liệu.
    """
    return cell_input(value).strip()


def cell_value(value: object) -> str | None:
    """Return cell text, or ``None`` when the cell is empty.

    Trả về văn bản ô, hoặc ``None`` khi ô trống.
    """
    text = cell_input(value)
    return text if text != "" else None


def excel_flag(case: TestRow, column: str) -> bool | None:
    """Parse a 0/1 Excel flag column; ``None`` when the cell is empty.

    Phân tích cột cờ 0/1 trong Excel; ``None`` khi ô trống.
    """
    value = case.get(column)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return cell_text(value) not in ("0", "false", "no", "")


def message_lower(case: TestRow) -> str:
    """Return the row ``message`` column in lowercase.

    Trả về cột ``message`` của dòng ở dạng chữ thường.
    """
    return cell_text(case.get("message")).lower()


def case_id(prefix: str, index: int, case: TestRow) -> str:
    """Build a stable pytest parametrize id from prefix, row index, and message.

    Tạo id pytest parametrize ổn định từ prefix, chỉ số dòng và message.
    """
    message = cell_text(case.get("message"))
    if message:
        return f"{prefix}-{index + 1}-{message[:40]}"
    return f"{prefix}-{index + 1}-pass"
