def butter_trading_algorithm(
    current_price,
    forecast_price,
    news_sentiment,
    market_reports,
    price_changes,
    historical_prices,
    quantity,
    initial_price,
    initial_counter_offer,
    final_settle_price,
    avg_bid_steps,
    avg_counter_offer_steps,
):
    """
    Executes a trade decision based on user-specific factors like price trends, sentiment, market reports, and forecasts.

    Args:
        current_price (float): The current price of butter.
        forecast_price (float): The predicted price of butter in the next month.
        news_sentiment (float): The sentiment score from the user's news articles (0 to 1, where 1 is positive).
        market_reports (dict): A dictionary containing supply and demand data from market reports.
        price_changes (list): List of price change percentages over the last few days.
        historical_prices (list): List of historical prices over the last N days.
        quantity (int): The number of units to trade.
        initial_price (float): The initial price from previous market data.
        initial_counter_offer (float): The initial counter offer from previous market data.
        final_settle_price (float): The final settle price from previous market data.
        avg_bid_steps (int): The average number of bid steps in previous market data.
        avg_counter_offer_steps (int): The average number of counter offer steps.

    Returns:
        None
    """
    # Calculate the average price change percentage over the last N days
    avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0

    # Calculate the average historical price over the last N days
    avg_historical_price = (
        sum(historical_prices) / len(historical_prices)
        if historical_prices
        else current_price
    )

    # Calculate the initial spread between initial price and initial counter offer
    initial_spread = abs(initial_price - initial_counter_offer)

    # Calculate price movement during the market process
    price_movement = final_settle_price - initial_price

    # Define trade actions
    action = None

    # Conditions based on initial spread and price movement
    if initial_spread > 500:  # Large spread indicates market uncertainty
        print("Market is uncertain. Trading cautiously.")
        action = "Hold"
    elif price_movement > 0 and avg_bid_steps > 10:
        # Upward trend with high bid steps suggests strong buying momentum
        print("Strong buying momentum, execute buy.")
        action = "Buy"
    elif price_movement < 0 and avg_counter_offer_steps < 5:
        # Downward trend with fewer counter offers suggests selling opportunity
        print("Bearish market, execute sell.")
        action = "Sell"

    # Use forecast to determine long-term trend
    if current_price < forecast_price and news_sentiment > 0.5:
        # Buy signal: if current price is below forecast and sentiment is positive
        action = "Buy"
    elif current_price > forecast_price and news_sentiment < 0.5:
        # Sell signal: if current price is above forecast and sentiment is negative
        action = "Sell"

    # Use market reports (supply vs. demand)
    if (
        current_price > avg_historical_price
        and market_reports["supply"] < market_reports["demand"]
    ):
        action = "Buy"
    elif (
        current_price < avg_historical_price
        and market_reports["supply"] > market_reports["demand"]
    ):
        action = "Sell"

    # Incorporate price change trend
    if avg_price_change > 0.5:  # Positive price change percentage trend
        print("Price is trending up, execute buy.")
        action = "Buy"
    elif avg_price_change < -0.5:  # Negative price change percentage trend
        print("Price is trending down, execute sell.")
        action = "Sell"

    # Compare current price with forecasted price and historical average
    if current_price < forecast_price and current_price > avg_historical_price:
        print(
            "Buy signal: Price is below forecast, but higher than historical average."
        )
        action = "Buy"
    elif current_price > forecast_price and current_price < avg_historical_price:
        print("Sell signal: Price is above forecast, and below historical average.")
        action = "Sell"

    # If no trade signal is generated
    if action is None:
        print("No trade executed. Conditions not met.")
    else:
        execute_trade(action, current_price, quantity)


# Example data
current_price = 7600.0
forecast_price = 7500.0
news_sentiment = 0.7  # Positive sentiment from news
market_reports = {"supply": 100000, "demand": 120000}
price_changes = [
    1.2,
    0.5,
    -0.3,
    0.4,
    1.0,
]  # Example price change percentages over the last 5 days
historical_prices = [
    7500.0,
    7550.0,
    7580.0,
    7600.0,
    7620.0,
]  # Historical price data for the last 5 days
quantity = 100

# Mock data for previous market conditions
initial_price = 7400.0
initial_counter_offer = 7450.0
final_settle_price = 7550.0
avg_bid_steps = 12
avg_counter_offer_steps = 4

# Execute the algorithm
butter_trading_algorithm(
    current_price,
    forecast_price,
    news_sentiment,
    market_reports,
    price_changes,
    historical_prices,
    quantity,
    initial_price,
    initial_counter_offer,
    final_settle_price,
    avg_bid_steps,
    avg_counter_offer_steps,
)
