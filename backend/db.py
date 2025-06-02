import os
import sqlite3

# DB_PATH = '../db/car_reference.db'


# Build absolute path to db regardless of where app is launched from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "car_reference.db")

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
    
def get_reference_listings(limit=100, make=None, model=None, year=None):
    """
    Returns a list of reference vehicle listings for preview purposes.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # build WHERE clause only for params that were provided
    where = []
    params = []
    if make:
        where.append("LOWER(manufacturer)=LOWER(?)")
        params.append(make)
    if model:
        where.append("LOWER(model)=LOWER(?)")
        params.append(model)
    if year:
        where.append("year=?")
        params.append(year)

    where_clause = "WHERE " + " AND ".join(where) if where else ""
    query = f"""
        SELECT id, manufacturer, model, year, price, odometer, created_at
        FROM vehicle_listings
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ?
    """
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_user_listings(limit=100):
    """
    Returns a list of user-submitted vehicle listings, or an empty list if the table doesn't exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM user_listings LIMIT ?", (limit,))
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        # Table might not exist yet
        rows = []
        
    conn.close()
    return [dict(row) for row in rows]