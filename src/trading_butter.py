import asyncio
import aiohttp


class TradingBot:
    def __init__(
        self,
        suggested_price: float,
        strategy: str,
    ):
        """
        Initializes the trading bot with necessary parameters.

        Args:
            suggested_price (float): The initial suggested price for the butter.
            strategy (str): The trading strategy ("aggressive", "neutral", "conservative").
        """
        self.suggested_price = suggested_price
        self.strategy = strategy
        self.bot_offer = suggested_price  # Start with the suggested price

    async def get_counter_offer_from_api(self):
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

    async def execute_trade(self):
        """
        Simulates the trading process asynchronously, where the bot makes an offer and reacts to the counter offer.
        The bot will adjust its offer based on the strategy and compare it to the counter offer.
        """
        step_count = 0

        while step_count < self.max_steps:
            print(f"Bot's offer: {self.bot_offer} (Step {step_count + 1})")

            # Wait asynchronously for the counter offer from the buyer
            counter_offer = (
                await self.get_counter_offer_from_api()
            )  # Asynchronous call to get counter offer

            print(f"Counter offer: {counter_offer}")

            # Compare the counter offer with the bot's offer
            if (
                abs(self.bot_offer - counter_offer) / self.bot_offer
                <= self.acceptance_threshold
            ):
                # If the counter offer is close enough to the bot's offer, the trade can be considered accepted
                print(
                    f"Trade accepted: {self.bot_offer} (within threshold of {self.acceptance_threshold * 100}% of counter offer)"
                )
                return "Trade accepted"

            # Adjust the bot's offer based on the strategy
            if self.strategy == "aggressive":
                self.bot_offer += self.price_step  # Increase offer in larger steps
            elif self.strategy == "neutral":
                self.bot_offer += self.price_step / 2  # Moderate increase in offer
            elif self.strategy == "conservative":
                self.bot_offer += self.price_step / 4  # Small increase in offer

            # Prevent price from going too high (stop if the price is too far above the suggested price)
            if (
                self.bot_offer > self.suggested_price * 1.2
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

    # Create an instance of the TradingBot class
    bot = TradingBot(suggested_price=suggested_price, strategy=strategy)

    # Run the asynchronous trade simulation
    asyncio.run(bot.execute_trade())
