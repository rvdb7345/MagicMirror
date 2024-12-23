"""The api endpoints that can be used to retrieve data"""

import asyncio
import json
from typing import List
import dotenv
from fastapi import FastAPI
import os
from pydantic import BaseModel
import uvicorn

from helper_files.db_connector import DBConnector
from market_changes_data import MarketChangesProcessor
from suggest_price import PriceSuggestion
from textual_data import MarketNewsSummary
from vpi_data import VesperDataProcessor
from fastapi.middleware.cors import CORSMiddleware
from trading_butter import TradingBot

app = FastAPI()

origins = ["http://localhost:3000", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the VesperDataProcessor with a DB connection
db_connection = DBConnector(connection_name="env")
vesper_processor = VesperDataProcessor(db_connection=db_connection)
# vp_data = vesper_processor.get_full_information(product_id=2, data_source_id=52)
# market_changes_processor = MarketChangesProcessor(db_connection=db_connection)

# # Retrieve the most recent market changes info using the class
# market_changes_info = market_changes_processor.get_full_market_changes_info(2831)

market_news = MarketNewsSummary(db_connection, os.getenv("OPENAI_API_KEY"))


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/generate-summary")
def generate_summary(user_id: int, number: int, days_threshold: int):
    # Initialize the MarketNewsSummary class

    # Generate the HTML summary
    html_summary = market_news.generate_summary(user_id, number, days_threshold)

    # Return the summary
    return {"html_summary": html_summary}


@app.get("/get-butter-vpi-information")
def get_full_information(product_id: int, data_source_id: int):
    """
    FastAPI endpoint that retrieves full information by calling the `VesperDataProcessor`.
    """
    # Use the class to get the full information
    full_info = vesper_processor.get_full_information(product_id, data_source_id)

    # If the returned DataFrame is empty, return an error message
    if full_info.empty:
        return {"error": "No data found for the given product_id and data_source_id."}

    # Convert DataFrame to a list of dictionaries for API response
    return full_info.to_dict(orient="records")


@app.get("/get-market-changes")
def get_market_changes(user_id: int):
    """
    FastAPI endpoint to retrieve most recent market changes data for a user.
    """
    market_changes_processor = MarketChangesProcessor(db_connection=db_connection)

    # Retrieve the most recent market changes info using the class
    market_changes_info = market_changes_processor.get_full_market_changes_info(user_id)

    if not market_changes_info:
        return {"error": "No market changes found for the given user."}

    return market_changes_info


@app.get("/suggest-price")
def suggest_price():
    """
    FastAPI endpoint to retrieve most recent market changes data for a user.
    """
    price_suggester = PriceSuggestion(
        median_listing_price=7400,
        median_first_counter_bid=7350,
        average_deal_price=7420,
        avg_step_change_counter_offers=2.5,
        avg_step_change_counter_bids=4,
        butter_price=7600,
        butter_forecast_value=7498.04,
    )
    suggested_price = price_suggester.suggest_selling_price()

    return {"suggested_price": suggested_price}


@app.get("/get-bot-offer")
def get_bot_offer(
    price: float, min_price: float, strategy: str, counter_bid_price: float
):
    """
    FastAPI endpoint to retrieve most recent market changes data for a user.
    """
    bot = TradingBot(
        suggested_price=price,
        min_price=min_price,
        strategy=strategy,
        counter_offer=counter_bid_price,
    )
    bot_offer = bot.make_offer()

    return {"bot_offer": bot_offer}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
