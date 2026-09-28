from tools.escalation_tools import create_human_escalation


result = create_human_escalation(
    scenario="Missing Miles",
    member_id="M001",
    reason="Additional information is required to investigate the missing miles claim.",
    query="My miles are missing for member M001."
)

print("=" * 60)
print("ESCALATION TEST")
print("=" * 60)

print(result)