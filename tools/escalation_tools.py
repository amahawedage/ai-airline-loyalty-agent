import json
import os
from datetime import datetime


LOG_DIR = "logs"
ESCALATION_FILE = os.path.join(
    LOG_DIR,
    "escalations.jsonl"
)


def create_human_escalation(
    scenario: str,
    member_id: str,
    reason: str,
    query: str
):

    # --------------------------------------------------------
    # Create logs directory if it does not exist
    # --------------------------------------------------------

    os.makedirs(
        LOG_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Generate escalation ID
    # --------------------------------------------------------

    existing_count = 0

    if os.path.exists(ESCALATION_FILE):

        with open(
            ESCALATION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            existing_count = sum(
                1 for line in file
                if line.strip()
            )

    escalation_number = existing_count + 1

    escalation_id = (
        f"ESC-{escalation_number:04d}"
    )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    # --------------------------------------------------------
    # Create escalation record
    # --------------------------------------------------------

    escalation_record = {
        "escalation_id": escalation_id,
        "timestamp": timestamp,
        "scenario": scenario,
        "member_id": member_id,
        "reason": reason,
        "user_query": query,
        "status": "Pending Human Review",
    }

    # --------------------------------------------------------
    # Save JSON Lines record
    # --------------------------------------------------------

    with open(
        ESCALATION_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(
                escalation_record
            )
            + "\n"
        )

    # --------------------------------------------------------
    # Return result to agent
    # --------------------------------------------------------

    return {
        "success": True,
        "escalation_id": escalation_id,
        "status": "Pending Human Review",
        "timestamp": timestamp,
        "scenario": scenario,
        "member_id": member_id,
        "reason": reason,
        "message": (
            "A prototype human-escalation record "
            "has been created for review."
        ),
    }