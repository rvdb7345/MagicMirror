import functools
import os
import base64
import json
import uvicorn
import dotenv
import requests
import pandas as pd
from openai import OpenAI
from helper_files.db_connector import DBConnector
from helper_files.file_paths import ProjectPaths
import functools
import weakref

def memoized_method(*lru_args, **lru_kwargs):
    def decorator(func):
        @functools.wraps(func)
        def wrapped_func(self, *args, **kwargs):
            # We're storing the wrapped method inside the instance. If we had
            # a strong reference to self the instance would never die.
            self_weak = weakref.ref(self)
            @functools.wraps(func)
            @functools.lru_cache(*lru_args, **lru_kwargs)
            def cached_method(*args, **kwargs):
                return func(self_weak(), *args, **kwargs)
            setattr(self, func.__name__, cached_method)
            return cached_method(*args, **kwargs)
        return wrapped_func
    return decorator
dotenv.load_dotenv()

class MarketNewsSummary:
    def __init__(self, db_connection, api_key: str):

        self.api_key = os.getenv("API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.username = ""
        self.db = db_connection
        self.project_paths = ProjectPaths()

    def _gather_market_report_ids(self):
        url = "https://news-recommendation.vespertool.com/v1/market_report_recommend"
        payload = {"user_id": self.user_id, "number": self.number, "days_threshold": self.days_threshold}
        credentials = f"{self.username}:{self.api_key}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        headers = {"Content-Type": "application/json", "Authorization": f"Basic {encoded_credentials}"}

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("recommended_articles")
            else:
                print(f"Failed to get recommendations. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
        return []

    def _gather_market_report_content_from_ids(self, ids):
        query = f"SELECT title, content FROM market_analyses WHERE id IN ({', '.join(map(str, ids))})"
        return self.db.query_data(query)

    def _gather_news_ids(self):
        url = "https://news-recommendation.vespertool.com/v1/news_recommend"
        payload = {"user_id": self.user_id, "number": self.number, "days_threshold": self.days_threshold}
        credentials = f"{self.username}:{self.api_key}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        headers = {"Content-Type": "application/json", "Authorization": f"Basic {encoded_credentials}"}

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("recommended_articles")
            else:
                print(f"Failed to get recommendations. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
        return []

    def _gather_news_content_from_ids(self, ids):
        query = f"SELECT title, content FROM news WHERE id IN ({', '.join(map(str, ids))})"
        return self.db.query_data(query)

    def _generate_highlights_summary(self, market_reports_df: pd.DataFrame, news_articles_df: pd.DataFrame) -> list:
        """
        Generates a summary in JSON format where each item is a dictionary containing title, content, 
        and a possible market effect indicator (emoji).
        """
        combined_df = pd.concat([market_reports_df, news_articles_df], ignore_index=True)

        # Prepare the content to be passed to ChatGPT
        combined_text = "\n\n".join([f"Title: {row['title']}\nContent: {row['content']}" for _, row in combined_df.iterrows()])
        
        prompt = f"""
        You are an assistant that summarizes market and news reports related to the dairy market. 
        Summarize the following articles into a JSON list. Each item in the JSON should contain the following fields:
        
        - "title": The title of the article.
        - "content": The content of the article.
        - "market_effect": An emoji that represents the potential market effect (upward 📈, downward 📉, or neutral 🟢). 
        If the content suggests an increase in prices, use 📈; if it suggests a decrease, use 📉; otherwise, use 🟢.

        Do not return HTML or bullet points. The output should be a JSON array where each object represents an article in the format:
        
        [
            {{
                "title": "Title of the article",
                "content": "Content of the article",
                "market_effect": "📈"
            }},
            ...
        ]
        
        Here is the content of the articles:
        {combined_text}
        """

        # Call OpenAI's API to generate the summary in the correct format
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": combined_text}],
            temperature=1,
            max_tokens=2000,
            top_p=1
        )
        
        print(response.choices[0].message.content.strip())
        
        # Parse the response as JSON and return
        try:
            summary_json = json.loads(response.choices[0].message.content.strip())
            return summary_json
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []

    @memoized_method()
    def generate_summary(self, user_id, number, days_threshold):
        
        self.user_id = user_id
        self.number = number
        self.days_threshold = days_threshold
        
        # Gather market reports and news
        market_report_ids = self._gather_market_report_ids()
        market_reports_df = self._gather_market_report_content_from_ids(market_report_ids)
        news_ids = self._gather_news_ids()
        news_articles_df = self._gather_news_content_from_ids(news_ids)

        # Generate and return the JSON summary
        return self._generate_highlights_summary(market_reports_df, news_articles_df)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
