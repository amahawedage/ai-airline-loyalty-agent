from tools.member_tools import get_member_details
from tools.transaction_tools import check_missing_miles
from tools.reward_tools import check_reward_eligibility
from tools.family_tools import get_family_account
from tools.partner_tools import check_partner_airline


print("\n===== MEMBER TOOL =====")
print(get_member_details("M001"))

print("\n===== MISSING MILES TOOL =====")
print(check_missing_miles("M001"))

print("\n===== REWARD TOOL =====")
print(
    check_reward_eligibility(
        "M001",
        "DXB",
        "LHR",
        "Economy"
    )
)

print("\n===== FAMILY TOOL =====")
print(get_family_account("M001"))

print("\n===== PARTNER TOOL =====")
print(check_partner_airline("Partner Air"))