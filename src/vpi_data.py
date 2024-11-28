import pandas as pd
from helper_files.db_connector import DBConnector

class VesperDataProcessor:
    def __init__(self, db_connection: DBConnector):
        self.db_connection = db_connection

    def get_latest_vesper_data(self, product_id: int, data_source_id: int):
        """
        Queries the vesper_quotations table for the latest entry based on product_id and data_source_id.
        """
        try:
            query = f"""
            SELECT price, currency, data_series_id, date
            FROM vesper_quotations
            WHERE product_id = {product_id} AND data_source_id = {data_source_id}
            ORDER BY date DESC
            LIMIT 1
            """
            result = self.db_connection.query_data(query=query)

            if not result.empty:
                latest_entry = result.iloc[0]
                return {
                    "price": float(latest_entry["price"]),
                    "currency": str(latest_entry["currency"]),
                    "data_series_id": int(latest_entry["data_series_id"]),
                    "date": latest_entry["date"].strftime("%Y-%m-%d"),
                }
            else:
                print("No data found for the given product_id and data_source_id.")
                return {}
        except Exception as e:
            print(f"Unexpected error while querying vesper_quotations: {e}")
            return {}

    def connect_to_forecasts(self, vesper_data: dict):
        """
        Connects vesper_quotations data to the forecasts_quotations table and retrieves
        value and display_date for matching entries.
        """
        try:
            data_series_id = vesper_data.get("data_series_id")
            date = vesper_data.get("date")

            if not data_series_id or not date:
                print("Vesper data is missing required fields.")
                return pd.DataFrame(columns=["value", "display_date"])

            query = f"""
            SELECT value, last_value_date, display_date
            FROM forecasts_quotations
            WHERE origin_data_series_id = {data_series_id}
              AND last_value_date = '{date}'
              AND duration = 1
            """
            forecasts_data = self.db_connection.query_data(query=query)

            return forecasts_data
        except Exception as e:
            print(f"Unexpected error while querying forecasts_quotations: {e}")
            return pd.DataFrame(columns=["value", "display_date"])

    def get_full_information(self, product_id: int, data_source_id: int):
        """
        Retrieves full information by querying vesper_quotations and joining it with forecasts_quotations
        based on matching data_series_id and date.
        """
        try:
            vesper_data = self.get_latest_vesper_data(product_id, data_source_id)

            if not vesper_data:
                print("No vesper data found.")
                return pd.DataFrame()

            forecasts_data = self.connect_to_forecasts(vesper_data)

            if forecasts_data.empty:
                print("No forecasts data found for the given vesper data.")
                return pd.DataFrame()

            vesper_df = pd.DataFrame([vesper_data])
            vesper_df["date"] = pd.to_datetime(vesper_df["date"]).dt.date
            forecasts_data["last_value_date"] = pd.to_datetime(forecasts_data["last_value_date"]).dt.date

            full_info = pd.merge(
                vesper_df, forecasts_data, left_on="date", right_on="last_value_date", how="left"
            )

            full_info = full_info[["price", "currency", "data_series_id", "date", "value", "display_date"]]

            return full_info
        except Exception as e:
            print(f"Unexpected error: {e}")
            return pd.DataFrame()
