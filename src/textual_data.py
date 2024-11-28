"""Should load and process the personal news and market reports"""
import base64
import json
import os

import dotenv
import requests

from openai import OpenAI
import pandas as pd

# Set your OpenAI API key here
client = OpenAI(api_key= os.getenv("OPENAI_API_KEY"))


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




def generate_highlights_summary(market_reports_df: pd.DataFrame, news_articles_df: pd.DataFrame) -> str:
    """
    Generate a diverse summary of the week's events from market reports and news articles.
    Highlights the market reports and includes key points from news articles.
    Returns the summary in a nicely formatted HTML.

    Args:
        market_reports_df (pd.DataFrame): Dataframe containing market reports with 'title' and 'content' columns.
        news_articles_df (pd.DataFrame): Dataframe containing news articles with 'title' and 'content' columns.

    Returns:
        str: HTML-formatted summary of the week's events.
    """
    # Combine market reports and news articles into one dataset
    combined_df = pd.concat([market_reports_df, news_articles_df], ignore_index=True)

    # Combine the titles and contents of all entries into a single string for the API prompt
    combined_text = "\n\n".join(
        [f"Title: {row['title']}\nContent: {row['content']}" for _, row in combined_df.iterrows()]
    )

    # Define the prompt for summarization
    prompt = f"""
    Provide a diverse summary of the following news and market events that happened during the last week. 
    Highlight key points from the market reports, and also give an overview of the major news topics.
    Stick to approximately 5 bullet points. Focus on the dairy market. It should be suitable for a short presentation.
    Put upward graph emojis in front of news that would push the price up, and downward graph emojis in front of news that would push the price down.
    And an neutral emoji in front of news that would not have a significant impact on the price.
    Format the response in HTML, using headings and bullet points where appropriate for clarity.
    

    {combined_text}
    """

    # Make the API call to OpenAI for the summary
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "system",
        "content": prompt
        },
        {
        "role": "user",
        "content": combined_text
        }
    ],
    temperature=1,
    max_tokens=1024,
    top_p=1
    )
    # Extract the response text (HTML formatted summary)
    html_content = response.choices[0].message.content.strip()

    print(html_content)

    return html_content

if __name__ == "__main__":
    user_id = 2831
    number = 5
    days_threshold = 7
    mr_ids = gather_market_report_ids(user_id, number, days_threshold)
    market_reports_df = gather_market_report_content_from_ids(mr_ids)
    
    print(market_reports_df)
    
    news_ids = gather_news_ids(user_id, number, days_threshold)
    news_articles_df = gather_news_content_from_ids(news_ids)
    
    print(news_articles_df)
    
    # Call the function to generate the summary
    html_summary = generate_highlights_summary(market_reports_df, news_articles_df)

    # Print or use the HTML summary
    print(html_summary)

