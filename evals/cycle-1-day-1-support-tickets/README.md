# Cycle 1 · Day 1 · Eval Frameworks — Support-Ticket Triage

**Format:** BUILD · **Date:** 2026-05-14 · **Topic:** evals (1 of 12)

## What I built
A from-scratch offline eval harness in Python — no eval libraries — for a 4-class support-ticket triage classifier:
- 15-example hand-written golden set covering billing, technical, account, other.
- Classifier: `claude-haiku-4-5` with a JSON-only response contract.
- Exact-match scorer → accuracy.
- LLM-as-judge: scores correct predictions 1–5 for clarity, explains failures in one sentence.
- Structured report + `results.json` dump.

## How to run
```bash
cd evals/cycle-1-day-1-support-tickets
python3 -m venv .venv && .venv/bin/pip install anthropic python-dotenv
.venv/bin/python eval.py
```
Reads `ANTHROPIC_API_KEY` from the repo-root `.env`.

## What happened
- 15/15 (100%) accuracy.
- Judge avg 5.00 / 5.0.
- No failures.

That sounds like a win but it isn't — see `findings.md`. The golden set was too easy; every ticket carried an explicit category keyword. An eval that can't fail can't tell me whether a prompt change helped.

## Interview hook (60-second answer)
> I built a from-scratch offline eval harness for a support-ticket classifier — no frameworks, just the primitives: golden set, exact-match scorer, LLM-as-judge for quality and failure rationale. The first run scored 100%, and the real lesson was that this was a *failure of the eval, not a success of the model*. A golden set without adversarial or ambiguous examples can't distinguish a good prompt from a bad one, so the next iteration is to deliberately seed near-misses — overlap cases, keyword traps, and sparse-signal tickets — so the harness has resolution to detect actual prompt regressions. The judge call earns its keep on the boundary cases, not on the obvious ones.

## What advances next cycle
Cycle 2 on this topic should build on this folder by importing `GOLDEN` and adding an adversarial v2 set, then comparing prompts head-to-head with a `compare_runs()` diff. The compositional jump is from "does my eval run" to "does my eval discriminate."
