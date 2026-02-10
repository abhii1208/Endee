## Retrieval Evaluation Plan

This project includes a simple approach for evaluating the retrieval quality of the Endee-backed search.

### Manual relevance checks

1. Define a small set of test queries and expected relevant items, for example:
   - "504 errors on payments API" → expect ticket `TCK-1001`, FAQ `FAQ-001`, runbook `RB-INC-504`.
   - "login failures after password reset" → expect ticket `TCK-1003`, FAQ `FAQ-003`, runbook `RB-AUTH-LOGIN`.
2. For each query, call the `/search` endpoint with `top_k=5`.
3. Record whether the expected items appear in the top-k lists for tickets, FAQs, and runbooks.
4. Compute simple metrics such as recall@k (how many of the expected items were returned) and average rank of expected items.

### Automated script sketch

An evaluation script can be added under `scripts/` to:

- Load a small YAML or JSON file containing `{query, expected_ids}` pairs.
- Call `/search` for each query.
- Compute and print recall@k and mean reciprocal rank across all queries.

This demonstrates how to close the loop between search quality and data or configuration changes, and can be extended with more realistic labels over time.

