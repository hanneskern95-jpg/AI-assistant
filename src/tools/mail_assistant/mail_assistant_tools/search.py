import json
import streamlit as st
from openai import OpenAI

import imaplib
import smtplib

from tool_base import AnswerDict, Tool
from ai_utils import get_response_text_from_chatcompletion

from .email_utils import fetch_emails, MailDict, render_mail, truncate_email_list


class MailAnswer(AnswerDict):
    answer_str: str
    list_of_mails: list[MailDict] | None


class MailSearchTool(Tool):

    group = "email"

    def __init__(self, model: str, openai: OpenAI) -> None:
        self.tool_dict = {
            "type": "function",
            "name": "search_emails",
            "description": (
                "Call this function to search for emails using an IMAP query and answer questions about the searched emails or summarize them. "
                "The input is the IMAP search query."
                "If the user has a specific question about the searched emails, answer that instead of summarizing them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The IMAP search query to find emails. For example, 'FROM \"boss@example.com\"' or 'SUBJECT \"meeting\"'."
                    },
                    "question": {
                        "type": "string",
                        "description": "A specific question about the searched emails. If provided, the tool will answer this question instead of summarizing the emails."
                        "For example, 'What are the key points from these emails?'"
                        "Leave empty if you want a summary of the searched emails."
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        }
        self._system_prompt = """You are an AI assistant that helps users manage their emails by summarizing searched emails or answering specific questions about them.
        You are given a list of the user's emails from a search query, and you can either provide a summary of those emails or answer a specific question the user has about their emails. 
        Always be concise and clear in your responses."""
        self._model = model
        self._openai = openai
        self.mail: imaplib.IMAP4_SSL | None = None
        self.sender_mail: smtplib.SMTP | None = None
        self.list_of_mails: list[MailDict] = None

    def add_new_mails(self, new_mails: list[MailDict]) -> None:
        """Add new mails to the list of mails, avoiding duplicates based on the mail's UID."""
        if self.list_of_mails is None:
            self.list_of_mails = new_mails
            return
        
        existing_uids = {mail["uid"] for mail in self.list_of_mails}
        for mail in new_mails:
            if mail["uid"] not in existing_uids:
                self.list_of_mails.append(mail)

    def run_tool(self, *args: object, **kwargs: object) -> MailAnswer:
        """Search for emails using the query and summarize them or answer a specific question about them.

        This method searches the user's emails using the provided IMAP query and either summarizes them or answers a specific question about them, depending on the input.

        Args:
            kwargs (dict): Keyword arguments parsed from the model's function/tool call payload. Expected keys are:
                - "query": A string containing the IMAP search query.
                - "question": An optional string containing a specific question about the searched emails.
        """

        # check arguments
        question = kwargs.get("question", None)
        query = kwargs["query"]

        assert isinstance(question, str | None)
        assert isinstance(query, str)

        self.mail.select("inbox")
        list_of_emails = fetch_emails(query=query, mail=self.mail)
        list_of_emails_for_model = truncate_email_list(list_of_emails, max_length=2000)

        self.add_new_mails(list_of_emails)

        if question is not None and question.strip() != "":
            task = "Answer the following question about the user's searched emails, using the attached list of emails as context: " + question
        else:
            task = "Summarize the following list of searched emails for the user. Concentrate on important mails and actionable information for the user, and ignore unimportant emails."

        task_json = {
            "task": task,
            "list_of_emails": list_of_emails_for_model,
        }

        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": json.dumps(task_json)},
            ]
        response = self._openai.chat.completions.create(model=self._model, messages=messages)
        response_text = get_response_text_from_chatcompletion(response)

        return {
            "answer_str": response_text,
            "list_of_mails": list_of_emails,
        }
    
    def render_answer(self, answer: MailAnswer) -> None:
        st.markdown(answer["answer_str"])
        if answer["list_of_mails"]:
            with st.expander("Raw Emails:"):
                for mail in answer["list_of_mails"]:
                    render_mail(mail, sender_mail=self.sender_mail, mail_object=self.mail)
