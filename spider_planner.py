from spider_retriever import retrieve_payloads


AVAILABLE_CATEGORIES = [
    "system_leak",
    "override",
    "roleplay",
    "indirect_injection",
    "tool_exploit",
    "encoding",
    "general",
    "multi_turn_setup",
    "context_poisoning",
]


def select_attack_strategy(target_response):

    response = target_response.lower()

    if "system prompt" in response:
        return "system_leak"

    if "cannot comply" in response:
        return "override"

    if "not allowed" in response:
        return "override"

    if "as an ai language model" in response:
        return "roleplay"

    if "tool" in response:
        return "tool_exploit"

    if "encoded" in response:
        return "encoding"

    return "general"


def get_next_payload(target_response):

    category = select_attack_strategy(target_response)

    if category not in AVAILABLE_CATEGORIES:
        category = "general"

    payloads = retrieve_payloads(category=category, k=3)

    return payloads
