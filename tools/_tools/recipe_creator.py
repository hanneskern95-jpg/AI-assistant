import json
from ..tool import Tool, ToolDict
import re

class RecipeSuggestTool(Tool):

    def __init__(self, model, openai):
        self.tool_dict = {
            "type": "function",
            "name": "find_recipe_online",
            "description": "Finds and suggests 3 food recipes online for the user. Can also be used to recommend food for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description_recipe": {
                        "type": "string",
                        "description": """
                                        A description of the recipes the user wants.
                                        Example 1: A savory meal using potatos and mushrooms, inspired by Indian cuisine.
                                        Example 2: Something very spicy. It must be lactose free.
                                       """,
                    },
                },
                "required": ["description"],
                "additionalProperties": False,
            }
        }
        self._system_prompt = "You are an AI assisstant searching healthy and tasty recipes on the website Chefkoch.de and suggesting them to the user. Always aim to present high rated recipes."
        self._model = model
        self._openai = openai
        self._sugested_recipes = None


    def create_answer(self):
        answer =  ""
        for index, recipe in enumerate(self._sugested_recipes):
            answer += f"Recipe {index+1}: {recipe['title']} \n\n"
            answer += recipe["description_and_advertisment"]
            if index+1 < len(self._sugested_recipes):
                answer += "\n\n"
        return {"content_str": answer}
    

    def _clean_up_str(self, raw_str: str) -> str:
        return re.sub(r"^```(?:json)?|```$", "", raw_str.strip(), flags=re.MULTILINE).strip()


    def run_tool(self, description_recipe):

        response = self._openai.responses.create(
            model=self._model,   # Or "gpt-5.1" if you prefer
            tools=[{"type": "web_search"}],  # Enable web browsing
            input=[
                {
                    "role": "user",
                    "content": (
                        "Use a web search to find exactly three different recipes on www.chefkoch.de "
                        f"that match this description: '{description_recipe}'. "
                        "Make sure that they are three different meals, not just the same meal by different users or with similar names."
                        "For each result, open the recipe page and extract its data. "
                        "Return ONLY valid JSON, structured as an array of recipe objects."
                        "Each object must have this format:\n\n"
                        "{\n"
                        "  'title': string,\n"
                        "  'link': string,\n"
                        "  'ingredients': [string, ...],\n"
                        "  'instructions': string\n"
                        "   'description_and_advertisment': string   // A short advertisment of the meal. It needs to contain a description of the meal and the reason, why it fits the user prompt.\n"
                        "}\n\n"
                        "The 'description_and_advertisment' field should be one concise paragraph describing the meal, explaining the match and advertising the meal to the user. Try to sell each recipe to the user."
                        "Do not include commentary. Do not include markdown. Only return valid JSON."
                    )
                }
            ]
        )
        recipe_list_str = response.output[1].content[0].text
        try:
            self._sugested_recipes = json.loads(self._clean_up_str(recipe_list_str))
        except json.decoder.JSONDecodeError:
            return "could not convert the following string into a dictionary:\n\n"+response.output[1].content[0].text

        return self.create_answer()
