from agent.graph import build_graph


graph = build_graph()


query = (
    #"My miles are missing but I don't have "
    #"my member ID."
    #"Can you check my tier upgrade status? My member ID is M003."
    "I need help with my missing miles for M999."
)


result = graph.invoke(
    {
        "query": query
    }
)


print("=" * 70)
print("ESCALATION AGENT TEST")
print("=" * 70)


print("\nQuery:")
print(query)


print("\nIntent:")
print(result.get("intent"))


print("\nMember ID:")
print(result.get("member_id"))


print("\nValidation:")
print(result.get("validation_status"))


print("\nEscalation Required:")
print(result.get("escalation_required"))


print("\nEscalation Reason:")
print(result.get("escalation_reason"))


print("\nTool Results:")
print(result.get("tool_results"))


print("\nResponse:")
print(result.get("response"))


print("\nTrace:")

for item in result.get("trace", []):
    print("-", item)