import imaplib
import streamlit as st
import streamlit_notify as stn

from openai import OpenAI
from tool_base import Tool, AnswerDict

from .email_utils import MailDict, render_mail


#TODO: A seperate AI call to find the uids from a description and self.list_of_mails.


class MailDeletionAnswer(AnswerDict):
    answer_str: str
    list_of_mails: list[MailDict]
    marks_for_deletion: dict[str, bool]


class MailDeletionTool(Tool):

    group = "email"

    def __init__(self, model: str, openai: OpenAI) -> None:
        self.tool_dict = {
            "type": "function",
            "name": "delete_emails",
            "description": (
                "Call this function to delete specific emails from the user's inbox. "
                "Provide a list of email UIDs to delete."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "uids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "A list of email UIDs to delete from the inbox. These UIDs can be found in the list_of_mails returned by the prevcious tools."
                    }
                },
                "required": ["uids"],
                "additionalProperties": False,
            },
        }
        self._model = model
        self._openai = openai
        self.mail: imaplib.IMAP4_SSL | None = None
        self.list_of_mails: list[MailDict] | None = None

    def run_tool(self, *args: object, **kwargs: object) -> MailDeletionAnswer:
        """Display emails for deletion.

        This method returns the list of emails for display and potential deletion.

        Args:
            kwargs (dict): Keyword arguments parsed from the model's function/tool call payload. Expected keys are:
                - "uids": A list of email UIDs to delete.
        """

        # check arguments
        uids = kwargs["uids"]
        print(uids)

        assert isinstance(uids, list) and all(isinstance(uid, str) for uid in uids)

        mails_to_delete = [mail for mail in self.list_of_mails if mail["uid"] in uids]
        return {
            "answer_str": "Marked the following mails for deletion:",
            "list_of_mails": mails_to_delete,
            "marks_for_deletion": dict.fromkeys(uids, True)
        }
    
    def render_answer(self, answer: MailDeletionAnswer) -> None:
        st.markdown(answer["answer_str"])
        marks_for_deletion = answer["marks_for_deletion"]
        for mail in answer["list_of_mails"]:
            checkbox_column, mail_column = st.columns([0.1, 0.9])
            with mail_column:
                render_mail(mail)
            with checkbox_column:
                marks_for_deletion[mail["uid"]] = st.checkbox("Delete", key=mail["uid"], value=True)
        st.button("Confirm Deletion", on_click=self.delete_mails, args=(marks_for_deletion,))
        
    
    def delete_mails(self, marks: dict[str, bool]) -> None:
        uids_to_delete = [uid for uid, should_delete in marks.items() if should_delete]
        for uid in uids_to_delete:
            self.mail.uid("copy", uid, "Papierkorb")
            self.mail.uid("STORE", uid, "+FLAGS", "\\Deleted")
        self.mail.expunge()