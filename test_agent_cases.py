from agent.graph import build_graph


# ============================================================
# BUILD AGENT
# ============================================================

graph = build_graph()


# ============================================================
# TEST CASES
# ============================================================

test_cases = [

    # --------------------------------------------------------
    # 1. NORMAL CASE - MISSING MILES
    # --------------------------------------------------------

    {
        "name": "Normal - Missing Miles",
        "query": (
            "My miles are missing for member M001."
        ),
    },

    # --------------------------------------------------------
    # 2. AMBIGUOUS CASE - MISSING MILES
    # --------------------------------------------------------

    {
        "name": "Ambiguous - Missing Miles",
        "query": (
            "My flight miles are missing."
        ),
    },

    # --------------------------------------------------------
    # 3. NORMAL CASE - TIER UPGRADE
    # --------------------------------------------------------

    {
        "name": "Normal - Tier Upgrade",
        "query": (
            "Can you check my tier upgrade status "
            "for member M003?"
        ),
    },

    # --------------------------------------------------------
    # 4. EXCEPTION CASE - UNKNOWN MEMBER
    # --------------------------------------------------------

    {
        "name": "Exception - Unknown Member",
        "query": (
            "Can you check my tier upgrade status "
            "for member M999?"
        ),
    },

    # --------------------------------------------------------
    # 5. NORMAL CASE - REWARD BOOKING
    # --------------------------------------------------------

    {
        "name": "Normal - Reward Booking",
        "query": (
            "Can I book a DXB to LHR Economy reward "
            "for member M001?"
        ),
    },

    # --------------------------------------------------------
    # 6. EXCEPTION CASE - REWARD NOT AVAILABLE
    # --------------------------------------------------------

    {
        "name": "Exception - Reward Unavailable",
        "query": (
            "Can member M002 book a DXB to SIN "
            "Economy reward?"
        ),
    },

    # --------------------------------------------------------
    # 7. NORMAL CASE - FAMILY ACCOUNT
    # --------------------------------------------------------

    {
        "name": "Normal - Family Account",
        "query": (
            "Can you show the family account information "
            "for member M001?"
        ),
    },

    # --------------------------------------------------------
    # 8. AMBIGUOUS CASE - FAMILY ACCOUNT
    # --------------------------------------------------------

    {
        "name": "Ambiguous - Family Account",
        "query": (
            "Can you tell me about my family account?"
        ),
    },

    # --------------------------------------------------------
    # 9. NORMAL CASE - PARTNER AIRLINE
    # --------------------------------------------------------

    {
        "name": "Normal - Partner Airline",
        "query": (
            "Can I earn miles on Partner Air?"
        ),
    },

    # --------------------------------------------------------
    # 10. EXCEPTION CASE - UNKNOWN PARTNER
    # --------------------------------------------------------

    {
        "name": "Exception - Unknown Partner",
        "query": (
            "Can I earn miles on Unknown Airlines?"
        ),
    },

    # --------------------------------------------------------
    # 11. ESCALATION CASE
    # --------------------------------------------------------

    {
        "name": "Escalation - Missing Member ID",
        "query": (
            "My miles are missing but I don't have "
            "my member ID."
        ),
    },
]


# ============================================================
# RUN TESTS
# ============================================================

print("=" * 80)
print("AGENTIC AI DECISION FLOW TEST")
print("=" * 80)


for number, test_case in enumerate(test_cases, start=1):

    print("\n")
    print("=" * 80)
    print(f"TEST CASE {number}: {test_case['name']}")
    print("=" * 80)

    query = test_case["query"]

    print("\nQuery:")
    print(query)

    try:

        result = graph.invoke(
            {
                "query": query
            }
        )

        print("\nIntent:")
        print(
            result.get(
                "intent"
            )
        )

        print("\nMember ID:")
        print(
            result.get(
                "member_id"
            )
        )

        print("\nValidation:")
        print(
            result.get(
                "validation_status"
            )
        )

        print("\nEscalation Required:")
        print(
            result.get(
                "escalation_required"
            )
        )

        print("\nEscalation Reason:")
        print(
            result.get(
                "escalation_reason"
            )
        )

        print("\nResponse:")
        print(
            result.get(
                "response"
            )
        )

        print("\nTrace:")

        for item in result.get(
            "trace",
            []
        ):
            print(
                " -",
                item
            )

    except Exception as error:

        print("\nTEST ERROR:")
        print(error)


print("\n")
print("=" * 80)
print("TESTING COMPLETE")
print("=" * 80)