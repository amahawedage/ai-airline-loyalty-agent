import sqlite3
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "loyalty.db"
)


def test_database():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n=== DATABASE TEST ===\n")

    # Test member
    member = cursor.execute(
        """
        SELECT *
        FROM members
        WHERE member_id = ?
        """,
        ("M001",)
    ).fetchone()

    print("M001:")
    print(member)

    # Test missing miles
    transaction = cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE transaction_id = ?
        """,
        ("T002",)
    ).fetchone()

    print("\nT002:")
    print(transaction)

    # Test reward
    reward = cursor.execute(
        """
        SELECT *
        FROM rewards
        WHERE reward_id = ?
        """,
        ("R001",)
    ).fetchone()

    print("\nR001:")
    print(reward)

    # Test family
    family = cursor.execute(
        """
        SELECT *
        FROM family_accounts
        WHERE family_account_id = ?
        """,
        ("FAM001",)
    ).fetchall()

    print("\nFAM001:")
    print(family)

    # Test partner
    partner = cursor.execute(
        """
        SELECT *
        FROM partner_airlines
        WHERE partner_name = ?
        """,
        ("Partner Air",)
    ).fetchone()

    print("\nPartner Air:")
    print(partner)

    conn.close()

    print("\n=== DATABASE TEST COMPLETE ===")


if __name__ == "__main__":
    test_database()