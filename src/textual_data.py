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

dotenv.load_dotenv()

class MarketNewsSummary:
    def __init__(self, db_connection, user_id: int, number: int, days_threshold: int, api_key: str):
        self.user_id = user_id
        self.number = number
        self.days_threshold = days_threshold
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

    def _generate_highlights_summary(self, market_reports_df: pd.DataFrame, news_articles_df: pd.DataFrame) -> str:
        combined_df = pd.concat([market_reports_df, news_articles_df], ignore_index=True)
        combined_text = "\n\n".join([f"Title: {row['title']}\nContent: {row['content']}" for _, row in combined_df.iterrows()])
        prompt = f"""
        Provide a diverse summary of the following news and market events that happened during the last week. 
        Highlight key points from the market reports, and also give an overview of the major news topics.
        Stick to approximately 5 bullet points. Focus on the dairy market. It should be suitable for a short presentation.
        Put upward graph emojis in front of news that would push the price up, and downward graph emojis in front of news that would push the price down.
        And a neutral emoji in front of news that would not have a significant impact on the price.
        Format the response in HTML, using headings and bullet points where appropriate for clarity.
        {combined_text}
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": combined_text}],
            temperature=1,
            max_tokens=1024,
            top_p=1
        )
        html_content = response.choices[0].message.content.strip()
        return html_content

    def generate_summary(self):
        market_report_ids = self._gather_market_report_ids()
        market_reports_df = self._gather_market_report_content_from_ids(market_report_ids)
        news_ids = self._gather_news_ids()
        news_articles_df = self._gather_news_content_from_ids(news_ids)

        return self._generate_highlights_summary(market_reports_df, news_articles_df)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
