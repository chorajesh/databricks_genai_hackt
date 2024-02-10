import sys

from heb_databricks_genai.app import hello_world
from heb_databricks_genai.ShoppingList_Full_code import openai_get_completion


def main() -> None:
    input_query = "Create me a shopping list for a super bowl event for 5 people that is under $100"
    print(openai_get_completion(input_query))


if __name__ == "__main__":
    main()
