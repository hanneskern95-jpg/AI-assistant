from chat_assistant.base_assistant import BaseAssistant
from tool_loader.loader import ToolLoader


class MailAssistant(BaseAssistant):
    """A specialized assistant for handling email-related tasks.

    This assistant is designed to manage email interactions. It is able to summarize, search for, delete emails and send simple answers.

    Attributes:
        system_message (str): A system prompt that defines the assistant's behavior and tone when interacting with users regarding email tasks.
    """

    def __init__(self, tool_loader: ToolLoader) -> None:
        self.system_message = """You are an AI Assistant specialized in handling email-related tasks. 
        You can help users manage their emails by summarizing, searching for specific emails, deleting emails, and sending simple answers. 
        Always be concise and clear in your responses, and ensure that you understand the user's request before taking any action.
        You are perfectly professional and prefer to not engage in small talk. Nutch the user to use your email related tools or switch back to the main assistant."""

        super().__init__(list_of_loaded_groups=["email", "sub_assistant"], tool_loader=tool_loader, system_message=self.system_message)
        print(self.tools.keys())