import os
import pandas as pd
import glob
import re
from pydantic_ai import Agent
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.google import GoogleModel
from typing import List, Dict
from kaggle.api.kaggle_api_extended import KaggleApi
from thefuzz import fuzz

# Initialize model
provider = GoogleProvider(api_key='AIzaSyB8N6cic96yyVx3UAlLt6tvZQTYAjNNlWc')
model = GoogleModel(model_name='gemini-1.5-flash', provider=provider)

# Kaggle API setup
os.environ['KAGGLE_USERNAME'] = 'tonistephens'
os.environ['KAGGLE_KEY'] = 'ec773fac0d98675bbadcf98e6365d0d3'
kaggle_api = KaggleApi()
kaggle_api.authenticate()

# Dataset setup
dataset_dir = 'data'
dataset_name = 'utsavdey1410/food-nutrition-dataset'
dl_flag = os.path.exists(f'{dataset_dir}/FINAL FOOD DATASET')

if not dl_flag:
    os.makedirs(dataset_dir, exist_ok=True)
    kaggle_api.dataset_download_files(dataset_name, path=dataset_dir, unzip=True)

csv_files = sorted(glob.glob(f"{dataset_dir}/FINAL FOOD DATASET/FOOD-DATA-GROUP*.csv"))
df_list = [pd.read_csv(file) for file in csv_files]
df = pd.concat(df_list, ignore_index=True)

SET_TOKEN = 80

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
    
kb = KnowledgeBase(df)

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
    system_prompt=PROMPT
)

async def chat():
    print("Hello! How can I help you?")

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
