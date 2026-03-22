import os
import uuid
from dotenv import load_dotenv

from datetime import datetime, timedelta, timezone, UTC
import email
from typing import TypedDict
import imaplib

import streamlit as st
import streamlit_notify as stn

import email
from email.header import decode_header

import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

from bs4 import BeautifulSoup


class MailDict(TypedDict):
    uid: str
    sender: str
    subject: str
    date_sent: str
    body: str


def render_mail(mail: MailDict, sender_mail: smtplib.SMTP | None = None, mail_object: imaplib.IMAP4_SSL | None = None, answerable: bool = True) -> None:
    with st.expander(f"Email from {mail['sender']} - {mail['subject']}"):
        st.markdown(f"**Date Sent:** {mail['date_sent']}")
        st.markdown(f"**Body:** {mail['body']}")
        if answerable:
            with st.expander("Answer"):
                unique_id = uuid.uuid4().hex
                st.text_area("Your answer:", key=f"answer_{mail['uid']}_{unique_id}")
                if st.button("Send Answer", key=f"send_{mail['uid']}_{unique_id}"):
                    answer = st.session_state[f"answer_{mail['uid']}_{unique_id}"]
                    send_mail(subject=f"Re: {mail['subject']}", body=answer, to_email=mail["sender"], mail=mail_object, sender_mail=sender_mail)
                    stn.toast("Answer sent!", duration=3, icon="✅")
                    stn.notify()

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


def fetch_emails(days_from_to: list[int] | None = None, query: str | None = None, mail: imaplib.IMAP4_SSL | None = None) -> list[MailDict]:
    """Fetch the user's emails from the specified time horizon or using a custom IMAP query.

    This method uses the IMAP protocol to fetch the user's emails from their email server, based on the provided time horizon or query.

    Args:
        days_from_to (list[int] | None): A list of two integers specifying the time horizon for fetching emails, in the format [from, to]. If None, query must be provided.
        query (str | None): A custom IMAP search query. If None, days_from_to must be provided.
        mail: The IMAP mail object.
    """
    if query is not None:
        search_query = query
    elif days_from_to is not None:
        date_from = (datetime.now() - timedelta(days=days_from_to[0])).strftime("%d-%b-%Y")
        date_to = (datetime.now()-timedelta(days=days_from_to[1]-1)).strftime("%d-%b-%Y")
        search_query = f'(SINCE "{date_from}" BEFORE "{date_to}")'
    else:
        raise ValueError("Either days_from_to or query must be provided.")
    
    if mail is None:
        raise ValueError("Mail object is not initialized.")
    status, messages = mail.uid('search', None, search_query)
    email_list = []
    if status != "OK":
        raise ValueError(f"Failed to fetch emails: {status}")
    for msg_id in messages[0].split():
        status, raw_email = mail.uid('fetch', msg_id, "(RFC822)")
        if status != "OK":
            raise ValueError(f"Failed to fetch email {msg_id}: {status}")
        msg = email.message_from_bytes(raw_email[0][1])

        sender = msg["From"]
        subject = decode_header_value(msg["Subject"])
        date_sent = decode_header_value(msg["Date"])
        body = get_body(msg)
        email_list.append({
            "uid": msg_id.decode(),
            "sender": sender,
            "subject": subject,
            "date_sent": date_sent,
            "body": body,
        })

    return email_list

def truncate_email(email_dict: MailDict, max_length: int = 1000) -> MailDict:
    """Truncate the body of an email to a specified maximum length.

    This function is used to ensure that the body of an email does not exceed a certain length, which can be useful for display purposes or when processing emails with limited resources.

    Args:
        email_dict (MailDict): A dictionary representing an email, containing keys such as "sender", "subject", "date_sent", and "body".
        max_length (int): The maximum allowed length for the email body. If the body exceeds this length, it will be truncated and appended with an ellipsis.

    Returns:
        MailDict: A new MailDict with the body truncated if it exceeded the specified maximum length.
    """
    if len(email_dict["body"]) > max_length:
        new_email_dict = email_dict.copy()
        new_email_dict["body"] = new_email_dict["body"][:max_length] + "... [truncated]"
        return new_email_dict
    return email_dict

def truncate_email_list(email_list: list[MailDict], max_length: int = 1000) -> list[MailDict]:
    """Truncate the bodies of a list of emails to a specified maximum length.

    This function applies the `truncate_email` function to each email in the provided list, ensuring that the body of each email does not exceed the specified maximum length.

    Args:
        email_list (list[MailDict]): A list of MailDict objects representing emails.
        max_length (int): The maximum allowed length for the email bodies. If any body exceeds this length, it will be truncated and appended with an ellipsis.

    Returns:
        list[MailDict]: A new list of MailDict objects with the bodies truncated if they exceeded the specified maximum length.
    """
    return [truncate_email(email, max_length) for email in email_list]

def send_mail(subject: str, body: str, to_email: str, mail: imaplib.IMAP4_SSL, sender_mail) -> None:
    """Send an email using the SMTP protocol.

    This function sends an email with the specified subject and body to the given recipient email address. It uses the SMTP protocol to connect to the email server and send the email.

    Args:
        subject (str): The subject of the email.
        body (str): The body content of the email.
        to_email (str): The recipient's email address.
    """
    load_dotenv(override=True)

    #create mail
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = formataddr((os.getenv("EMAIL_NAME"), os.getenv("EMAIL_USER")))
    msg["To"] = to_email

    msg["Date"] = formatdate(localtime=True)

    msg["Message-ID"] = make_msgid()

    # Send email
    sender_mail.send_message(msg)

    #addmail to sent folder
    mail.append("Gesendet", "", imaplib.Time2Internaldate(datetime.now(UTC)), msg.as_bytes())