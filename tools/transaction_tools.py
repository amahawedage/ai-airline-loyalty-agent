import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "loyalty.db"


def check_missing_miles(member_id: str) -> dict:
    """Check missing or pending mileage transactions for a member."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.execute(
            """
            SELECT
                Transaction_ID,
                Member_ID,
                Flight_Date,
                Airline,
                Flight_Number,
                Miles_Earned,
                Transaction_Status,
                Credit_Date
            FROM transactions
            WHERE Member_ID = ?
            AND Transaction_Status IN ('Missing', 'Pending')
            """,
            (member_id,)
        )

        rows = cursor.fetchall()

        if not rows:
            return {
                "success": True,
                "member_id": member_id,
                "transactions": [],
                "message": "No missing or pending mileage transactions were found."
            }

        return {
            "success": True,
            "member_id": member_id,
            "transactions": [dict(row) for row in rows]
        }

    finally:
        connection.close()