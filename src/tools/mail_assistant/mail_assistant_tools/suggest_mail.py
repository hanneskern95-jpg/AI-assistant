import os
from dotenv import load_dotenv

import streamlit as st
import streamlit_notify as stn
from dotenv import load_dotenv
from openai import OpenAI

from tool_base import AnswerDict, Tool
from ai_utils import get_response_text_from_chatcompletion

from .email_utils import send_mail

import imaplib
import smtplib


class SuggestEmailAnswer(AnswerDict):
    answer_str: str
    receiver: str
    subject: str
    body: str


class MailSuggestionTool(Tool):

    group = "email"

    def __init__(self, model: str, openai: OpenAI) -> None:
        self.tool_dict = {
            "type": "function",
            "name": "suggest_email",
            "description": (
                "Call this function to suggest and send an email based on the provided context. "
                "The email adress to send the mail to is either in the context, or in previous tool calls. "
                "If a unique email address cannot be found, the tool will indicate that."
                "Also use this tool if the user wants to send an email or answer to one."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email_send_to": {
                        "type": "string",
                        "description": (
                            "The email address to send the email to. It might be in the user prompt "
                            "(E.g. 'Send an email to example@web.de), or it might be in the context of "
                            "previous tool calls (E.g. 'Send a mail to bender, and the last tool call "
                            "contained the email bender@math.uni-bremen.de). If the email address cannot "
                            "be found or is not unique, use an empty string. The tool will then indicate "
                            "that it could not find a unique email address to send the mail to."
                        )
                    },
                    "subject": {
                        "type": "string",
                        "description": (
                            "The subject of the email. Find it from the context. If you answer an older "
                            "email, use the subject of the original email, but add 'Re:' in front of it."
                        ),
                    },
                    "body": {
                        "type": "string",
                        "description": (
                            "The body of the email. Find it from the context. If you answer an older "
                            "email, use the content of the original email as context for the body of the "
                            "answer email."
                        ),
                    },
                },
                "required": ["email_send_to", "subject", "body"],
                "additionalProperties": False,
            },
        }

        load_dotenv(override=True)

        self._system_prompt = """You are an AI assistant that helps generate professional email subjects and bodies based on the provided context.
        Generate a concise subject and a polite, professional body for the email."""
        self._model = model
        self._openai = openai
        self.mail: imaplib.IMAP4_SSL | None = None
        self.sender_mail: smtplib.SMTP | None = None

        self.sender_adress = os.getenv("EMAIL_USER", "")

    def run_tool(self, *args: object, **kwargs: object) -> SuggestEmailAnswer:
        """Suggest and send an email based on the context.

        Args:
            kwargs (dict): Keyword arguments expected:
                - "email_send_to": The email address to send the email to.
                - "subject": The subject of the email.
                - "body": The body of the email.
        """
        email_send_to = kwargs.get("email_send_to", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")

        assert isinstance(email_send_to, str)
        assert isinstance(subject, str)
        assert isinstance(body, str)

        if not email_send_to or not email_send_to.strip():
            return {
                "answer_str": "Could not figure out a unique email address from the context.",
                "receiver": "",
                "subject": "",
                "body": "",
            }

        return {
            "answer_str": f"Ready to send email to {email_send_to}",
            "receiver": email_send_to,
            "subject": subject,
            "body": body,
        }

    def render_answer(self, answer: AnswerDict) -> None:

        st.markdown(str(answer.get("answer_str", "")))

        if answer.get("receiver"):
            col1, col2 = st.columns(2)
            with col1:
                receiver = st.text_input("To:", value=str(answer.get("receiver", "")), disabled=False)
            with col2:
                st.text_input("From:", value=str(self.sender_adress), disabled=True)

            subject = st.text_area(
                "Subject:", value=str(answer.get("subject", "")), height=50
            )
            body = st.text_area("Body:", value=str(answer.get("body", "")), height=200)

            if st.button("Send Email"):
                if self.mail is None or self.sender_mail is None:
                    st.error("Mail connections not initialized.")
                else:
                    send_mail(
                        subject=subject,
                        body=body,
                        to_email=receiver,
                        mail=self.mail,
                        sender_mail=self.sender_mail,
                    )
                    stn.toast(f"Email sent to {answer.get('receiver')}!", duration=3, icon="✅")
                    stn.notify()

