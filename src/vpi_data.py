import pandas as pd
from helper_files.db_connector import DBConnector

db_connection = DBConnector(connection_name="production")


def get_latest_vesper_data(db_connection, product_id, data_source_id):
    """
    Queries the vesper_quotations table for the latest entry based on product_id and data_source_id.

    Args:
        db_connection: The database connection object to execute queries.
        product_id (int): The product ID to filter on.
        data_source_id (int): The data source ID to filter on.

    Returns:
        dict: A dictionary containing the latest value, price, currency, and data_series_id.
    """
    try:
        query = f"""
        SELECT price, currency, data_series_id, date
        FROM vesper_quotations
        WHERE product_id = {product_id} AND data_source_id = {data_source_id}
        ORDER BY date DESC
        LIMIT 1
        """
        result = db_connection.query_data(query=query)

        # If the result is not empty, return the first row as a dictionary
        if not result.empty:
            latest_entry = result.iloc[0]
            return {
                "price": float(latest_entry["price"]),  # Convert np.float64 to float
                "currency": str(latest_entry["currency"]),  # Ensure it's a string
                "data_series_id": int(
                    latest_entry["data_series_id"]
                ),  # Convert np.int64 to int
                "date": latest_entry["date"].strftime(
                    "%Y-%m-%d"
                ),  # Format datetime.date as string
            }
        else:
            print("No data found for the given product_id and data_source_id.")
            return {}
    except Exception as e:
        print(f"Unexpected error while querying vesper_quotations: {e}")
        return {}


def connect_to_forecasts(db_connection, vesper_data):
    """
    Connects vesper_quotations data to the forecasts_quotations table and retrieves
    value and display_date for matching entries.

    Args:
        db_connection: The database connection object to execute queries.
        vesper_data (dict): A dictionary containing 'data_series_id' and 'date' from vesper_quotations.

    Returns:
        pd.DataFrame: A DataFrame with columns 'value' and 'display_date' for matching entries.
    """
    try:
        # Extract necessary fields from the vesper data
        data_series_id = vesper_data.get("data_series_id")
        date = vesper_data.get("date")

        if not data_series_id or not date:
            print("Vesper data is missing required fields.")
            return pd.DataFrame(columns=["value", "display_date"])

        # Query the forecasts_quotations table
        query = f"""
        SELECT value, last_value_date, display_date
        FROM forecasts_quotations
        WHERE origin_data_series_id = {data_series_id}
          AND last_value_date = '{date}'
          AND duration = 1
        """
        # Execute the query and fetch results into a DataFrame
        forecasts_data = db_connection.query_data(query=query)

        return forecasts_data
    except Exception as e:
        print(f"Unexpected error while querying forecasts_quotations: {e}")
        return pd.DataFrame(columns=["value", "display_date"])


def get_full_information(db_connection, product_id, data_source_id):
    """
    Retrieves full information by querying vesper_quotations and joining it with forecasts_quotations
    based on matching data_series_id and date.

    Args:
        db_connection: The database connection object to execute queries.
        product_id (int): The product ID to filter on.
        data_source_id (int): The data source ID to filter on.

    Returns:
        pd.DataFrame: A DataFrame with all the required information.
    """
    try:
        # Step 1: Get the latest vesper data
        vesper_data = get_latest_vesper_data(db_connection, product_id, data_source_id)

        if not vesper_data:
            print("No vesper data found.")
            return pd.DataFrame()

        # Step 2: Get the corresponding forecasts data
        forecasts_data = connect_to_forecasts(db_connection, vesper_data)

        if forecasts_data.empty:
            print("No forecasts data found for the given vesper data.")
            return pd.DataFrame()

        # Step 3: Create a DataFrame for the vesper data
        vesper_df = pd.DataFrame([vesper_data])

        # Step 4: Ensure both date columns are in the same format (convert both to datetime.date)
        vesper_df["date"] = pd.to_datetime(
            vesper_df["date"]
        ).dt.date  # Convert vesper date to datetime.date
        forecasts_data["last_value_date"] = pd.to_datetime(
            forecasts_data["last_value_date"]
        ).dt.date  # Convert forecasts date to datetime.date

        # Step 5: Merge the two DataFrames on the 'date' and 'last_value_date'
        full_info = pd.merge(
            vesper_df,
            forecasts_data,
            left_on="date",
            right_on="last_value_date",
            how="left",
        )

        # Step 6: Clean and rearrange columns (if necessary)
        full_info = full_info[
            ["price", "currency", "data_series_id", "date", "value", "display_date"]
        ]

        return full_info

    except Exception as e:
        print(f"Unexpected error: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    # Example product_id and data_source_id
    product_id = 2
    data_source_id = 52

    # Retrieve full information by combining data from both tables
    full_info = get_full_information(db_connection, product_id, data_source_id)

    if not full_info.empty:
        print("Full Information:")
        print(full_info)
