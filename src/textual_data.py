"""Should load and process the personal news and market reports"""
import base64
import json
import os

import dotenv
import requests

from helper_files.file_paths import ProjectPaths
from helper_files.db_connector import DBConnector

project_paths = ProjectPaths()


dotenv.load_dotenv(project_paths.PROJECT_DIR.joinpath(".env"))
API_KEY = os.getenv("API_KEY")
username = ""



def gather_market_report_ids(user_id, number, days_threshold):
    # Define the API endpoint
    url = "https://news-recommendation.vespertool.com/v1/market_report_recommend"

    # Define the user ID and number of recommendations
    payload = {"user_id": user_id, "number": number, "days_threshold": days_threshold}  # Optional parameter
        
    # Encode the API key for Basic Auth
    credentials = f"{username}:{API_KEY}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {"Content-Type": "application/json", "Authorization": f"Basic {encoded_credentials}"}

    try:
        # Make the API call
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            print(data)
            print("Recommended Articles:", data.get("recommended_articles"))
            print("Recommendation type:", data.get("recommendation_type"))
        else:
            print(f"Failed to get recommendations. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        
    return data.get("recommended_articles")

def gather_market_report_content_from_ids(ids):
    db = DBConnector(connection_name='env')
    
    mr_content = db.query_data(
        f"""
        SELECT title, content FROM market_analyses WHERE id IN ({", ".join([str(mr_id) for mr_id in ids])})
        """
    )
    
    return mr_content


def gather_news_ids(user_id, number, days_threshold):
    # Define the API endpoint
    url = "https://news-recommendation.vespertool.com/v1/news_recommend"

    # Define the user ID and number of recommendations
    payload = {"user_id": user_id, "number": number, "days_threshold": days_threshold}  # Optional parameter
        
    # Encode the API key for Basic Auth
    credentials = f"{username}:{API_KEY}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    headers = {"Content-Type": "application/json", "Authorization": f"Basic {encoded_credentials}"}

    try:
        # Make the API call
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            print(data)
            print("Recommended Articles:", data.get("recommended_articles"))
            print("Recommendation type:", data.get("recommendation_type"))
        else:
            print(f"Failed to get recommendations. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        
    return data.get("recommended_articles")

def gather_news_content_from_ids(ids):
    db = DBConnector(connection_name='env')
    
    mr_content = db.query_data(
        f"""
        SELECT title, content FROM news WHERE id IN ({", ".join([str(mr_id) for mr_id in ids])})
        """
    )
    
    return mr_content

if __name__ == "__main__":
    user_id = 2831
    number = 5
    days_threshold = 7
    mr_ids = gather_market_report_ids(user_id, number, days_threshold)
    mr_content = gather_market_report_content_from_ids(mr_ids)
    
    print(mr_content)
    
    news_ids = gather_news_ids(user_id, number, days_threshold)
    news_content = gather_news_content_from_ids(news_ids)
    
    print(news_content)