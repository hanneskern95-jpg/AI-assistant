    
from datetime import datetime, timedelta
import json
from openai import OpenAI

import imaplib
import email
from email.header import decode_header

from tool_base import AnswerDict, Tool
from ai_utils import get_response_text_from_chatcompletion

class MailAnswer(AnswerDict):
    answer_str: str
    list_of_mails: list | None


class MailSummarizerTool(Tool):

    group = "email"

    def __init__(self, model: str, openai: OpenAI) -> None:
        self.tool_dict = {
            "type": "function",
            "name": "summarize_emails",
            "description": (
                "Call this functione to summarize the user's emails or answer questions about them. "
                "The input is the time horizon for the summary in days."
                "If the user has a specific question about their emails, answer that instead of summarizing them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days_from_to": {
                        "type": "array",
                        "items": {
                            "type": "integer"
                        },
                        "description": "The number of days to fetch emails for summarization or answering the user's question."
                        "In the format [from, to], where 'from' is how many days ago to start the summary and 'to' is how many days ago to end the summary."
                        "For example, [7, 0] would summarize emails from the last week."
                        "Default is [30, 0], which summarizes emails from the last month.",
                    },
                    "question": {
                        "type": "string",
                        "description": "A specific question about the user's emails. If provided, the tool will answer this question instead of summarizing the emails."
                        "For example, 'What emails do I have from my boss?'"
                        "Leave empty if you want a summary of the emails in the specified time horizon."
                    }
                },
                "required": ["days_from_to"],
                "additionalProperties": False,
            },
        }
        self._system_prompt = """You are an AI assistant that helps users manage their emails by summarizing them or answering specific questions about them.
        You are given a list of the user's emails from a specified time horizon, and you can either provide a summary of those emails or answer a specific question the user has about their emails. 
        Always be concise and clear in your responses."""
        self._model = model
        self._openai = openai
        self.mail: imaplib.IMAP4_SSL | None = None

    def run_tool(self, *args: object, **kwargs: object) -> MailAnswer:
        """Summarize the user's emails or answer a specific question about them.

        This method fetches the user's emails from the specified time horizon and either summarizes them or answers a specific question about them, depending on the input.

        Args:
            kwargs (dict): Keyword arguments parsed from the model's function/tool call payload. Expected keys are:
                - "days_from_to": A list of two integers specifying the time horizon for fetching emails, in the format [from, to].
                - "question": An optional string containing a specific question about the user's emails.
        """

        # check arguments
        question = kwargs.get("question", None)
        days_from_to = kwargs["days_from_to"]

        assert isinstance(question, str | None)
        assert isinstance(days_from_to, list) and len(days_from_to) == 2 and all(isinstance(x, int) for x in days_from_to)

        self.mail.select("inbox")
        list_of_emails = self.fetch_emails(days_from_to)
        if question is not None and question.strip() != "":
            task = "Answer the following question about the user's emails, using the attached list of emails as context: " + question
        else:
            task = "Summarize the following list of emails for the user. Concentrate on important mails and actionable information for the user, and ignore unimportant emails."

        task_json = {
            "task": task,
            "list_of_emails": list_of_emails,
        }

        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": json.dumps(task_json)},
            ]
        response = self._openai.chat.completions.create(model=self._model, messages=messages)
        response_text = get_response_text_from_chatcompletion(response)

        return{
            "answer_str": response_text,
            "list_of_mails": list_of_emails,
        }

    def get_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                # Skip attachments
                if part.get_content_disposition() == "attachment":
                    continue

                # Prefer plain text
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset()

                    if charset:
                        return payload.decode(charset, errors="replace")
                    else:
                        return payload.decode(errors="replace")

        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset()

            if charset:
                return payload.decode(charset, errors="replace")
            else:
                return payload.decode(errors="replace")

        return "[No readable body]"
    

    def decode_header_value(self, value):
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


    def fetch_emails(self, days_from_to: list[int]) -> list:
        """Fetch the user's emails from the specified time horizon.

        This method uses the IMAP protocol to fetch the user's emails from their email server, based on the provided time horizon.

        Args:
            days_from_to (list[int]): A list of two integers specifying the time horizon for fetching emails, in the format [from, to].
        """
        date_from = (datetime.now() - timedelta(days=days_from_to[0])).strftime("%d-%b-%Y")
        date_to = (datetime.now()-timedelta(days=days_from_to[1]-1)).strftime("%d-%b-%Y")
        if self.mail is None:
            raise ValueError("Mail object is not initialized.")
        status, messages = self.mail.search(None, f'(SINCE "{date_from}" BEFORE "{date_to}")')
        email_list = []
        if status != "OK":
            raise ValueError(f"Failed to fetch emails: {status}")
        for msg_id in messages[0].split():
            status, raw_email = self.mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                raise ValueError(f"Failed to fetch email {msg_id}: {status}")
            msg = email.message_from_bytes(raw_email[0][1])

            sender = msg["From"]
            subject = self.decode_header_value(msg["Subject"])
            date_sent = self.decode_header_value(msg["Date"])
            body = self.get_body(msg)
            if len(body) > 1000:
                body = body[:1000] + "... [truncated]"
            email_list.append({
                "sender": sender,
                "subject": subject,
                "date_sent": date_sent,
                "body": body,
            })

        return email_list