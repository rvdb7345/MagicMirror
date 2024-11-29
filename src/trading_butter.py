import asyncio
import aiohttp

MARKET_DATA = [
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


class TradingBot:
    def __init__(
        self,
        suggested_price: float,
        min_price: float,
        strategy: str,
        counter_offer: float,
    ):
        """
        Initializes the trading bot with necessary parameters.

        Args:
            suggested_price (float): The initial suggested price for the butter.
            strategy (str): The trading strategy ("aggressive", "neutral", "conservative").
        """
        self.suggested_price = suggested_price
        self.min_price = min_price
        self.strategy = strategy
        self.bot_offer = suggested_price  # Start with the suggested price
        self.counter_offer = counter_offer

        # Calculate the price_step based on historical market data
        self.price_step = self.calculate_price_step(market_data=MARKET_DATA)

    def calculate_price_step(self, market_data):
        """
        Calculate a dynamic price step based on historical market data.
        """
        # Extract the historical step changes for COUNTER_OFFERs
        counter_offer_steps = [
            entry["Average Step Change for COUNTER_OFFERs"] for entry in market_data
        ]

        # Calculate the average of the counter offer step changes
        avg_counter_offer_step = sum(counter_offer_steps) / len(counter_offer_steps)

        # The price step can be directly tied to this average, possibly adjusted by strategy
        price_step = avg_counter_offer_step

        # If the strategy is aggressive, increase the step, if conservative, decrease it
        if self.strategy == "aggressive":
            price_step *= 1.5  # Increase step by 50% for aggressive strategy
        elif self.strategy == "conservative":
            price_step *= 0.5  # Decrease step by 50% for conservative strategy

        return price_step

    def make_offer(self):
        """
        Simulates the process of the bot making offers.
        The bot adjusts its offer according to the strategy and sends it to the front-end.
        """
        step_count = 0

        print(f"Bot's offer: {self.bot_offer} (Step {step_count + 1})")

        # Simulate receiving a counter offer (this will come from the buyer)
        counter_offer = self.counter_offer
        # counter_offer = 7430  # Simulating a counter offer
        print(f"Counter offer: {counter_offer}")

        # Adjust the bot's offer based on the counter offer (lower it slightly)
        # If the current offer is higher than the counter offer, lower it
        if self.bot_offer > counter_offer:
            self.bot_offer -= (
                self.price_step
            )  # Decrease offer based on calculated price step

        # Prevent the offer from going lower than the minimum price
        if self.bot_offer < self.min_price:
            self.bot_offer = self.min_price  # Cap the offer at the minimum price
            print(f"Bot's offer adjusted to minimum price: {self.bot_offer}")

        # Prevent the offer from going over the suggested price
        if self.bot_offer > self.suggested_price:
            self.bot_offer = (
                self.suggested_price
            )  # Cap the offer at the suggested price
            print(f"Bot's offer adjusted to suggested price: {self.bot_offer}")

        # Prevent price from going too high (stop if the price is too far above the suggested price)
        if (
            self.bot_offer > self.suggested_price * 1.2
        ):  # 20% higher than the original suggested price
            print("Bot's offer is too high, stopping further offers.")
            return "Bot's offer is too high, stopping further offers."

        step_count += 1
        return self.bot_offer


# Entry point
if __name__ == "__main__":
    # These values will come from the frontend
    suggested_price = 7500.0  # Example starting price (from frontend)
    strategy = "neutral"  # Example strategy (from frontend)
    min_price = 7320  # Example minimum price (from frontend)

    # Create an instance of the TradingBot class
    bot = TradingBot(
        suggested_price=suggested_price, min_price=min_price, strategy=strategy
    )

    # Run the asynchronous trade simulation
    asyncio.run(bot.make_offer())
