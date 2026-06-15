# In-call chat test data (`call_chat` sheet)

Excel sheet **`call_chat`** in `test_data/data.xlsx` drives parametrized in-call chat tests in `tests/test_6_call_in_call_chat.py`.

Until that sheet exists, cases fall back to the smoke array in `helpers/call/chat_excel.py` (`CALL_CHAT_SMOKE_CASES`).

Each **row** is one test case. Row 1 = column headers; row 2+ = cases.

---

## Row keys (columns)

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `sender` | yes | — | Which browser sends the message. See [Sender / receiver roles](#sender--receiver-roles). |
| `receiver` | yes | — | Which browser must see the message. |
| `message` | yes* | — | Text typed into `chat-input` and sent (or attempted). *Column must be present; value may be empty for `reject` cases. |
| `outcome` | no | `deliver` | Expected result: message is delivered to the peer, or send is blocked. See [Outcome values](#outcome-values). |
| `received` | no | `message.strip()` | Text the receiver must see in `chat-messages-container`. Use when trim/normalization changes the visible text. |
| `viewport` | no | `desktop` | Screen layout for user1 + user2. See [Viewport values](#viewport-values). |

**Category is not a column.** It is inferred automatically for pytest IDs (see [Auto-detected category](#auto-detected-category)).

### Minimal row

```text
sender | receiver | message
user1  | user2      | hello-from-user1
```

### Row with optional columns

```text
sender | receiver | message              | outcome | received        | viewport
user2  | user1      |   trimmed message    | deliver | trimmed message | desktop+mobile
```

---

## Viewport values

| `viewport` | user1 | user2 | Notes |
|------------|-------|-------|-------|
| `desktop` | desktop | desktop | **Default** — both browsers at 1280×720 |
| `mobile` | mobile | mobile | Both at 390×844 |
| `desktop+mobile` | desktop | mobile | Mixed layout |
| `mobile+desktop` | mobile | desktop | Mixed layout (reversed) |
| `all` | — | — | Expands to **four tests**: all layouts above |

Omitted or blank `viewport` = `desktop`.

A row with `viewport: all` produces four parametrized tests (one per layout). Matched pairs are cached per layout so rematching only happens once per layout, not per row.

---

## Auto-detected category

Used only in pytest test IDs (`call_chat_case_id`). Detection order in `infer_call_chat_category`:

| Category | Detected when |
|----------|----------------|
| `validation` | `outcome` is `reject` |
| `boundary` | `boundary|` prefix, `received` differs from trimmed `message`, length 1 or ≥ 200, leading/trailing whitespace, double spaces, or tab characters |
| `unicode` | Message contains non-ASCII characters |
| `special` | URL, JSON-like text, HTML-like tags, backslashes, digits-only, heavy punctuation, or mixed quotes |
| `smoke` | Everything else (basic delivery, role aliases) |

---

## Sender / receiver roles

Both columns identify **which matched browser** acts in the scenario. They are resolved by `helpers/call/chat_flow.py`.

| Value | Maps to |
|-------|---------|
| `user1`, `user_a`, `a`, `1` | First browser in the pair (`page_a`) |
| `user2`, `user_b`, `b`, `2` | Second browser in the pair (`page_b`) |

Matching is case-insensitive. Any other value raises `ValueError`.

---

## Outcome values

| `outcome` | Aliases | Test behaviour |
|-----------|---------|----------------|
| `deliver` | `delivered`, `success`, `ok`, `1` | Sender opens chat, fills `message`, clicks send. Receiver must see `received` (or trimmed `message`) in the chat panel. |
| `reject` | `rejected`, `blocked`, `invalid`, `0` | Sender fills `message` but **send stays disabled** (empty / whitespace-only). Receiver must **not** show the raw text. |

Omitted `outcome` is treated as `deliver`.

### App rules (what rows should reflect)

- Max **200 characters** per socket message; longer text is split into multiple chunks client-side.
- Leading/trailing whitespace is trimmed before send.
- Empty or whitespace-only text cannot be sent (`chat-send-button` disabled).

---

## `received` column

Use when the UI shows different text than the raw `message` cell.

| Scenario | `message` | `received` |
|----------|-----------|------------|
| Trim | `"  hello  "` | `hello` |
| Normal | `hello-from-user1` | *(omit — defaults to `hello-from-user1`)* |
| Long / chunked | `boundary|bbb…` (201+ chars) | *(omit — full trimmed text; test waits per 200-char chunk)* |

If `outcome` is `reject`, `received` is ignored.

---

## How a row is executed

1. **`load_call_chat_cases`** expands `viewport: all` into separate rows (one per layout).
2. **Fixture `in_call_chat_pair`**: two browsers log in, match once per viewport layout (cached).
3. **`run_call_chat_exchange`** (`helpers/call/chat_flow.py`):
   - Ensures both sides are still `in_call`
   - Resolves `sender` / `receiver` pages
   - Runs deliver or reject flow per `outcome`

Run:

```bash
uv run python -m pytest tests/test_6_call_in_call_chat.py -m call_in_call_chat
```

---

## Excel setup

1. Add sheet **`call_chat`** to `test_data/data.xlsx`.
2. Row 1 headers (order flexible): `sender`, `receiver`, `message`, `outcome`, `received`, `viewport`.
3. Leave optional columns blank to use defaults (`outcome` → `deliver`, `viewport` → `desktop`).
4. When the sheet has at least one data row, it replaces `CALL_CHAT_SMOKE_CASES`.

**Tips**

- For messages **> 200 chars**, prefer a short prefix (e.g. `boundary|`) so chunked delivery is easy to assert.
- Do not put formulas that strip leading spaces if you are testing trim behaviour.
- Use `viewport: all` only when a case must run on every layout; otherwise leave blank for faster runs.
- GIF/sticker/image chat is **not** covered by this sheet (text only).

---

## Example rows

| sender | receiver | message | outcome | received | viewport |
|--------|----------|---------|---------|----------|----------|
| user1 | user2 | hello-from-user1 | deliver | | |
| user2 | user1 | hello-from-user2 | deliver | | mobile |
| user1 | user2 | `  trimmed  ` | deliver | trimmed | desktop+mobile |
| user1 | user2 | | reject | | |
| user1 | user2 | Xin chào | deliver | | all |
| user2 | user1 | `<script>alert(1)</script>` | deliver | | |

---

## Related code

| File | Role |
|------|------|
| `helpers/call/chat_excel.py` | Load sheet / smoke array, expand viewport, build pytest IDs |
| `helpers/call/chat_validation.py` | Infer category, parse `outcome` / `received` / viewport |
| `helpers/browser/viewport.py` | Viewport sizes and layout expansion |
| `helpers/call/chat_flow.py` | Execute one row against a matched pair |
| `tests/test_6_call_in_call_chat.py` | Parametrized tests |
| `pages/video_chat.py` | Chat UI actions (`send_message`, `wait_message_text`, …) |
