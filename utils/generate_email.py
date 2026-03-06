import time
from typing import Literal


def generate_email(
    base_email: str | None,
    enable_generate_email: bool = True,
    auto_remove_content: str | None = None,
    auto_remove_content_position: Literal["prefix", "suffix", "include"] | None = None,
) -> str:
    if not enable_generate_email:
        return base_email or ""

    if not base_email:
        return ""

    if "@" not in base_email:
        return base_email

    local, domain = base_email.split("@", 1)

    if "+clerk_test" not in local.lower():
        return base_email

    prefix, suffix = local.split("+", 1)
    timestamp = str(int(time.time()))

    if not auto_remove_content or not auto_remove_content_position:
        return f"{prefix}{timestamp}+{suffix}@{domain}"

    content = auto_remove_content

    if auto_remove_content_position == "prefix":
        new_local = f"{content}{prefix}{timestamp}"
    elif auto_remove_content_position == "suffix":
        new_local = f"{prefix}{timestamp}{content}"
    elif auto_remove_content_position == "include":
        new_local = f"{prefix}{content}{timestamp}"
    else:
        new_local = f"{prefix}{timestamp}"

    return f"{new_local}+{suffix}@{domain}"