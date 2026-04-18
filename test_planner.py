from spider_planner import get_next_payload

mock_response = "I'm sorry, I cannot provide that information."

payloads = get_next_payload(mock_response)

print("\nSelected payloads:\n")

for p in payloads:
    print(p["prompt"])
    print("-" * 60)