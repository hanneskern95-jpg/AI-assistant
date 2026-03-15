from chat_assistant.base_assistant import BaseAssistant
from tool_loader.loader import ToolLoader

import imaplib

import os

from dotenv import load_dotenv

from .mail_assistant_tools.email_utils import truncate_email_list


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

        self.list_of_mails = []

        # give mail object to the tools that need it
        tools_needing_email_object = ["summarize_emails", "delete_emails"]
        for tool_name in tools_needing_email_object:
            self.tools[tool_name].update_attributes(mail=self.mail, list_of_mails=self.list_of_mails)

    
    def handle_tools(self, message):
        """Emails are to long to simply add to the contex, but we still want them in the streamlithistory for the user to see.
        Thus, we return the full list of emails in this function, but go through self.history and truncate new emails, if any have been added.
        """
        new_messages_for_chat = super().handle_tools(message)
        
        if self.history[-1]["role"] == "tool":
            tool_answer = self.history[-1]["tool_answer"]
            if "list_of_mails" in tool_answer and tool_answer["list_of_mails"] is not None:
                tool_answer["list_of_mails"] = truncate_email_list(tool_answer["list_of_mails"], max_length=200)
        return new_messages_for_chat
            



    def close(self) -> None:
        self.mail.logout()
        