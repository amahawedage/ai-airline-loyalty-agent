import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "loyalty.db"


def check_reward_eligibility(
    member_id: str,
    origin: str,
    destination: str,
    cabin: str
) -> dict:
    """Check whether a member has enough miles for an available reward."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        member = connection.execute(
            """
            SELECT Miles_Balance
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

        reward = connection.execute(
            """
            SELECT
                Reward_ID,
                Origin,
                Destination,
                Miles_Required,
                Cabin,
                Availability
            FROM rewards
            WHERE Origin = ?
            AND Destination = ?
            AND Cabin = ?
            """,
            (origin, destination, cabin)
        ).fetchone()

        if reward is None:
            return {
                "success": False,
                "member_id": member_id,
                "message": "No matching reward was found."
            }

        miles_balance = member["Miles_Balance"]
        miles_required = reward["Miles_Required"]

        return {
            "success": True,
            "member_id": member_id,
            "miles_balance": miles_balance,
            "reward": dict(reward),
            "eligible": (
                miles_balance >= miles_required
                and reward["Availability"] == "Available"
            ),
            "miles_shortfall": max(
                0,
                miles_required - miles_balance
            )
        }

    finally:
        connection.close()