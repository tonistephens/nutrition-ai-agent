import os
from pydantic_ai import Agent
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from typing import Optional
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd

# https://www.kaggle.com/datasets/utsavdey1410/food-nutrition-dataset

# Initialize model
provider = GoogleProvider(api_key='AIzaSyB8N6cic96yyVx3UAlLt6tvZQTYAjNNlWc')
model = GoogleModel(model_name='gemini-1.5-flash', provider=provider)

os.environ['KAGGLE_USERNAME'] = 'tonistephens'
os.environ['KAGGLE_KEY'] = 'ec773fac0d98675bbadcf98e6365d0d3'
kaggle_api = KaggleApi()
kaggle_api.authenticate()
df = pd.read_csv('data/Food_Nutrition.csv')

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

        result = await agent.run(user_input)
        print(f"Agent: {result.output}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(chat())
