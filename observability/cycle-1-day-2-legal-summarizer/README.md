# Cycle 1, Day 2 — Legal Brief Summarizer (Observability)

**Topic:** Observability
**Date:** 2026-05-15
**Stack:** Python 3.14, `anthropic`, `langfuse` v4.6.1, `opentelemetry-instrumentation-anthropic`, `claude-haiku-4-5-20251001`

## What I built

A two-step legal-brief summarization pipeline (extract claims → write summary) with full Langfuse tracing. Each brief produces one trace containing:

- A root `legal-summarize` span with brief metadata
- Three child observations: `extract-claims`, `write-summary`, `judge-faithfulness`
- A nested generation span under each (auto-captured by `AnthropicInstrumentor`)
- Two trace-level scores: `compression_ratio` (guardrail) and `faithfulness` (LLM-judge, 0–1)

The judge composes Topic 1 (eval/judge prompts from Day 1) with Topic 2 (observability) — the natural Cycle 1 → Cycle 2 link the brief calls out as the stretch.

## Architecture choice: instrumentor + `@observe`, not manual spans

I tried hand-rolling `langfuse.start_as_current_generation(...)` around each Claude call first. Then read the Langfuse skill (langfuse/skills) and refactored to:

- **`AnthropicInstrumentor().instrument()`** auto-captures every `client.messages.create()` as a generation span with model name, input/output, and token counts. Zero hand-written code per call.
- **`@observe(name="...")`** decorators on the *structural* steps (`extract-claims`, `write-summary`, `judge-faithfulness`, `legal-summarize`). These name the business logic — the framework doesn't know `extract_claims()` is different from `write_summary()`, only I do.

Layered story: instrumentor handles the *what* (LLM mechanics), `@observe` handles the *why* (which step). Less code, more captured context.

## What observability surfaced

**1. The "0.0 faithfulness" bug was a parser bug, not a model bug.**
First run, brief-001 and brief-002 both scored 0.0. Without traces I would have assumed the summaries were hallucinating. Looking at the raw judge output in the Langfuse UI:

> `"0.75\n\nThe summary accurately captures most"` — `finish_reason: length`

The model returned a correct score; `max_tokens=10` truncated trailing prose; `float(text.strip())` raised ValueError on the partial sentence; the `except` branch returned 0.0. Replaced with a regex that grabs the first number — fixed. **The trace was the only place the actual model output was visible.** A console with three numbers told a misleading story.

**2. Write-summary dominates latency, not extract-claims.**
Predicted: write-summary slower (it has to "reason and generate"). Confirmed: write-summary ~4.65s of a ~7.99s end-to-end (58%). The reason isn't that it reasons more — extract-claims reads the *full brief* (more input tokens) but emits ~175 output tokens; write-summary reads short claims but emits ~200+ output tokens. **Output tokens dominate latency, not input tokens.** That's a load-bearing fact for future cost/perf tradeoffs.

**3. Compression ratio target was wrong.**
Brief said target <0.25; predicted 0.25–0.30. Actual: 0.45–0.82. A one-paragraph summary of a 3-paragraph brief is structurally never going to hit 0.25 character compression. The metric is more useful as a **regression detector** ("did our summaries suddenly get longer?") than as a quality threshold. Will revisit in a later cycle when we get into eval design properly.

**4. Single-run variance is real.**
Re-ran the pipeline; brief-001's compression jumped 0.526 → 0.818 between runs. Same prompts, same model, default temperature. **One run is a sample, not a measurement.** Worth filing for the future cycle on statistical thinking + temperature.

## Predictions (recorded before running)

| Question | Prediction | Actual |
|---|---|---|
| Compression ratio | <0.25 or <0.30 | 0.45–0.82 — wrong, target was unrealistic |
| Slowest span | write-summary | write-summary (4.65 / 7.99s) — right |
| Failure mode caught only by Langfuse | unknown | parser swallowing valid model output |

## Interview hook (60-second story)

> "I built a two-step legal summarization pipeline with Langfuse traces and an LLM-judge faithfulness score. On the first run two of three traces scored 0.0 faithfulness. Looking at the raw judge output in Langfuse, the model had returned correct scores like '0.75' but `max_tokens=10` truncated the trailing prose and my parser threw a ValueError on the partial sentence — falling through to a 0.0 default. Without observability I would have blamed the summarizer; the trace immediately localized the bug to my parsing logic. The takeaway: observability isn't just for performance, it's the single source of truth that decides *which component* you debug."

## Files

- `summarize.py` — pipeline, instrumentation, scoring, console table
- `sample_briefs.py` — three hardcoded briefs (commercial contract, non-solicit injunction, data-breach class action)
- `requirements.txt` — pinned deps
- `explainer.html` — Mets-themed daily explainer

## What I'd do in cycle 2+

- Multiple runs per brief to get distributions, not point values
- LLM-judge with structured output (JSON mode) instead of regex parsing
- Score the judge itself against a small human-rated set
- Use Langfuse Datasets to lock in golden inputs and run regression evals against future prompt changes
