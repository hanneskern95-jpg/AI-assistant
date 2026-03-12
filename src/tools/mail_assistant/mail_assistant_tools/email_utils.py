from datetime import datetime, timedelta
import email
from typing import TypedDict

import streamlit as st

import email
from email.header import decode_header

from bs4 import BeautifulSoup


class MailDict(TypedDict):
    sender: str
    subject: str
    date_sent: str
    body: str


def render_mail(mail: MailDict) -> None:
    with st.expander(f"Email from {mail['sender']} - {mail['subject']}"):
        st.markdown(f"**Date Sent:** {mail['date_sent']}")
        st.markdown(f"**Body:** {mail['body']}")


def extract_text_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove junk
    for tag in soup(["script", "style", "img", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text

def decode_main_part(part):
    html_body = None
    text_body = None

    if part.get_content_disposition() == "attachment":
        return None, None

    content_type = part.get_content_type()
    payload = part.get_payload(decode=True)
    charset = part.get_content_charset() or "utf-8"

    if not payload:
        return None, None

    decoded = payload.decode(charset, errors="replace")

    if content_type == "text/html":
        html_body = decoded

    elif content_type == "text/plain":
        text_body = decoded
    
    return html_body, text_body

def get_body(msg):
    html_body = ""
    text_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            html_body_part, text_body_part = decode_main_part(part)  
            if html_body_part:
                html_body += html_body_part
            if text_body_part:
                text_body += text_body_part

    else:
        html_body, text_body = decode_main_part(msg)

    # Prefer HTML if available
    if html_body:
        return extract_text_from_html(html_body)
    if text_body:
        return text_body.strip()

    return "[No readable body]"


def decode_header_value(value):
    if value is None:
        return ""

    parts = decode_header(value)
    decoded = ""

    for part, charset in parts:
        if isinstance(part, bytes):
            decoded += part.decode(charset or "utf-8", errors="replace")
        else:
            decoded += part

    return decoded


def fetch_emails(days_from_to: list[int], mail) -> list[MailDict]:
    """Fetch the user's emails from the specified time horizon.

    This method uses the IMAP protocol to fetch the user's emails from their email server, based on the provided time horizon.

    Args:
        days_from_to (list[int]): A list of two integers specifying the time horizon for fetching emails, in the format [from, to].
    """
    date_from = (datetime.now() - timedelta(days=days_from_to[0])).strftime("%d-%b-%Y")
    date_to = (datetime.now()-timedelta(days=days_from_to[1]-1)).strftime("%d-%b-%Y")
    if mail is None:
        raise ValueError("Mail object is not initialized.")
    status, messages = mail.search(None, f'(SINCE "{date_from}" BEFORE "{date_to}")')
    email_list = []
    if status != "OK":
        raise ValueError(f"Failed to fetch emails: {status}")
    for msg_id in messages[0].split():
        status, raw_email = mail.fetch(msg_id, "(RFC822)")
        if status != "OK":
            raise ValueError(f"Failed to fetch email {msg_id}: {status}")
        msg = email.message_from_bytes(raw_email[0][1])

        sender = msg["From"]
        subject = decode_header_value(msg["Subject"])
        date_sent = decode_header_value(msg["Date"])
        body = get_body(msg)
        if len(body) > 1000:
            body = body[:1000] + "... [truncated]"
        email_list.append({
            "sender": sender,
            "subject": subject,
            "date_sent": date_sent,
            "body": body,
        })

    return email_list