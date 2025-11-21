# Mail-to-Telegram

Simple IMAP -> Telegram forwarder designed to deploy on Railway.

Required ENV:
- IMAP_SERVER (e.g. imap.zoho.com)
- IMAP_PORT (default 993)
- IMAP_USER
- IMAP_PASSWORD (use app-password if provider needs)
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- POLL_INTERVAL (optional)
- MAILBOX (optional)
