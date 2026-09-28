import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "loyalty.db"


def get_family_account(member_id: str) -> dict:
    """Retrieve family-account information for a member."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        member = connection.execute(
            """
            SELECT Family_Account_ID
            FROM members
            WHERE Member_ID = ?
            """,
            (member_id,)
        ).fetchone()

        if member is None:
            return {
                "success": False,
                "message": f"Member {member_id} was not found."
            }

        family_id = member["Family_Account_ID"]

        if not family_id:
            return {
                "success": True,
                "member_id": member_id,
                "family_account": None,
                "message": "This member is not associated with a family account."
            }

        rows = connection.execute(
            """
            SELECT
                Family_Account_ID,
                Member_ID,
                Relationship,
                Status
            FROM family_accounts
            WHERE Family_Account_ID = ?
            """,
            (family_id,)
        ).fetchall()

        return {
            "success": True,
            "member_id": member_id,
            "family_account_id": family_id,
            "members": [dict(row) for row in rows]
        }

    finally:
        connection.close()