    
import json
import streamlit as st
from openai import OpenAI

import imaplib

from tool_base import AnswerDict, Tool
from ai_utils import get_response_text_from_chatcompletion

from .email_utils import fetch_emails, MailDict, render_mail, truncate_email_list


class MailAnswer(AnswerDict):
    answer_str: str
    list_of_mails: list[MailDict] | None


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
                        "For example, [30, 0] would summarize emails from the last month."
                        "Default is [7, 0], which summarizes emails from the last week.",
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
        list_of_emails = fetch_emails(days_from_to, self.mail)
        list_of_emails_for_model = truncate_email_list(list_of_emails, max_length=2000)
        if question is not None and question.strip() != "":
            task = "Answer the following question about the user's emails, using the attached list of emails as context: " + question
        else:
            task = "Summarize the following list of emails for the user. Concentrate on important mails and actionable information for the user, and ignore unimportant emails."

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

        return{
            "answer_str": response_text,
            "list_of_mails": list_of_emails,
        }
    
    def render_answer(self, answer: MailAnswer) -> None:
        st.markdown(answer["answer_str"])
        if answer["list_of_mails"]:
            with st.expander("Raw Emails:"):
                for mail in answer["list_of_mails"]:
                    render_mail(mail)