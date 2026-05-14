# Findings — Cycle 1, Day 1

## Result
- 15/15 (100%) accuracy on the hand-written golden set.
- Judge average: 5.00 / 5.0 across all 15.
- No failures to analyze — which is itself the finding.

## What this actually tells me
The golden set was too easy. Each ticket I wrote contained a near-explicit category keyword ("invoice," "crashes," "delete my account," "discounts for nonprofits"). Claude Haiku 4.5 has no trouble with surface-level pattern matching, so the eval has no signal — every prompt change would still score 100%. An eval that can't distinguish a good prompt from a bad one is worthless.

## What I'd change next
Adversarial examples are where this harness earns its keep. Concretely:
- **Ambiguous overlap**: "I was charged after I deleted my account" (billing or account?). Force the prompt to declare a tie-breaking rule.
- **Wrong-keyword traps**: "I want to *technically* close my account" — a ticket that contains the literal word "technically" but is an account request.
- **Sparse signal**: "It's broken" with no detail — the classifier must either pick `other` or ask for more info, and the eval should encode which.
- **Mixed intent**: "My card was charged twice AND the app crashes on login" — should produce a primary category plus flag the secondary.

The judge is also under-utilized when accuracy is 100%. Its real value shows up on near-misses, so the next iteration should keep ~30% of the set in the "could go either way" zone.

## Prompt-improvement hypothesis (testable next cycle)
Add a tie-breaker rule to the classifier system prompt: *"If a ticket mentions both a charge and an account action, classify by what the user is asking for, not what they mention."* Then re-run against an adversarial v2 golden set and see whether the rule moves accuracy on the ambiguous subset specifically (the only subset where it should matter).
