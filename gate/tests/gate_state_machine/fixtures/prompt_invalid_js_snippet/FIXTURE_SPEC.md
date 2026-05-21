# Fixture: prompt_invalid_js_snippet

## Setup

- Implementation prompt file: `sprints/s42/P03_add_model_routing.md`
- Prompt includes the following code snippet:
  ```javascript
  // Register the new model
  const config = {
    model: claude-sonnet-4-6,   // BUG: unquoted — JS parses as claude minus sonnet minus 4 minus 6
    tier: 2,
    maxTokens: 8192
  };
  registry.register(config);
  ```
- The identifier `claude-sonnet-4-6` is unquoted — it will be parsed as a subtraction expression
- `IMPLEMENTER_PROMPT_LINT.md` records: Check 2 (Unquoted JS identifiers): PASS (incorrect)
- The implementer agent that reads this prompt will produce broken code:
  ```javascript
  model: claude - sonnet - 4 - 6   // NaN or ReferenceError
  ```

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Implementer prompt lint: invalid JS snippet found
       File: sprints/s42/P03_add_model_routing.md
       Line: "model: claude-sonnet-4-6,"
       Issue: UNQUOTED_JS_IDENTIFIER — "claude-sonnet-4-6" is not a valid JS expression;
              JS parses "claude - sonnet - 4 - 6" as subtraction
       Correct: "model: \"claude-sonnet-4-6\","
       IMPLEMENTER_PROMPT_LINT.md Check 2 verdict: PASS (incorrect)
       Invariant violated: no_unquoted_js_identifiers_in_prompt_snippets
```

## Expected invariant

`no_unquoted_js_identifiers_in_prompt_snippets`

## Why this matters

The implementer agent reads the prompt and copies the snippet. The resulting code will
throw a ReferenceError at runtime or silently use NaN as the model string. Model routing
will silently fail. This is a hot file change (LLM routing) and this bug would cause
all LLM requests to fail with an invalid model string.
