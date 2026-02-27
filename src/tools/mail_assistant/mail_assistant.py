from chat_assistant.base_assistant import BaseAssistant
from tool_loader.loader import ToolLoader

import imaplib

import os

from dotenv import load_dotenv


class MailAssistant(BaseAssistant):
    """A specialized assistant for handling email-related tasks.

    This assistant is designed to manage email interactions. It is able to summarize, search for, delete emails and send simple answers.

    Attributes:
        system_message (str): A system prompt that defines the assistant's behavior and tone when interacting with users regarding email tasks.
    """

    load_dotenv(override=True)

    def __init__(self, tool_loader: ToolLoader) -> None:
        self.system_message = """You are an AI Assistant specialized in handling email-related tasks. 
        You can help users manage their emails by summarizing, searching for specific emails, deleting emails, and sending simple answers. 
        Always be concise and clear in your responses, and ensure that you understand the user's request before taking any action.
        You are perfectly professional and prefer to not engage in small talk. Nutch the user to use your email related tools or switch back to the main assistant."""

        super().__init__(list_of_loaded_groups=["email", "sub_assistant"], tool_loader=tool_loader, system_message=self.system_message)

        self.mail = imaplib.IMAP4_SSL("imap." + os.getenv("EMAIL_DOMAIN", ""), 993)
        self.mail.login(os.getenv("EMAIL_USER", ""), os.getenv("EMAIL_PASSWORD", ""))

        # give mail object to the tools that need it
        tools_needing_email_object = ["summarize_emails"]
        for tool_name in tools_needing_email_object:
            self.tools[tool_name].update_attributes(mail=self.mail)

    
    def close(self) -> None:
        self.mail.logout()
        