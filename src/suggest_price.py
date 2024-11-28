import random


def suggest_selling_price(
    median_listing_price,
    median_first_counter_bid,
    average_deal_price,
    avg_step_change_counter_offers,
    avg_step_change_counter_bids,
    butter_price,
    price_change_percentage_last_month,
    butter_forecast_value,
):
    """
    Suggests a selling price for butter based on historical market data, current butter price,
    price change percentage, forecasted butter price, but excludes the strategy factor.

    Args:
        median_listing_price (float): The median listing price from the market.
        median_first_counter_bid (float): The median first counter bid from the market.
        average_deal_price (float): The average deal price in the market.
        avg_step_change_counter_offers (float): The average step change for counter offers.
        avg_step_change_counter_bids (float): The average step change for counter bids.
        butter_price (float): The current market price of butter.
        price_change_percentage_last_month (float): The price change percentage for the last month.
        butter_forecast_value (float): The forecasted price of butter for the next month.

    Returns:
        float: Suggested selling price.
    """

    # Calculate the price range between the median listing price and the median first counter bid
    price_range = median_listing_price - median_first_counter_bid
    avg_price_step = (avg_step_change_counter_offers + avg_step_change_counter_bids) / 2

    # Suggest the selling price by adjusting the average deal price with the calculated price range
    suggested_price = average_deal_price + (price_range * avg_price_step)

    # Ensure the suggested price is not too far from the initial counter offer
    suggested_price = max(median_first_counter_bid, suggested_price)

    # Adjust based on market trend (price change percentage last month)
    if price_change_percentage_last_month > 0:
        # Market is bullish, so we could adjust the suggested price upwards
        suggested_price += suggested_price * 0.05  # Increase price by 5%
    elif price_change_percentage_last_month < 0:
        # Market is bearish, adjust price downwards
        suggested_price -= suggested_price * 0.05  # Decrease price by 5%

    # Adjust based on the forecast (if forecast is higher, we may hold)
    if butter_forecast_value > butter_price:
        # The forecast suggests higher prices, so we may want to hold
        suggested_price = max(suggested_price, butter_price)

    # Ensure the suggested price does not exceed the forecasted value by too much
    suggested_price = min(suggested_price, butter_forecast_value)

    # Add a small random variation to simulate market dynamics
    suggested_price += random.uniform(-20, 20)

    return round(suggested_price, 2)


# Simulating with the mock data
market_data = [
    {
        "Market Date": "Nov 27, 2024",
        "Median Listing Price": 7400,
        "Median First COUNTER_BID": 7350,
        "Average Deal Price": 7420,
        "Average Step Change for COUNTER_OFFERs": 2.5,
        "Average Step Change for COUNTER_BIDs": 4.0,
    },
    {
        "Market Date": "Nov 20, 2024",
        "Median Listing Price": 7350,
        "Median First COUNTER_BID": 7300,
        "Average Deal Price": 7370,
        "Average Step Change for COUNTER_OFFERs": 2.2,
        "Average Step Change for COUNTER_BIDs": 3.8,
    },
    {
        "Market Date": "Nov 13, 2024",
        "Median Listing Price": 7340,
        "Median First COUNTER_BID": 7270,
        "Average Deal Price": 7360,
        "Average Step Change for COUNTER_OFFERs": 2.3,
        "Average Step Change for COUNTER_BIDs": 3.5,
    },
    {
        "Market Date": "Nov 6, 2024",
        "Median Listing Price": 7370,
        "Median First COUNTER_BID": 7310,
        "Average Deal Price": 7390,
        "Average Step Change for COUNTER_OFFERs": 2.7,
        "Average Step Change for COUNTER_BIDs": 4.3,
    },
    {
        "Market Date": "Oct 30, 2024",
        "Median Listing Price": 7300,
        "Median First COUNTER_BID": 7230,
        "Average Deal Price": 7350,
        "Average Step Change for COUNTER_OFFERs": 2.4,
        "Average Step Change for COUNTER_BIDs": 3.9,
    },
]

butter_price = 7500
price_change_percentage_last_month = 2.0
butter_forecast_value = 7550

# Running the function for each market data point
for data in market_data:
    suggested_price = suggest_selling_price(
        data["Median Listing Price"],
        data["Median First COUNTER_BID"],
        data["Average Deal Price"],
        data["Average Step Change for COUNTER_OFFERs"],
        data["Average Step Change for COUNTER_BIDs"],
        butter_price,
        price_change_percentage_last_month,
        butter_forecast_value,
    )
    print(f"Suggested selling price for {data['Market Date']}: {suggested_price}")
