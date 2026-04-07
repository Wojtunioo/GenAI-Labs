Each stage is isolated and returns a structured output, which makes it easier to debug, although observability is still basic.

### Components

- `OpenRouterLLMClient`
  - Handles communication with the LLM
  - Tracks basic stats like token usage and number of calls
- `SQLValidator`
  - Allows only SELECT queries
  - Blocks simple unsafe patterns like `SELECT *`
- `SQLiteExecutor`
  - Executes SQL queries against SQLite
  - Returns a limited number of rows (first 100)
- `AnalyticsPipeline`
  - Connects all stages together
  - Handles basic error states and final response

---

## Key Decisions

### 1. Basic SQL validation

Only `SELECT` queries are allowed.

Reason:
- Prevent destructive operations (e.g. `DELETE`, `DROP`)
- Keep the system safe at a basic level

Note:
- This is a simple rule-based check, not a full SQL parser.

---

### 2. Limiting result size

Only the first 100 rows are passed to the LLM.

Reason:
- Reduce token usage
- Avoid sending large payloads
- Keep latency under control

---

### 3. Two-step LLM usage

Each request uses:
- 1 call for SQL generation
- 1 call for answer generation

Reason:
- Keeps the flow simple and predictable
- Makes debugging easier

Note:
- This is not optimized for cost or performance.

---

### 4. Prompt-focused approach

Most of the effort went into prompt design to make outputs more analytical.

Reason:
- Raw LLM outputs tend to just list values
- The goal was to encourage more meaningful summaries

Note:
- Results are still inconsistent and often miss the main insight.

---

## Error Handling

The pipeline defines basic statuses:

- `success`
- `invalid_sql`
- `unanswerable`
- `error`

Behavior:
- Invalid or missing SQL → fallback message
- Execution errors → classified based on SQLite error

This works, but error handling is simple and not very detailed.

---

## Performance

Measured using the provided benchmark script (slightly extended with LLM metrics).

Example metrics:

- Average latency: ~3.2s per request
- Success rate: 100%
- Average LLM calls per request: 2
- Average tokens per request: 1419.22

---

## Limitations

- SQL validation is very basic (not a full parser)
- Potential risk of prompt/SQL injection
- Only a single table is supported
- No schema awareness beyond prompt instructions
- Answer quality is inconsistent and often misses key insights
- No structured logging or tracing
- Token usage is not optimized

---

## Possible Improvements

- Stronger SQL validation (e.g. proper parsing, injection protection)
- Improve answer quality (better prompts or post-processing)
- Add caching for repeated queries
- Add schema awareness instead of hardcoded schema
- Introduce structured logging and tracing
- Reduce token usage and optimize LLM calls

---

## Conclusion

This is a working prototype rather than a production-ready system.

The pipeline is simple and understandable, and it correctly connects all stages (LLM → SQL → execution → answer), but the main limitation is the quality and consistency of the final answers.

The system works, but it would need improvements in validation, observability, and especially answer quality to be considered production-ready.