from tools.tier_tools import calculate_tier_upgrade


test_members = [
    "M001",
    "M002",
    "M003",
    "M004",
    "M005",
]


for member_id in test_members:

    print("=" * 60)
    print(f"Member: {member_id}")

    result = calculate_tier_upgrade(member_id)

    print(result)