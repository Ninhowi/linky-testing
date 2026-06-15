"""Viewport sizes aligned with ``useIsMobile`` (breakpoint 768px).

Kích thước viewport khớp ``useIsMobile`` (breakpoint 768px).
"""

from __future__ import annotations

MOBILE_BREAKPOINT_PX = 768
DESKTOP_VIEWPORT = (1280, 720)
MOBILE_VIEWPORT = (390, 844)

VIEWPORT_SIZES = {
    "desktop": DESKTOP_VIEWPORT,
    "mobile": MOBILE_VIEWPORT,
}

CHAT_VIEWPORT_LAYOUTS = (
    "desktop",
    "mobile",
    "desktop+mobile",
    "mobile+desktop",
)


def parse_viewport_layout(layout: str) -> tuple[str, str]:
    if "+" in layout:
        user1, user2 = layout.split("+", 1)
        return user1.strip(), user2.strip()
    return layout, layout


def apply_viewport_layout(
    driver_user1,
    driver_user2,
    layout: str,
) -> tuple[str, str]:
    user1_viewport, user2_viewport = parse_viewport_layout(layout)
    w1, h1 = VIEWPORT_SIZES[user1_viewport]
    w2, h2 = VIEWPORT_SIZES[user2_viewport]
    driver_user1.set_window_size(w1, h1)
    driver_user2.set_window_size(w2, h2)
    return user1_viewport, user2_viewport
