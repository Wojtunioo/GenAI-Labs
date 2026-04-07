# Production Readiness Checklist

**Instructions:** Complete all sections below. Check the box when an item is implemented, and provide descriptions where requested. This checklist is a required deliverable.

---

## Approach
I focused mainly on prompt design and making the system produce more sensible answers.

I built a simple pipeline with SQL generation, validation, execution, and answer generation, but most of my effort went into improving the prompts so the outputs are more analytical instead of just listing numbers.

I am not fully satisfied with the results. The system works, but the answers are often too generic or miss the main insight.

I spent around 4 hours on this. The remaining ~2 hours I spent on validation, running tests, and completing this questionnaire.

- [ ] **System works correctly end-to-end** 
nope :(

**What were the main challenges you identified?**
This was my first time working with Python, so part of the challenge was just getting comfortable with the language and environment.

The main problem I focused on was getting the LLM to generate meaningful SQL and answers. Even when the SQL is correct, the final answer is often not what I would expect.

For example, for the question "Compare average addiction levels across age groups", the system returns a breakdown of values, but the real insight is that there is basically no meaningful difference between age groups. That kind of conclusion is missing.

So the biggest challenge was not the pipeline itself, but getting useful, sensible outputs from the LLM.

**What was your approach?**
At a high level, I used GPT to help me implement the solution, because this was my first time working with Python.

My goal was to get a working pipeline and then focus on improving the quality of outputs, especially by adjusting prompts so the answers are more meaningful.

I am aware that this is not a perfect solution, and I am not fully satisfied with the results, but it allowed me to understand the problem and build a working system within limited time.
---

## Observability

- [x] **Logging**
  - Description:
  Basic logging is implemented using print statements in the benchmark script (questions, SQL, status, answers). There is no structured logging or log levels.
- [x] **Metrics**
  - Description:
  Basic metrics are collected in the pipeline, including total latency per request, number of LLM calls, and token usage. These are aggregated in the benchmark script.
- [ ] **Tracing**
  - Description:
  Not implemented. There is no request-level tracing across pipeline stages.
---

## Validation & Quality Assurance

- [x] **SQL validation**
  - Description:
  Implemented a simple validation that allows only SELECT queries and blocks patterns like SELECT *. This prevents destructive queries, but it is very basic and not a full SQL parser.
- [ ] **Answer quality**
  - Description:
  Answer quality is inconsistent. Even when SQL is correct, the LLM often returns generic summaries instead of clear insights. I tried improving this with prompt tuning, but I am not satisfied with the results.
- [ ] **Result consistency**
  - Description:
   Results are not fully consistent. The same question can lead to slightly different answers because of LLM variability.
- [x] **Error handling**
  - Description:
  Basic error handling is implemented with clear statuses (success, invalid_sql, unanswerable, error). Failures in SQL generation, validation, or execution are handled without crashing the pipeline.
---

## Maintainability

- [x] **Code organization**
  - Description:

  - Description:
    The code is split into separate components (pipeline, validator, executor, LLM client), so responsibilities are clearly separated. It is simple and easy to follow, but not deeply structured.
- [x] **Configuration**
  - Description:
    Basic configuration is done via environment variables (API key, model) and default paths. There is no advanced configuration system.
- [x] **Error handling**
  - Description:
    Errors are handled at each stage of the pipeline and mapped to simple statuses. It works, but the handling is basic and not very detailed.
- [ ] **Documentation**
  - Description:
     Minimal documentation. Only basic explanations in code and solution notes.
---

## LLM Efficiency

- [ ] **Token usage optimization**
  - Description:
    Not really optimized. I limited the number of rows passed to the LLM to reduce token usage, but there is no deeper optimization. Token usage could be reduced further.
- [x] **Efficient LLM requests**
  - Description:
    Each request uses two LLM calls (one for SQL, one for answer generation). This is simple and predictable, but not optimized for cost or performance.

---

## Testing

- [x] **Unit tests**
  - Description:
  Basic unit tests are provided (from the assignment). I did not add additional ones myself.
- [x] **Integration tests**
  - Description:
  The provided tests cover the full pipeline (LLM → SQL → execution → answer), so they act as integration tests.
- [x] **Performance tests**
  - Description:
   A benchmark script was provided as part of the assignment. I used it and extended it slightly to include LLM metrics (tokens and number of calls).
- [ ] **Edge case coverage**
  - Description:
  imited coverage. Some cases like invalid questions or unusual LLM outputs are handled, but not deeply tested.

---

## Optional: Multi-Turn Conversation Support

**Only complete this section if you implemented the optional follow-up questions feature.**

- [ ] **Intent detection for follow-ups**
  - Description: [How does your system decide if a follow-up needs new SQL or uses existing context?]

- [ ] **Context-aware SQL generation**
  - Description: [How does your system use conversation history to generate SQL for follow-ups?]

- [ ] **Context persistence**
  - Description: [How does your system maintain state across multiple conversation turns?]

- [ ] **Ambiguity resolution**
  - Description: [How does your system resolve ambiguous references like "what about males?"]

**Approach summary:**
```
[Describe your approach to implementing follow-up questions. What architecture did you choose?]
```

---

## Production Readiness Summary

**What makes your solution production-ready?**
It is not production-ready.

The basic pipeline works (SQL generation, validation, execution, answer), and there is simple validation and error handling, but the overall quality is not reliable enough.

The biggest issue is answer quality. Even when SQL is correct, the final answer often misses the main insight or is too generic. I am not confident in the consistency of the outputs.

There is also no proper logging, tracing, or strong validation, so debugging and monitoring would be limited in a real system.

This is more of a working prototype than a production-ready solution.

**Key improvements over baseline:**
Added a basic SQL validation layer to block unsafe queries (only SELECT allowed).
Improved prompt design to encourage analytical queries instead of raw data outputs.
Collected basic metrics (latency, token usage, number of LLM calls).
Extended the benchmark to include LLM-related metrics.

Overall, the improvements focus on safety and basic observability, but the system is still quite simple.

**Known limitations or future work:**
Answer quality is not reliable and often misses the main insight.
SQL validation is very basic and not a full parser.
Potential risk of prompt/SQL injection — current validation is simple and may not catch all malicious patterns.
No tracing or structured logging.
Token usage is not optimized.
Results can vary due to LLM randomness.
Limited handling of edge cases.

Future work would mainly focus on improving answer quality, stronger validation (including injection protection), and more reliable outputs.

---

## Benchmark Results

Include your before/after benchmark results here.

**Baseline (if you measured):**
- Average latency: `8458.97 ms`
- p50 latency: `9026.53 ms`
- p95 latency: `11318.88 ms`
- Success rate: `0.0 %`

> ⚠️ **Note:** Baseline was measured after a minimal compatibility fix in `scripts/benchmark.py` (`result["status"]` → `result.status`) because the script expected `PipelineOutput` to be subscriptable.
> ⚠️ **Observation:** The baseline pipeline returned `unanswerable` for all queries due to LLM response parsing issues (`content=None`) and lack of schema awareness.

**Your solution:**
- Average latency: `3132.2 ms`
- p50 latency: `2651.77 ms`
- p95 latency: `5078.22 ms`
- Success rate: `1.0 %`

**LLM efficiency:**
- Average tokens per request: `1419.22`
- Average LLM calls per request: `2.0`

---

**Completed by:** Wojciech Los
**Date:** 07.04.2026
**Time spent:** 6