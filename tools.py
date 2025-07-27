import re
from typing import List, Dict
from thefuzz import fuzz
import pandas as pd

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