"""Should load and process the market changes data"""


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


if __name__ == "__main__":
    query = """SELECT user_id, data_series_id FROM user_top_data_series"""
    df = db_connection.execute_query(query=query)
    user_id = 2831  # jasper
    data_series_ids = get_user_data_series(df, user_id)
    print(f"Data series for user {user_id}: {data_series_ids}")
