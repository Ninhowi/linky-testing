"""Clerk form CSS selectors (field names, scoped inputs, buttons).

Selector CSS cho form Clerk (tên trường, input scoped, nút).
"""

from __future__ import annotations

from helpers.browser.locators import scoped_css

_CLERK_SCOPE = '[data-clerk-ready="true"] '

_EMAIL_FIELDS = (
    'input[name="identifier"], input#identifier, '
    'input[name="emailAddress"], input#emailAddress, '
    'input[type="email"]'
)
_PASSWORD_FIELDS = 'input[name="password"], input#password, input[type="password"]'
_LEGAL_FIELDS = 'input[name="legalAccepted"], input#legalAccepted-field'
_OTP_INPUT_CSS = (
    'input[autocomplete="one-time-code"], input[name*="code"], '
    'input[name*="otp"], input[inputmode="numeric"]'
)

_EMAIL_INPUT_SCOPED_CSS = scoped_css(_CLERK_SCOPE, _EMAIL_FIELDS)
_PASSWORD_INPUT_SCOPED_CSS = scoped_css(_CLERK_SCOPE, _PASSWORD_FIELDS)
_LEGAL_INPUT_SCOPED_CSS = scoped_css(_CLERK_SCOPE, _LEGAL_FIELDS)
_OTP_INPUT_LOCATOR = ("css selector", _OTP_INPUT_CSS)

_NEW_PASSWORD_FIELDS = 'input[name="password"], input#password-field'
_CONFIRM_PASSWORD_FIELDS = (
    'input[name="confirmPassword"], input#confirmPassword-field'
)
_SIGN_OUT_FIELDS = (
    'input[name="signOutOfOtherSessions"], input#signOutOfOtherSessions-field'
)
_NEW_PASSWORD_SCOPED = scoped_css(_CLERK_SCOPE, _NEW_PASSWORD_FIELDS)
_CONFIRM_PASSWORD_SCOPED = scoped_css(_CLERK_SCOPE, _CONFIRM_PASSWORD_FIELDS)
_SIGN_OUT_SCOPED = scoped_css(_CLERK_SCOPE, _SIGN_OUT_FIELDS)

_SUBMIT_BUTTON_CSS = (
    '[data-localization-key="signIn.resetPassword.formButtonPrimary"], '
    '[data-localization-key="taskResetPassword.formButtonPrimary"]'
)
