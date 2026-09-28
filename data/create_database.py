import sqlite3
from pathlib import Path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "loyalty.db"


# ---------------------------------------------------------
# Database creation
# ---------------------------------------------------------

def create_database():

    print("Creating synthetic airline loyalty database...")
    print(f"Database location: {DB_PATH}")

    # Remove existing database so that the script creates
    # a clean reproducible database.
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # -----------------------------------------------------
    # Members
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE members (
            member_id TEXT PRIMARY KEY,
            membership_tier TEXT NOT NULL,
            miles_balance INTEGER NOT NULL,
            tier_miles INTEGER NOT NULL,
            join_date TEXT NOT NULL,
            status TEXT NOT NULL,
            family_account_id TEXT
        )
    """)

    # -----------------------------------------------------
    # Transactions
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY,
            member_id TEXT NOT NULL,
            flight_date TEXT NOT NULL,
            airline TEXT NOT NULL,
            flight_number TEXT NOT NULL,
            miles_earned INTEGER NOT NULL,
            transaction_status TEXT NOT NULL,
            credit_date TEXT,
            FOREIGN KEY (member_id)
                REFERENCES members(member_id)
        )
    """)

    # -----------------------------------------------------
    # Rewards
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE rewards (
            reward_id TEXT PRIMARY KEY,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            miles_required INTEGER NOT NULL,
            cabin TEXT NOT NULL,
            availability TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # Family accounts
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE family_accounts (
            family_account_id TEXT NOT NULL,
            member_id TEXT NOT NULL,
            relationship TEXT NOT NULL,
            status TEXT NOT NULL,
            PRIMARY KEY (
                family_account_id,
                member_id
            ),
            FOREIGN KEY (member_id)
                REFERENCES members(member_id)
        )
    """)

    # -----------------------------------------------------
    # Partner airlines
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE partner_airlines (
            partner_id TEXT PRIMARY KEY,
            partner_name TEXT NOT NULL,
            eligibility TEXT NOT NULL,
            earning_rule TEXT NOT NULL,
            redemption_rule TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # Synthetic member data
    # -----------------------------------------------------

    members = [
        (
            "M001",
            "Silver",
            42000,
            30000,
            "2021-05-12",
            "Active",
            "FAM001"
        ),
        (
            "M002",
            "Blue",
            18000,
            12000,
            "2023-02-20",
            "Active",
            "FAM002"
        ),
        (
            "M003",
            "Gold",
            85000,
            60000,
            "2019-08-15",
            "Active",
            "FAM001"
        ),
        (
            "M004",
            "Blue",
            5000,
            4000,
            "2025-01-10",
            "Active",
            None
        ),
        (
            "M005",
            "Silver",
            55000,
            35000,
            "2020-11-03",
            "Active",
            "FAM003"
        )
    ]

    cursor.executemany("""
        INSERT INTO members (
            member_id,
            membership_tier,
            miles_balance,
            tier_miles,
            join_date,
            status,
            family_account_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, members)

    # -----------------------------------------------------
    # Synthetic transaction data
    # -----------------------------------------------------

    transactions = [
        (
            "T001",
            "M001",
            "2026-08-01",
            "Synthetic Airways",
            "SA101",
            5000,
            "Credited",
            "2026-08-03"
        ),
        (
            "T002",
            "M001",
            "2026-08-15",
            "Synthetic Airways",
            "SA205",
            4500,
            "Missing",
            None
        ),
        (
            "T003",
            "M002",
            "2026-08-20",
            "Partner Air",
            "PA301",
            3500,
            "Pending",
            None
        ),
        (
            "T004",
            "M003",
            "2026-07-10",
            "Synthetic Airways",
            "SA401",
            7000,
            "Credited",
            "2026-07-12"
        ),
        (
            "T005",
            "M005",
            "2026-08-22",
            "Partner Air",
            "PA501",
            6000,
            "Missing",
            None
        )
    ]

    cursor.executemany("""
        INSERT INTO transactions (
            transaction_id,
            member_id,
            flight_date,
            airline,
            flight_number,
            miles_earned,
            transaction_status,
            credit_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    # -----------------------------------------------------
    # Synthetic reward data
    # -----------------------------------------------------

    rewards = [
        (
            "R001",
            "DXB",
            "LHR",
            45000,
            "Economy",
            "Available"
        ),
        (
            "R002",
            "DXB",
            "LHR",
            80000,
            "Business",
            "Available"
        ),
        (
            "R003",
            "DXB",
            "SIN",
            35000,
            "Economy",
            "Unavailable"
        ),
        (
            "R004",
            "DXB",
            "SYD",
            90000,
            "Economy",
            "Available"
        )
    ]

    cursor.executemany("""
        INSERT INTO rewards (
            reward_id,
            origin,
            destination,
            miles_required,
            cabin,
            availability
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, rewards)

    # -----------------------------------------------------
    # Synthetic family-account data
    # -----------------------------------------------------

    family_accounts = [
        (
            "FAM001",
            "M001",
            "Primary",
            "Active"
        ),
        (
            "FAM001",
            "M003",
            "Spouse",
            "Active"
        ),
        (
            "FAM002",
            "M002",
            "Primary",
            "Active"
        ),
        (
            "FAM003",
            "M005",
            "Primary",
            "Active"
        )
    ]

    cursor.executemany("""
        INSERT INTO family_accounts (
            family_account_id,
            member_id,
            relationship,
            status
        )
        VALUES (?, ?, ?, ?)
    """, family_accounts)

    # -----------------------------------------------------
    # Synthetic partner-airline data
    # -----------------------------------------------------

    partner_airlines = [
        (
            "P001",
            "Partner Air",
            "Eligible on qualifying flights",
            "Based on eligible fare",
            "Subject to reward availability"
        ),
        (
            "P002",
            "Global Connect",
            "Eligible for selected fares",
            "Fare-class dependent",
            "Limited redemption"
        )
    ]

    cursor.executemany("""
        INSERT INTO partner_airlines (
            partner_id,
            partner_name,
            eligibility,
            earning_rule,
            redemption_rule
        )
        VALUES (?, ?, ?, ?, ?)
    """, partner_airlines)

    # -----------------------------------------------------
    # Commit and close
    # -----------------------------------------------------

    conn.commit()
    conn.close()

    print()
    print("SUCCESS")
    print("Synthetic database created successfully.")
    print(f"Location: {DB_PATH}")


if __name__ == "__main__":
    create_database()