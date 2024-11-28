import pandas as pd
from helper_files.db_connector import DBConnector
import json

class MarketChangesProcessor:
    def __init__(self, db_connection: DBConnector):
        self.db_connection = db_connection

    def get_user_data_series(self, df, user_id: int):
        """
        Returns the data series IDs for a given user ID from a DataFrame.
        """
        try:
            # Filter the rows for the specified user_id
            user_data = df[df["user_id"] == user_id]
            return user_data["data_series_id"].tolist()
        except KeyError as e:
            print(f"Error: Missing expected column {e} in the DataFrame.")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    def get_price_details_for_data_series_last_month(self, data_series_ids):
        """
        Fetches price IDs and change percentages from the price_changes table
        for the given data series IDs, filtered by the last month.
        """
        if not data_series_ids:
            print("No data series IDs provided.")
            return pd.DataFrame(columns=["price_id", "change_percentage", "created_at", "product_id", "date", "price", "currency"])

        try:
            start_of_last_month_str = "2024-11-01"
            end_of_this_month_str = "2024-11-28"
            ids_str = ", ".join(map(str, data_series_ids))
            query = f"""
            SELECT price_id, change_percentage, created_at
            FROM price_changes
            WHERE data_series_id IN ({ids_str})
              AND created_at >= '{start_of_last_month_str}'
              AND created_at < '{end_of_this_month_str}'
            """
            return self.db_connection.query_data(query=query)
        except Exception as e:
            print(f"Unexpected error while fetching price details: {e}")
            return pd.DataFrame(columns=["price_id", "change_percentage", "created_at", "product_id", "date", "price", "currency"])

    def enrich_price_details_with_vpi(self, price_details):
        """
        Enriches the price details DataFrame with additional information
        from the vesper_quotations table.
        """
        if price_details.empty:
            print("Price details DataFrame is empty.")
            return pd.DataFrame(
                columns=price_details.columns.tolist() + ["product_id", "data_source_id", "date", "price", "currency"]
            )

        try:
            price_ids = price_details["price_id"].unique().tolist()
            ids_str = ", ".join(map(str, price_ids))

            query = f"""
            SELECT id AS price_id, product_id, data_source_id, date, price, currency
            FROM vesper_quotations
            WHERE id IN ({ids_str})
            """
            vesper_data = self.db_connection.query_data(query=query)

            enriched_data = price_details.merge(vesper_data, on="price_id", how="left")
            return enriched_data
        except Exception as e:
            print(f"Unexpected error while enriching price details: {e}")
            return price_details

    def get_full_market_changes_info(self, user_id: int):
        """
        Retrieves the most recent market change information for a given user and returns it in JSON format.
        """
        try:
            # Query the user_top_data_series table to get the user's data series
            query = "SELECT user_id, data_series_id FROM user_top_data_series"
            df = self.db_connection.query_data(query=query)

            # Get data series IDs for the given user_id
            data_series_ids = self.get_user_data_series(df, user_id)
            print(f"Data series for user {user_id}: {data_series_ids}")

            if not data_series_ids:
                print(f"No data series found for user {user_id}.")
                return []

            # Fetch price details for the last month
            price_details_df = self.get_price_details_for_data_series_last_month(data_series_ids)
            print(f"Price details for user {user_id} in the last month:")
            print(price_details_df)

            # Enrich the price details with additional data from vesper_quotations
            enriched_price_details = self.enrich_price_details_with_vpi(price_details_df)
            print(f"Enriched price details for user {user_id}:")
            print(enriched_price_details)

            # Filter the most recent record per product_id
            recent_price_details = enriched_price_details.sort_values(by=["product_id", "created_at"], ascending=[True, False])
            most_recent_price = recent_price_details.drop_duplicates(subset="product_id", keep="first")

            # Convert the most recent price record for each product into a JSON object
            most_recent_json = [
                {
                    "product_id": row["product_id"],
                    "price": row["price"],
                    "change_percentage": row["change_percentage"],
                    "date": row["date"].strftime('%Y-%m-%d'),  # Format the date as a string
                    "currency": row["currency"]
                }
                for _, row in most_recent_price.iterrows()
            ]
            
            return most_recent_json  # Return the JSON as a formatted string
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {[]}  # Return an empty JSON array in case of an error
