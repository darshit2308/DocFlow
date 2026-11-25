# DECISIONS.md

Every significant design choice, the alternative considered, and why this one was picked.
This is the interview script.

---

## 1. Postgres for both workflow state and vectors

**Decision:** Use a single Postgres instance (pgvector extension) for workflow state, audit log, and vector embeddings.

**Alternative:** Redis for queue, Pinecone/Weaviate for vectors, Postgres for state.

**Why rejected:** Three services means three failure modes, three connection pools, and three things to pay for. pgvector with an HNSW index is fast enough for <10k clause chunks. Single-service simplicity wins at this scale.

---

## 2. Code guardrail for the final decision (not an agent)

**Decision:** `decide()` in `app/decision/engine.py` is a pure Python function — no LLM, no I/O.

**Alternative:** Let the policy_checker agent make the final routing decision.

**Why rejected:** An LLM can be prompt-injected, can hallucinate a compliant verdict, or can be misconfigured. The cost is coverage: some edge cases the model would route correctly go to review instead. That is the right trade-off for a finance approval system. Every reviewer correction is an eval example that improves the model, but the guardrail never approves what the rules say not to.

---

## 3. AI Studio (free) instead of Vertex AI (paid)

**Decision:** Use `google-generativeai` SDK pointing to the AI Studio endpoint.

**Alternative:** Vertex AI Gemini through the Google GenAI SDK in Vertex mode.

**Why:** Student project — no billing. The SDK supports the same Gemini models. Document the production upgrade path (`USE_VERTEX=true`, service account credentials) in the README. The friction of this switch is a genuine field-insight (see `field_insights.md`).

---

## 4. 3-sample agreement for field confidence (not model self-reported confidence)

**Decision:** Run extraction 3× at temperatures [0, 0.4, 0.4], take the modal normalized value per field, and compute confidence as the fraction of samples that agreed.

**Alternative:** Use the model's own logprob or stated confidence score.

**Why rejected:** Self-reported model confidence is poorly calibrated and not directly available through the structured-output API. Sample agreement is empirically calibrated: we bin it on the dev set and pick the threshold that hits our accuracy target. That number is defensible in an interview.

---

## 5. Hybrid retrieval (vector + full-text) over vector-only

**Decision:** Reciprocal rank fusion of pgvector cosine similarity and Postgres ts_rank, top 5.

**Alternative:** Vector-only retrieval.

**Why:** Measured on the 40-question policy eval set. Results in `docs/eval/retrieval_comparison.md`. Short exact clause references ("clause 7.3") are found by full-text search and missed by embedding similarity. Hybrid wins by N pp on hit@3. Numbers filled in after the eval run.

---

_Add entries here as you make each design decision. Do it the same day, not at the end._
