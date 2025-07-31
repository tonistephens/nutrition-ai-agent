import os
import pandas as pd
import re
from typing import List, Dict
from thefuzz import fuzz
import pandas as pd
from pydantic_ai import Agent
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.google import GoogleModel
from kaggle.api.kaggle_api_extended import KaggleApi

GOOGLE_API_KEY = 'AIzaSyB8N6cic96yyVx3UAlLt6tvZQTYAjNNlWc'

# Initialise model
provider = GoogleProvider(api_key=GOOGLE_API_KEY)
model = GoogleModel(model_name='gemini-1.5-flash', provider=provider)

SET_TOKEN = 75

def normalise_text(text: str) -> str:
    """Lowercase and remove punctuation"""
    return re.sub(r"[^\w\s]","",text.lower())

# Initialise knowledge base
class KnowledgeBase:
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe

    def search_foods(self, query: str) -> List[Dict]:
        """Simple keyword search over food names and descriptions"""
        query_keywords = normalise_text(query)
        results = []

        for _, row in self.df.iterrows():
            description = normalise_text(str(row.get('food', '')))

            score = fuzz.token_set_ratio(query_keywords, description)
            if score >= SET_TOKEN:
                results.append((score,row.to_dict()))

        results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in results[:5]]

# Kaggle API setup
os.environ['KAGGLE_USERNAME'] = 'tonistephens'
os.environ['KAGGLE_KEY'] = 'ec773fac0d98675bbadcf98e6365d0d3'
kaggle_api = KaggleApi()
kaggle_api.authenticate()

# Dataset setup
dataset_dir = 'data'
dataset_name = 'utsavdey1410/food-nutrition-dataset'
dl_flag = os.path.exists(f'{dataset_dir}/FINAL FOOD DATASET')

# Download and unzip dataset, if not already downloaded
if not dl_flag:
    os.makedirs(dataset_dir, exist_ok=True)
    kaggle_api.dataset_download_files(dataset_name, path=dataset_dir, unzip=True)

# Combine all csv files into a single dataframe
folder_path = os.path.join(dataset_dir, 'FINAL FOOD DATASET')
all_files = os.listdir(folder_path)
csv_files = sorted([
    os.path.join(folder_path, file)
    for file in all_files
    if file.startswith("FOOD-DATA-GROUP") and file.endswith(".csv")
])
df_list = [pd.read_csv(file) for file in csv_files]
df = pd.concat(df_list, ignore_index=True)
    
kb = KnowledgeBase(df)

def macronutrient_tool(food: str) -> Dict:
    """Find macronutrients of a particular food"""
    matched_foods = kb.search_foods(food)
    if matched_foods:
        top_match = matched_foods[0]  # take the top match
        return {
            "found": True,
            "food": top_match.get("food"),
            "calories": top_match.get("Caloric Value"),
            "protein": top_match.get("Protein"),
            "fat": top_match.get("Fat"),
            "carbohydrates": top_match.get("Carbohydrates"),
        }
    return {"found": False, "message": "Food not found"}

def ingredient_tool(ingredients: str) -> Dict:
    """Generate a creative recipe using given ingredients."""
    # Normalize and match ingredients
    ingredient_list = [normalise_text(ing.strip()) for ing in ingredients.split(",")]
    matched_items = []

    for ingredient in ingredient_list:
        results = kb.search_foods(ingredient)
        if results:
            matched_items.append(results[0].get("food"))
    
    if len(matched_items) < 2:
        return {
            "found": False,
            "message": "I couldn’t find enough matching ingredients. Try adding more or check your spelling."
        }

    prompt = f"""
    Create a healthy, flavorful, and easy-to-follow recipe using the following ingredients:
    {', '.join(matched_items)}.

    Guidelines:
    - Structure it with: Ingredients list, Instructions (step-by-step), Estimated Prep & Cook Time.
    - Emphasize nutritional benefits and mood-enhancing qualities.
    - Ensure the recipe is balanced and realistic.
    """

    response = model.run(prompt)
    
    return {
        "found": True,
        "recipe": response.output.strip()
    }

# System prompt
PROMPT = """
You are a helpful nutrition and meal planning assistant,
offering personalised meal plans designed to improve user's mental and physical health through diet.

Your responsibilities:
- Understand users current mood, dietary preferences, and restrictions.
- Provide personalised meal suggestions.
- Briefly explain how specific foods or nutrients influence mood and mental health.
- Assist users with questions about nutrition, dietary guidelines, and meal planning.
- Offer practical tips for meal preparation and ingredient substitutions.
- Maintain an empathetic and encouraging tone.
- If you cannot answer a question, politely explain and suggest consulting a registered dietitian or healthcare professional.

Core policies to remember:
- Allergies and dietary restrictions are respected in all suggestions.
- Emphasise balanced nutrition and variety in meal plans.
- Provide clear, easy-to-follow meal ideas with brief explanations linking nutrition to mood improvement.

Tools usage:
- If a user asks about calories or macronutrients of a food, use macronutrient_tool to gather the required information.
- If a user wants you to create a recipe for them given the ingredients they have left in their cupboard, use ingredient_tool to handle this.

Always be patient, supportive, and informative, aiming to empower users toward healthier eating habits that positively impact their mood and lifestyle.
"""

def get_context(user_message: str) -> str:
    """Retrieve relevant nutritional information based on user query"""
    search_results = kb.search_foods(user_message)
    if not search_results:
        return "No nutritional information found for this query."
    
    context = "Relevant nutritional knowledge:\n\n"
    for food in search_results:
        context += f"Food: {food.get('food')}\n"
        context += f"Calories: {food.get('Caloric Value')}\n"
        context += f"Protein: {food.get('Protein')}\n"
        context += f"Carbohydrates: {food.get('Carbohydrates')}\n"
        context += f"Fat: {food.get('Fat')}\n"
    return context

# Create agent
agent = Agent(
    model=model,
    system_prompt=PROMPT,
    tools=[macronutrient_tool,
           ingredient_tool]
)

async def chat():
    print("Hello! How can I help you?")
    history = []

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'end chat']:
            print("Have a great day!")
            break

        nutrition_context = get_context(user_input)
        enhanced_prompt = f"User query: {user_input}\n\nNutritional Information:\n{nutrition_context}"

        result = await agent.run(enhanced_prompt)
        print(f"Agent: {result.output}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(chat())
