def suggest_selling_price(
    initial_price,
    initial_counter_offer,
    final_settle_price,
    avg_bid_steps,
    avg_counter_offer_steps,
    butter_price,
    price_change_percentage_last_month,
    butter_forecast_value,
):
    """
    Suggests a selling price for butter based on historical market data, current butter price,
    price change percentage, forecasted butter price, but excludes the strategy factor.

    Args:
        initial_price (float): The initial price of butter in the market.
        initial_counter_offer (float): The initial counter offer from the market.
        final_settle_price (float): The final price at which the market settled.
        avg_bid_steps (int): The average number of bid steps in the market.
        avg_counter_offer_steps (int): The average number of counter offer steps in the market.
        butter_price (float): The current market price of butter.
        price_change_percentage_last_month (float): The price change percentage for the last month.
        butter_forecast_value (float): The forecasted price of butter for the next month.

    Returns:
        float: Suggested selling price.
    """

    # Base calculation based on historical market data (price range)
    price_range = final_settle_price - initial_price
    avg_price_step = (avg_bid_steps + avg_counter_offer_steps) / 2

    # Suggest the selling price by adjusting the final deal price
    suggested_price = final_settle_price + (price_range * avg_price_step)

    # Ensure the suggested price is not too far from the initial counter offer
    suggested_price = max(initial_counter_offer, suggested_price)

    # Adjust based on market trend (price change percentage last month)
    if price_change_percentage_last_month > 0:
        # Market is bullish, so we could adjust the suggested price upwards
        suggested_price += suggested_price * 0.05  # Increase price by 5%
    elif price_change_percentage_last_month < 0:
        # Market is bearish, adjust price downwards
        suggested_price -= suggested_price * 0.05  # Decrease price by 5%

    # Adjustment based on forecast: Use the midpoint between the current butter price and the forecasted value
    price_midpoint = (butter_price + butter_forecast_value) / 2
    suggested_price = min(suggested_price, price_midpoint)

    # Ensure the suggested price does not exceed the forecasted value by too much
    suggested_price = min(suggested_price, butter_forecast_value)

    return round(suggested_price, 2)
