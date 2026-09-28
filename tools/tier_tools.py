import sqlite3


DB_PATH = "data/loyalty.db"


def calculate_tier_upgrade(member_id: str):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                Member_ID,
                Membership_Tier,
                Tier_Miles,
                Status
            FROM Members
            WHERE Member_ID = ?
            """,
            (member_id,),
        )

        member = cursor.fetchone()

        if member is None:

            return {
                "success": False,
                "member_id": member_id,
                "message": "Member not found.",
            }

        current_tier = member["Membership_Tier"]
        tier_miles = member["Tier_Miles"]
        status = member["Status"]

        # Prototype tier thresholds
        silver_threshold = 25000
        gold_threshold = 50000

        # Determine current qualification based on tier miles
        if tier_miles >= gold_threshold:
            calculated_tier = "Gold"

        elif tier_miles >= silver_threshold:
            calculated_tier = "Silver"

        else:
            calculated_tier = "Blue"

        # Determine next defined tier
        if calculated_tier == "Blue":

            next_tier = "Silver"
            next_threshold = silver_threshold
            miles_required = silver_threshold - tier_miles

        elif calculated_tier == "Silver":

            next_tier = "Gold"
            next_threshold = gold_threshold
            miles_required = gold_threshold - tier_miles

        else:

            next_tier = None
            next_threshold = None
            miles_required = 0

        return {
            "success": True,
            "member_id": member_id,
            "current_membership_tier": current_tier,
            "calculated_tier_from_miles": calculated_tier,
            "tier_miles": tier_miles,
            "status": status,
            "silver_threshold": silver_threshold,
            "gold_threshold": gold_threshold,
            "next_tier": next_tier,
            "next_tier_threshold": next_threshold,
            "miles_required_for_next_tier": miles_required,
        }

    finally:

        conn.close()