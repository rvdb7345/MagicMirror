"""Should load and process the vpi data"""

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


if __name__ == "__main__":
    # Parameters for the query
    product_id = 2
    data_source_id = 52

    # Query for the latest vesper data
    latest_data = get_latest_vesper_data(db_connection, product_id, data_source_id)
    if latest_data:
        print("Latest Vesper Quotation Data:")
        print(latest_data)
