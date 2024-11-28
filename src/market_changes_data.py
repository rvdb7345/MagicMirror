"""Should load and process the market changes data"""

import pandas as pd
from helper_files.db_connector import DBConnector

db_connection = DBConnector(connection_name="production")


def get_user_data_series(df, user_id):
    """
    Returns the data series IDs for a given user ID from a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame containing the table with 'user_id' and 'data_series_id'.
        user_id (int): The user ID to query.

    Returns:
        list: A list of data series IDs associated with the given user ID.
    """
    try:
        # Filter the rows for the specified user_id
        user_data = df[df["user_id"] == user_id]

        # Extract and return the data_series_id column as a list
        return user_data["data_series_id"].tolist()
    except KeyError as e:
        print(f"Error: Missing expected column {e} in the DataFrame.")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def get_price_details_for_data_series_last_month(db_connection, data_series_ids):
    """
    Fetches price IDs and change percentages from the price_changes table
    for the given data series IDs, filtered by the last month.

    Args:
        db_connection: The database connection object to execute queries.
        data_series_ids (list): A list of data series IDs to filter on.

    Returns:
        pd.DataFrame: A DataFrame with columns 'price_id', 'change_percentage', and 'created_at'.
    """
    if not data_series_ids:
        print("No data series IDs provided.")
        return pd.DataFrame(columns=["price_id", "change_percentage", "created_at"])

    try:
        # Calculate the start of the last month
        start_of_last_month_str = "2024-11-01"
        end_of_this_month_str = "2024-11-28"

        # Convert the list of IDs to a comma-separated string for the SQL query
        ids_str = ", ".join(map(str, data_series_ids))
        query = f"""
        SELECT price_id, change_percentage, created_at
        FROM price_changes
        WHERE data_series_id IN ({ids_str})
          AND created_at >= '{start_of_last_month_str}'
          AND created_at < '{end_of_this_month_str}'
        """
        # Execute the query and fetch results into a DataFrame
        return db_connection.query_data(query=query)
    except Exception as e:
        print(f"Unexpected error while fetching price details: {e}")
        return pd.DataFrame(columns=["price_id", "change_percentage", "created_at"])


def enrich_price_details_with_vpi(db_connection, price_details):
    """
    Enriches the price details DataFrame with additional information
    from the vesper_quotations table.

    Args:
        db_connection: The database connection object to execute queries.
        price_details (pd.DataFrame): A DataFrame containing price details with a 'price_id' column.

    Returns:
        pd.DataFrame: The enriched DataFrame with added columns from vesper_quotations.
    """
    if price_details.empty:
        print("Price details DataFrame is empty.")
        return pd.DataFrame(
            columns=price_details.columns.tolist()
            + ["product_id", "data_source_id", "date", "price", "currency"]
        )

    try:
        # Extract unique price_ids from the price_details DataFrame
        price_ids = price_details["price_id"].unique().tolist()
        ids_str = ", ".join(map(str, price_ids))

        # Query the vesper_quotations table
        query = f"""
        SELECT id AS price_id, product_id, data_source_id, date, price, currency
        FROM vesper_quotations
        WHERE id IN ({ids_str})
        """
        vesper_data = db_connection.query_data(query=query)

        # Merge the vesper_quotations data with the price_details DataFrame
        enriched_data = price_details.merge(vesper_data, on="price_id", how="left")
        return enriched_data
    except Exception as e:
        print(f"Unexpected error while enriching price details: {e}")
        return price_details


if __name__ == "__main__":
    query = """SELECT user_id, data_series_id FROM user_top_data_series"""
    df = db_connection.query_data(query=query)
    user_id = 2831  # jasper
    data_series_ids = get_user_data_series(df, user_id)
    print(f"Data series for user {user_id}: {data_series_ids}")

    # Map data series IDs to price details for the last month
    price_details_df = get_price_details_for_data_series_last_month(
        db_connection, data_series_ids
    )
    print(f"Price details for user {user_id} in the last month:")
    print(price_details_df)

    # Enrich price details with vesper_quotations data
    enriched_price_details = enrich_price_details_with_vpi(
        db_connection, price_details_df
    )
    print(f"Enriched price details for user {user_id}:")
    print(enriched_price_details)
