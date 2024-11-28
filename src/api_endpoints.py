"""The api endpoints that can be used to retrieve data"""
from fastapi import FastAPI
import os
import uvicorn

from textual_data import MarketNewsSummary

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/generate-summary")
def generate_summary(user_id: int, number: int, days_threshold: int):
    # Initialize the MarketNewsSummary class
    market_news = MarketNewsSummary(user_id, number, days_threshold, os.getenv("OPENAI_API_KEY"))
    
    # Generate the HTML summary
    html_summary = market_news.generate_summary()
    
    # Return the summary
    return {"html_summary": html_summary}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)