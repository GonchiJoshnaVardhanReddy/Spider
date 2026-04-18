from spider_retriever import retrieve_payloads

results = retrieve_payloads(category="system_leak", k=3)

for r in results:
    print(r)