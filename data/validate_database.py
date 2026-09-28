import sqlite3
from pathlib import Path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "loyalty.db"


REQUIRED_TABLES = {
    "members",
    "transactions",
    "rewards",
    "family_accounts",
    "partner_airlines"
}


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------

def check(condition, message):

    if condition:
        print(f"[PASS] {message}")
        return True

    print(f"[FAIL] {message}")
    return False


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_database():

    print("=" * 60)
    print("AIRLINE LOYALTY SYNTHETIC DATABASE VALIDATION")
    print("=" * 60)
    print()

    if not DB_PATH.exists():

        print("[FAIL] Database file does not exist.")
        print(f"Expected: {DB_PATH}")
        return False

    print(f"Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    all_passed = True

    # -----------------------------------------------------
    # Check tables
    # -----------------------------------------------------

    tables = {
        row[0]
        for row in cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()
    }

    missing_tables = REQUIRED_TABLES - tables

    all_passed &= check(
        not missing_tables,
        "All required tables exist"
    )

    if missing_tables:
        print(
            f"Missing tables: {sorted(missing_tables)}"
        )

    # -----------------------------------------------------
    # Check record counts
    # -----------------------------------------------------

    expected_counts = {
        "members": 5,
        "transactions": 5,
        "rewards": 4,
        "family_accounts": 4,
        "partner_airlines": 2
    }

    for table, expected in expected_counts.items():

        count = cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        all_passed &= check(
            count == expected,
            f"{table}: expected {expected}, found {count}"
        )

    # -----------------------------------------------------
    # Check duplicate member IDs
    # -----------------------------------------------------

    duplicates = cursor.execute("""
        SELECT member_id, COUNT(*)
        FROM members
        GROUP BY member_id
        HAVING COUNT(*) > 1
    """).fetchall()

    all_passed &= check(
        len(duplicates) == 0,
        "No duplicate member IDs"
    )

    # -----------------------------------------------------
    # Check duplicate transaction IDs
    # -----------------------------------------------------

    duplicates = cursor.execute("""
        SELECT transaction_id, COUNT(*)
        FROM transactions
        GROUP BY transaction_id
        HAVING COUNT(*) > 1
    """).fetchall()

    all_passed &= check(
        len(duplicates) == 0,
        "No duplicate transaction IDs"
    )

    # -----------------------------------------------------
    # Check NULL values in mandatory member fields
    # -----------------------------------------------------

    null_members = cursor.execute("""
        SELECT COUNT(*)
        FROM members
        WHERE member_id IS NULL
           OR membership_tier IS NULL
           OR miles_balance IS NULL
           OR tier_miles IS NULL
           OR join_date IS NULL
           OR status IS NULL
    """).fetchone()[0]

    all_passed &= check(
        null_members == 0,
        "No NULL values in mandatory member fields"
    )

    # -----------------------------------------------------
    # Check invalid miles
    # -----------------------------------------------------

    invalid_miles = cursor.execute("""
        SELECT COUNT(*)
        FROM members
        WHERE miles_balance < 0
           OR tier_miles < 0
    """).fetchone()[0]

    all_passed &= check(
        invalid_miles == 0,
        "No negative member mileage values"
    )

    # -----------------------------------------------------
    # Check invalid transaction mileage
    # -----------------------------------------------------

    invalid_transaction_miles = cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE miles_earned < 0
    """).fetchone()[0]

    all_passed &= check(
        invalid_transaction_miles == 0,
        "No negative transaction mileage values"
    )

    # -----------------------------------------------------
    # Check valid transaction statuses
    # -----------------------------------------------------

    valid_statuses = {
        "Credited",
        "Missing",
        "Pending"
    }

    statuses = {
        row[0]
        for row in cursor.execute(
            """
            SELECT DISTINCT transaction_status
            FROM transactions
            """
        ).fetchall()
    }

    invalid_statuses = statuses - valid_statuses

    all_passed &= check(
        not invalid_statuses,
        "All transaction statuses are valid"
    )

    # -----------------------------------------------------
    # Check member references
    # -----------------------------------------------------

    orphan_transactions = cursor.execute("""
        SELECT COUNT(*)
        FROM transactions t
        LEFT JOIN members m
            ON t.member_id = m.member_id
        WHERE m.member_id IS NULL
    """).fetchone()[0]

    all_passed &= check(
        orphan_transactions == 0,
        "All transactions reference valid members"
    )

    # -----------------------------------------------------
    # Check family-account references
    # -----------------------------------------------------

    orphan_family_members = cursor.execute("""
        SELECT COUNT(*)
        FROM family_accounts f
        LEFT JOIN members m
            ON f.member_id = m.member_id
        WHERE m.member_id IS NULL
    """).fetchone()[0]

    all_passed &= check(
        orphan_family_members == 0,
        "All family-account members are valid"
    )

    # -----------------------------------------------------
    # Check reward miles
    # -----------------------------------------------------

    invalid_rewards = cursor.execute("""
        SELECT COUNT(*)
        FROM rewards
        WHERE miles_required <= 0
    """).fetchone()[0]

    all_passed &= check(
        invalid_rewards == 0,
        "All reward mileage requirements are valid"
    )

    conn.close()

    # -----------------------------------------------------
    # Final result
    # -----------------------------------------------------

    print()
    print("=" * 60)

    if all_passed:

        print("VALIDATION RESULT: PASSED")

    else:

        print("VALIDATION RESULT: FAILED")

    print("=" * 60)

    return all_passed


if __name__ == "__main__":

    success = validate_database()

    if not success:
        raise SystemExit(1)