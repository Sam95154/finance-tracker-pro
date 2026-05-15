import sqlite3
import pandas as pd

DB_NAME = "finance_tracker.db"

# CREATE TABLE
def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            amount REAL,
            category TEXT,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()

# LOAD DATA
def load_data(username):

    conn = sqlite3.connect(DB_NAME)

    query = """
        SELECT amount AS Amount,
               category AS Category,
               date AS Date
        FROM expenses
        WHERE username = ?
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(username,)
    )

    conn.close()

    return df

# SAVE DATA
def save_data(df, username):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    # DELETE OLD USER DATA
    cursor.execute(
        "DELETE FROM expenses WHERE username = ?",
        (username,)
    )

    # INSERT NEW DATA
    for _, row in df.iterrows():

        cursor.execute("""
            INSERT INTO expenses (
                username,
                amount,
                category,
                date
            )
            VALUES (?, ?, ?, ?)
        """, (
            username,
            row["Amount"],
            row["Category"],
            str(row["Date"])
        ))

    conn.commit()
