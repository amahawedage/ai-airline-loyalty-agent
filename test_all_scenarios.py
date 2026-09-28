from agent.graph import build_graph


def run_test(query):
    print("\n" + "=" * 70)
    print("QUERY:", query)
    print("=" * 70)

    graph = build_graph()

    result = graph.invoke({
        "query": query
    })

    print("Intent:", result.get("intent"))
    print("Member ID:", result.get("member_id"))
    print("Sources:", result.get("retrieved_sources"))
    print("Tool Results:", result.get("tool_results"))
    print("Validation:", result.get("validation_status"))
    print("Response:", result.get("response"))

    print("\nTrace:")
    for item in result.get("trace", []):
        print("-", item)


def main():

    run_test(
        "My miles are missing for member M001."
    )

    run_test(
        "Can member M003 qualify for a higher tier?"
    )

    run_test(
        "Can member M001 book a reward flight from DXB to LHR in Economy?"
    )

    run_test(
        "Who are the family members for member M001?"
    )

    run_test(
        "Can I earn miles when flying with Partner Air?"
    )


if __name__ == "__main__":
    main()