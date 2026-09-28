import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "loyalty.db"


def check_partner_airline(partner_name: str) -> dict:
    """Retrieve partner-airline eligibility and rules."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        row = connection.execute(
            """
            SELECT
                Partner_ID,
                Partner_Name,
                Eligibility,
                Earning_Rule,
                Redemption_Rule
            FROM partner_airlines
            WHERE LOWER(Partner_Name) = LOWER(?)
            """,
            (partner_name,)
        ).fetchone()

        if row is None:
            return {
                "success": False,
                "message": f"Partner airline '{partner_name}' was not found."
            }

        return {
            "success": True,
            "partner": dict(row)
        }

    finally:
        connection.close()