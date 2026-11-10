---
name: send
track: bonus
kind: action
provider: Telegram Bot API
requires_env: [TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]
inputs: [text, confirmed]
outputs: [status]
side_effect: true
---
# send

Posts text to a Telegram channel. The message is only sent when `confirmed` is true.

## Input boundary regression

Only the literal boolean confirmed=True authorizes sending. Strings (including
"true" and "false"), numbers and objects return needs_confirmation without HTTP.
