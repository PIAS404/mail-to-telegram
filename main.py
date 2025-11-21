#!/usr/bin/env python3
# main.py - IMAP -> Telegram forwarder (simple polling)
import imaplib
import email
import time
import os
import requests
from email.header import decode_header

IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
MAILBOX = os.getenv("MAILBOX", "INBOX")
MAX_BODY_CHARS = int(os.getenv("MAX_BODY_CHARS", "800"))

def clean_subject(subject):
    if subject is None:
        return "(no subject)"
    dh = decode_header(subject)
    parts = []
    for part, enc in dh:
        if isinstance(part, bytes):
            parts.append(part.decode(enc or "utf-8", "ignore"))
        else:
            parts.append(part)
    return "".join(parts)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=data, timeout=15)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)

def parse_mail(raw):
    msg = email.message_from_bytes(raw)
    subject = clean_subject(msg.get("Subject"))
    frm = msg.get("From")
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ctype == "text/plain" and "attachment" not in disp:
                try:
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "ignore")
                except:
                    body = part.get_payload(decode=True).decode("utf-8", "ignore")
                break
    else:
        try:
            body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", "ignore")
        except:
            body = str(msg.get_payload())

    snippet = body.strip().replace("\r","").replace("\n\n","\n")
    if len(snippet) > MAX_BODY_CHARS:
        snippet = snippet[:MAX_BODY_CHARS] + "\n... (truncated)"
    return subject, frm, snippet

def main_loop():
    print("Starting IMAP -> Telegram forwarder...")
    while True:
        try:
            imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            imap.login(IMAP_USER, IMAP_PASSWORD)
            imap.select(MAILBOX)
            status, messages = imap.search(None, '(UNSEEN)')
            if status == "OK":
                ids = messages[0].split()
                for num in ids:
                    res, data = imap.fetch(num, "(RFC822)")
                    if res != 'OK':
                        continue
                    raw = data[0][1]
                    subject, frm, snippet = parse_mail(raw)
                    text = f"📩 <b>New Mail</b>\n<b>From:</b> {frm}\n<b>Subject:</b> {subject}\n\n{snippet}"
                    ok, resp = send_telegram(text)
                    if ok:
                        imap.store(num, '+FLAGS', '\\Seen')
                        print(f"Forwarded: {subject}")
                    else:
                        print(f"Telegram send failed: {resp}")
            imap.logout()
        except Exception as e:
            print("Error:", e)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    missing = [k for k in ("IMAP_SERVER","IMAP_USER","IMAP_PASSWORD","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID") if not os.getenv(k)]
    if missing:
        print("Missing env vars:", missing)
        raise SystemExit(1)
    main_loop()
