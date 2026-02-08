"""Recipe suggestion tool using web search (Chefkoch.de).

This module provides a tool that searches Chefkoch.de for recipes
matching a user's description. It returns a small JSON array of
recipe objects and offers rendering helpers to display and pin the
recipes within the Streamlit UI.
"""

import json
import re
from typing import TypedDict, TypeGuard

from openai import OpenAI
import streamlit as st

from ai_utils import get_response_text
from tool_base import AnswerDict, Tool


class Recipe(TypedDict):
    """TypedDict describing a recipe extracted from the web.

    Fields:
        title: The recipe title.
        link: URL to the original recipe page.
        ingredients: A list of ingredient strings.
        instructions: A list of instruction steps.
        description_and_advertisment: Short paragraph selling the recipe.
    """

    title: str
    link: str
    ingredients: list[str]
    instructions: list[str]
    description_and_advertisment: str


class RecipeAnswerDict(AnswerDict):
    """AnswerDict extended with a list of recipes."""

    recipes: list[Recipe]


class RecipeSuggestTool(Tool):
    """Tool that finds and suggests recipes from Chefkoch.de.

    The tool asks the responses API (with web search enabled) to find
    three distinct recipes matching the user's description, parses the
    returned JSON, and provides rendering helpers that integrate with
    Streamlit (including pinning recipes into session state).
    """

    def __init__(self, model: str, openai: OpenAI) -> None:
        """Initialize the recipe suggestion tool.

        Args:
            model (str): Model identifier used for the responses API.
            openai (OpenAI): An initialized OpenAI client instance.

        Returns:
            None
        """
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
            },
        }
        self._system_prompt = "You are an AI assisstant searching healthy and tasty recipes on the website Chefkoch.de and suggesting them to the user. Always aim to present high rated recipes."
        self._model = model
        self._openai = openai

    def create_answer(self, suggested_recipes: list[Recipe]) -> RecipeAnswerDict:
        """Create a human-readable summary and package recipes for the UI.

        Args:
            suggested_recipes (list[Recipe]): Parsed recipe objects.

        Returns:
            RecipeAnswerDict: A dict containing ``answer_str`` for display
            and the original list of recipes under ``recipes``.
        """
        answer = ""
        for index, recipe in enumerate(suggested_recipes):
            answer += f"Recipe {index + 1}: {recipe['title']} \n\n"
            answer += recipe["description_and_advertisment"]
            if index + 1 < len(suggested_recipes):
                answer += "\n\n"
        return {
            "answer_str": answer,
            "recipes": suggested_recipes,
        }

    def _clean_up_str(self, raw_str: str) -> str:
        """Remove surrounding code fences and trim whitespace from model output.

        The responses API may return JSON wrapped in markdown code
        fences (```json ... ```). This helper strips those fences and
        returns a clean string ready for JSON parsing.

        Args:
            raw_str (str): Raw text returned by the model.

        Returns:
            str: Cleaned string without code fences.
        """
        return re.sub(r"^```(?:json)?|```$", "", raw_str.strip(), flags=re.MULTILINE).strip()

    def _render_recipe(self, recipe: Recipe, index: int | None) -> st.delta_generator.DeltaGenerator:  # type: ignore
        """Render a single recipe into the Streamlit UI.

        The method shows title, description, ingredients, instructions,
        and a link to the original page. It returns the column used for
        action buttons so callers can attach a pin button.

        Args:
            recipe (Recipe): The recipe to render.
            index (int | None): Optional index used for labeling.

        Returns:
            st.delta_generator.DeltaGenerator: The column container for buttons.
        """
        st.markdown(f"### Rezept {'' + str(index + 1) if index else ''}: {recipe['title']}")
        st.markdown(recipe["description_and_advertisment"])
        with st.expander("Zutaten", expanded=False):
            for ingredient in recipe["ingredients"]:
                st.markdown(f"- {ingredient}")
        with st.expander("Anleitung", expanded=False):
            for index, instruction in enumerate(recipe["instructions"]):
                st.markdown(f"**Step {index + 1}:**")
                st.markdown(instruction)
        column_button, column_link = st.columns(2)
        with column_link:
            st.markdown(f"[View Recipe Online]({recipe['link']})")
        return column_button

    def render_answer(self, answer: AnswerDict) -> None:
        """Render the tool's answer in the Streamlit chat UI.

        If the answer contains a list of recipes they are rendered with
        pin buttons. Otherwise the textual ``answer_str`` is displayed.

        Args:
            answer (AnswerDict): The value returned by ``run_tool`` or
                ``create_answer`` containing ``answer_str`` and
                optionally ``recipes``.

        Returns:
            None
        """
        recipes = answer.get("recipes", [])

        if not isinstance(recipes, list) or len(recipes) == 0:
            st.markdown(answer.get("answer_str", "No recipes found."))
            return

        for index, recipe in enumerate(recipes):
            column_button = self._render_recipe(recipe, index)
            with column_button:
                st.button("Pin to chat", on_click=lambda rec=recipe: self.add_tabbed_object(rec), key=f"pin_recipe_{recipe['title']}_{index}")

    @staticmethod
    def is_recipe(obj: dict) -> TypeGuard[Recipe]:
        """Type guard that validates whether a dict is a Recipe.

        Args:
            obj (dict): The object to validate.

        Returns:
            TypeGuard[Recipe]: True when the object has the required keys.
        """
        required_keys = {"title", "link", "ingredients", "instructions", "description_and_advertisment"}
        return isinstance(obj, dict) and required_keys.issubset(obj.keys())

    def render_pinned_object(self, answer: dict) -> None:
        """Render a pinned recipe previously stored in session state. The answer needs to be a recipe.

        Args:
            answer (dict): Pinned recipe data. Raises an error in the
                UI if the format is invalid.

        Returns:
            None
        """

        if not self.is_recipe(answer):
            st.error("Pinned object has invalid format.")
            return
        self._render_recipe(answer, None)

    def run_tool(self, *args: object, **kwargs: object) -> RecipeAnswerDict:
        """Search the web for recipes matching the provided description.

        The tool requests three distinct recipe pages from Chefkoch.de,
        instructs the model to extract structured fields, parses the
        returned JSON, and converts it into a ``RecipeAnswerDict``.

        Args:
            description_recipe (str): Description of the desired recipes.

        Returns:
            RecipeAnswerDict: A dictionary containing ``answer_str`` and
            the parsed ``recipes`` list. If parsing fails an error-like
            result with an empty recipes list is returned.
        """

        # check arguments
        description_recipe = kwargs["description_recipe"]
        assert isinstance(description_recipe, str)

        response = self._openai.responses.create(
            model=self._model,  # Or "gpt-5.1" if you prefer
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
                        "  'instructions': [string,...],\n"
                        "   'description_and_advertisment': string   // A short advertisment of the meal. It needs to contain a description of the meal and the reason, why it fits the user prompt.\n"
                        "}\n\n"
                        "The 'description_and_advertisment' field should be one concise paragraph describing the meal, explaining the match and advertising the meal to the user."
                        "Try to sell each recipe to the user."
                        "Do not include commentary. Do not include markdown. Only return valid JSON."
                    ),
                },
            ],
        )
        recipe_list_str = get_response_text(response)
        try:
            suggested_recipes = json.loads(self._clean_up_str(recipe_list_str))
        except json.decoder.JSONDecodeError:
            return {
                "answer_str": "could not convert the following string into a dictionary:\n\n" + recipe_list_str,
                "recipes": [],
            }

        return self.create_answer(suggested_recipes)
