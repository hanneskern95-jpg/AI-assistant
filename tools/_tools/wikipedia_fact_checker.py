import json
import re

from openai import OpenAI

from ..tool import AnswerDict, Tool


class WikipediaFactCheckerTool(Tool):

    def __init__(self, model: str, openai: OpenAI) -> None:
        self.tool_dict = {
            "type": "function",
            "name": "check_fact_wikipedia",
            "description": (
                "Only call this function when the user explicitly requests verification or a citation from Wikipedia, "
                "or asks what Wikipedia says about a claim or topic. Do NOT call this function for ordinary factual "
                "questions the assistant can answer directly (e.g., simple math, definitions, translations, or general "
                "explanations). Triggers: user asks 'What does Wikipedia say about...', 'fact-check', 'verify with Wikipedia', "
                "'is it true that...', or explicitly requests a Wikipedia source. Non-triggers: routine knowledge queries, "
                "conversational replies, or operational instructions. When called, return ONLY the JSON described in the schema below. "
                "JSON format expected: {\n  'answer': string|null,\n  'wikipedia_link': string|null,\n  'article_answers_question': 'Yes'|'Inconclusive'|'NoArticleFound'\n}\n\n"
                "Definitions:"
                "'Yes' — the located Wikipedia article directly and conclusively answers the user's question (the article contains a clear statement or verifiable data that addresses the claim). "
                "'Inconclusive' — a relevant Wikipedia article exists but it does not directly or clearly answer the user's question; the article may be related or provide partial information."
                "'NoArticleFound' — no relevant Wikipedia article could be found for the query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The fact or question to check against Wikipedia. Example: 'What is the capital of France?'",
                    },
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        }
        self._system_prompt = "You are an AI assistant that fact-checks information using Wikipedia. Your task is to search for relevant Wikipedia articles and provide accurate answers based on them."
        self._model = model
        self._openai = openai
        self._result = None

    def _clean_up_str(self, raw_str: str) -> str:
        return re.sub(r"^```(?:json)?|```$", "", raw_str.strip(), flags=re.MULTILINE).strip()


    def _create_answer(self, answer_dict: dict) -> AnswerDict:
        if answer_dict["article_answers_question"] == "NoArticleFound":
            answer = "No relevant Wikipedia article found to answer the question."
        elif answer_dict["article_answers_question"] == "Inconclusive":
            answer = f"Found a Wikipedia article but it does not conclusively answer the question. \nClosest Answer: {answer_dict['answer']}\nLink: {answer_dict['wikipedia_link']}"
        else:
            answer = f"{answer_dict['answer']}\nSource: {answer_dict['wikipedia_link']}"
        return {"answer_str": answer}


    def run_tool(self, question: str) -> AnswerDict:
        response = self._openai.responses.create(
            model=self._model,
            tools=[{"type": "web_search"}],
            input=[
                {
                    "role": "user",
                    "content": (
                        f"Search Wikipedia to find information about: '{question}'. "
                        "Find the most relevant Wikipedia article for this question/fact. "
                        "If you find a Wikipedia article, read it and provide an answer to the question based on the article content. "
                        "Return ONLY valid JSON with this exact format:\n\n"
                        "{\n"
                        "  'answer': string,  // The answer to the question based on the Wikipedia article, or null if no article found. This should be a full sentence.\n"
                        "  'wikipedia_link': string,  // The URL link to the Wikipedia article, or null if no article found\n"
                        "  'article_answers_question': string  // One of: 'Yes' (article conclusively answers the question),"
                        "       'Inconclusive' (article exists but doesn't conclusively answer)," 
                        "       or 'NoArticleFound' (no Wikipedia article found)\n"
                        "}\n\n"
                        "Do not include commentary. Do not include markdown. Only return valid JSON."
                    ),
                },
            ],
        )
        
        result_str = response.output[1].content[0].text
        try:
            self._result = json.loads(self._clean_up_str(result_str))
        except json.decoder.JSONDecodeError:
            return json.dumps({
                "answer": None,
                "wikipedia_link": None,
                "article_answers_question": "NoArticleFound",
                "error": "Could not parse response: " + result_str,
            })

        return self._create_answer(self._result)