import asyncio
import aiohttp


async def get_counter_offer_from_api():
    """
    Asynchronously gets the counter offer from an external API.
    Replace this with the actual API request you're using to receive counter offers.
    """
    # Simulating an asynchronous API request (replace with your API logic)
    async with aiohttp.ClientSession() as session:
        async with session.get("https://example.com/get_counter_offer") as response:
            counter_offer = (
                await response.json()
            )  # Assuming the counter offer comes as JSON
            return float(
                counter_offer["counter_offer"]
            )  # Extracting the counter offer price


async def execute_trade(
    suggested_price, strategy, price_step, max_steps=100, acceptance_threshold=0.02
):
    """
    Simulates the trading process asynchronously, where the bot makes an offer and reacts to the counter offer.
    The bot will adjust its offer based on the strategy and compare it to the counter offer.

    Args:
        suggested_price (float): The initial suggested price for the butter.
        strategy (str): The trading strategy ("aggressive", "neutral", "conservative").
        price_step (float): The amount by which the bot adjusts its offer each time.
        max_steps (int): The maximum number of steps the bot will take.
        acceptance_threshold (float): The threshold (percentage) at which the user might accept the counter offer.
    """
    bot_offer = suggested_price  # The initial offer is based on the suggested price
    step_count = 0

    while step_count < max_steps:
        print(f"Bot's offer: {bot_offer} (Step {step_count + 1})")

        # Wait asynchronously for the counter offer from the buyer
        counter_offer = (
            await get_counter_offer_from_api()
        )  # Asynchronous call to get counter offer

        print(f"Counter offer: {counter_offer}")

        # Check if the counter offer is close enough to the bot's offer
        # The user can decide whether to accept based on the threshold.
        if abs(bot_offer - counter_offer) <= bot_offer * acceptance_threshold:
            print(f"User can accept the counter offer of {counter_offer}.")
            # The bot will just print the result, and the user decides to accept or not.

        # Adjust the bot's offer based on the strategy
        if strategy == "aggressive":
            bot_offer += price_step  # Increase offer in larger steps
        elif strategy == "neutral":
            bot_offer += price_step / 2  # Moderate increase in offer
        elif strategy == "conservative":
            bot_offer += price_step / 4  # Small increase in offer

        # Prevent price from going too high (stop if the price is too far above the suggested price)
        if (
            bot_offer > suggested_price * 1.2
        ):  # 20% higher than the original suggested price
            print("Trade failed: Price is too high.")
            return "Trade failed"

        step_count += 1
        await asyncio.sleep(1)  # Simulate a slight delay before the next offer

    print("Trade failed: Maximum steps reached.")
    return "Trade failed"


# Entry point
if __name__ == "__main__":
    # These values will come from the frontend
    suggested_price = (
        7500.0  # Example starting price (from frontend, as calculated earlier)
    )
    strategy = "neutral"  # Example strategy (from frontend)
    price_step = 50  # Example price step (from frontend)

    # Run the asynchronous trade simulation
    asyncio.run(execute_trade(suggested_price, strategy, price_step))
