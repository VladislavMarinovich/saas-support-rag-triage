# How the assistant cites knowledge base sources

Every answer the Polaris assistant gives is grounded in knowledge base articles, and it shows you which ones it used so you can check the answer yourself.

## Reading the sources under an answer

Each response lists the articles it drew on. Use them for three things:

1. **Verification** — open the article and confirm the answer matches. The assistant summarizes; the article is authoritative.
2. **Depth** — an answer is short by design. The article usually has prerequisites, role requirements, and edge cases the summary omits.
3. **Trust calibration** — if the listed sources look unrelated to your question, treat the answer with suspicion and rephrase using product terms.

An answer with no sources is not a grounded answer. When the assistant has no relevant article it tells you so (AG002) instead of answering without sources.

## Why grounding matters more than fluency

The assistant is not allowed to answer from general knowledge, even when it could produce something that sounds right. Marketing analytics questions have product-specific answers: which plan includes Salesforce, whether a Viewer can edit an alert, what ER005 actually means. A fluent guess on any of those is wrong in a way that costs you time.

That constraint is why refusals exist at all. AG002 means no article covers your question; AG003 means the answer would need your private data; AG004 means a person has to handle it. All three are better outcomes than an invented answer.

If an answer cites an article that does not actually address your question, contact support and quote both the question and the cited source so the gap can be corrected.
