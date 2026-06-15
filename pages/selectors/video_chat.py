"""Video chat page CSS selectors.

Selector CSS cho trang video chat.
"""

from __future__ import annotations

_SIDEBAR_SUB_PARENTS: dict[str, str] = {
    "callHistory": "connections",
    "favorites": "connections",
    "blockedUsers": "connections",
}


def testid(name: str) -> str:
    return f'[data-testid="{name}"]'


def sidebar_nav(nav_id: str) -> str:
    return testid(f"sidebar-nav-{nav_id}")


def connection_container(status: str) -> str:
    return f'{testid("chat-video-container")}[data-connection-status="{status}"]'


def stream_quality_option(quality: str) -> str:
    return testid(f"chat-stream-quality-option-{quality}")


CHAT_IDLE_CONTAINER = testid("chat-idle-container")
CHAT_IDLE_PROGRESS_CARD = testid("chat-idle-progress-card")
CHAT_START_BUTTON = testid("chat-start-button")
CHAT_SEARCHING_INDICATOR = testid("chat-searching-indicator")
CHAT_SEARCHING_CARD = testid("chat-searching-card")
CHAT_CANCEL_SEARCH_BUTTON = testid("chat-cancel-search-button")
CHAT_VIDEO_CONTAINER = testid("chat-video-container")
CHAT_LOCAL_VIDEO = testid("chat-local-video")
CHAT_REMOTE_VIDEO = testid("chat-remote-video")
CHAT_CAMERA_OFF_INDICATOR = testid("chat-camera-off-indicator")
CHAT_CALL_TIMER = testid("chat-call-timer")
CHAT_CONTROLS_BAR = testid("chat-controls-bar")
CHAT_MUTE_BUTTON = testid("chat-mute-button")
CHAT_VIDEO_TOGGLE_BUTTON = testid("chat-video-toggle-button")
CHAT_END_CALL_BUTTON = testid("chat-end-call-button")
CHAT_OVERFLOW_MENU_BUTTON = testid("chat-overflow-menu-button")
CHAT_TOGGLE_BUTTON = testid("chat-toggle-button")
CHAT_SIDEBAR = testid("chat-sidebar")
CHAT_SIDEBAR_SHEET = testid("chat-sidebar-sheet")
CHAT_FULL_PAGE_CLIENT = testid("chat-full-page-client")
CHAT_FULL_PAGE = testid("chat-full-page")
CHAT_BACK_TO_CALL_BUTTON = testid("chat-back-to-call-button")
CHAT_MESSAGES_CONTAINER = testid("chat-messages-container")
CHAT_INPUT = testid("chat-input")
CHAT_SEND_BUTTON = testid("chat-send-button")
CALL_HISTORY_PAGE = testid("call-history-page")
CALL_HISTORY_TABLE = testid("call-history-table")
CALL_HISTORY_REFRESH_BUTTON = testid("call-history-refresh-button")
SIDEBAR_VIDEO_CHAT = sidebar_nav("videoChat")
SIDEBAR_CALL_HISTORY = sidebar_nav("callHistory")
SIDEBAR_CONNECTIONS = sidebar_nav("connections")
SIDEBAR_TRIGGER = testid("sidebar-trigger")


def sidebar_sub_parent(sub_nav_id: str) -> str | None:
    return _SIDEBAR_SUB_PARENTS.get(sub_nav_id)
