import sqlite3

DB_PATH = '../db/car_reference.db'

def get_db_connection():
    """Creates and returns a new connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # So results behave like dictionaries
    return conn

def get_average_price(make, model, year):
    """
    Returns the average price and count of listings for the given make, model, and year.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT ROUND(AVG(price), 0) AS avg_price, COUNT(*) AS count
    FROM vehicle_listings
    WHERE LOWER(manufacturer) = LOWER(?) AND LOWER(model) = LOWER(?) AND year = ?
    """

    cursor.execute(query, (make, model, year))
    result = cursor.fetchone()
    conn.close()

    # Return as dictionary
    return {
        "avg_price": result["avg_price"] if result["avg_price"] else None,
        "count": result["count"]
    }