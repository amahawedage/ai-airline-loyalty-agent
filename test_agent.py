from agent.graph import build_graph


def main():

    graph = build_graph()

    test_query = "My miles are missing for member M001."

    result = graph.invoke(
        {
            "query": test_query
        }
    )

    print("\n==============================")
    print("AGENT TEST RESULT")
    print("==============================")

    print("\nQuery:")
    print(result["query"])

    print("\nIntent:")
    print(result.get("intent"))

    print("\nMember ID:")
    print(result.get("member_id"))

    print("\nRetrieved Sources:")
    print(result.get("retrieved_sources"))

    print("\nTool Results:")
    print(result.get("tool_results"))

    print("\nValidation:")
    print(result.get("validation_status"))

    print("\nResponse:")
    print(result.get("response"))

    print("\nTrace:")
    for item in result.get("trace", []):
        print("-", item)


if __name__ == "__main__":
    main()