import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "loyalty.db"


def get_member_details(member_id: str) -> dict:
    """Retrieve loyalty member details from the synthetic SQLite database."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.execute(
            """
            SELECT
                Member_ID,
                Membership_Tier,
                Miles_Balance,
                Tier_Miles,
                Join_Date,
                Status,
                Family_Account_ID
            FROM members
            WHERE Member_ID = ?
            """,
            (member_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return {
                "success": False,
                "message": f"Member {member_id} was not found."
            }

        return {
            "success": True,
            "member": dict(row)
        }

    finally:
        connection.close()