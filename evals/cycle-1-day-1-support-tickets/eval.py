"""Offline eval harness: support-ticket triage classifier + LLM-as-judge.

Run: python eval.py
Requires ANTHROPIC_API_KEY in repo-root .env.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

CLIENT = Anthropic()
MODEL = "claude-haiku-4-5"
CATEGORIES = ["billing", "technical", "account", "other"]

GOLDEN: list[dict] = [
    # billing (4)
    {"ticket": "My invoice is wrong, charged twice for the same month", "expected": "billing"},
    {"ticket": "I need a refund for last month's subscription, I cancelled before renewal", "expected": "billing"},
    {"ticket": "Why was my card charged $49 when the plan says $39?", "expected": "billing"},
    {"ticket": "Can I get a copy of my receipt for the March payment?", "expected": "billing"},
    # technical (4)
    {"ticket": "App crashes on login on iOS 17, started after the latest update", "expected": "technical"},
    {"ticket": "Can't reset 2FA, the SMS code never arrives", "expected": "technical"},
    {"ticket": "Export to CSV produces a corrupted file every time", "expected": "technical"},
    {"ticket": "Dashboard charts are blank in Safari but work in Chrome", "expected": "technical"},
    # account (4)
    {"ticket": "How do I change the email address on my account?", "expected": "account"},
    {"ticket": "I want to delete my account and all associated data", "expected": "account"},
    {"ticket": "Add my coworker Sarah as an admin on our team workspace", "expected": "account"},
    {"ticket": "Transfer ownership of the workspace to a different user", "expected": "account"},
    # other (3)
    {"ticket": "Do you offer discounts for nonprofits?", "expected": "other"},
    {"ticket": "Where can I find your API documentation?", "expected": "other"},
    {"ticket": "Are you hiring? I saw your product at a conference", "expected": "other"},
    # adversarial / boundary cases — designed to trip the classifier
    # The user's PRIMARY ASK governs the category, even if other keywords appear.
    {
        # Mentions a charge, but the ask is to close the account → account, not billing.
        "ticket": "I was charged again after I deleted my account last month — please close it for good.",
        "expected": "account",
    },
    {
        # Keyword "technically" is a trap; intent is account ownership change.
        "ticket": "Technically my cofounder owns the workspace, but I'm the one paying — can you swap us?",
        "expected": "account",
    },
    {
        # Bug-shaped, but the user is asking how to use the product, not reporting breakage → other.
        "ticket": "Is there a way to bulk-export tickets older than 90 days? Couldn't find it in the docs.",
        "expected": "other",
    },
    {
        # Sounds like billing ("invoice", "$"), but the ask is a feature/process question → other.
        "ticket": "Do your invoices show line-item taxes? Our finance team needs that for compliance.",
        "expected": "other",
    },
]

CLASSIFIER_SYSTEM = f"""You are a support-ticket triage classifier.
Classify each ticket into exactly one of: {", ".join(CATEGORIES)}.

- billing: invoices, charges, refunds, receipts, pricing disputes
- technical: bugs, crashes, errors, things not working as expected
- account: profile changes, deletions, team membership, ownership
- other: anything else (sales questions, partnerships, general inquiries)

Respond with ONLY a JSON object: {{"category": "<one of the four>"}}"""

JUDGE_CORRECT_SYSTEM = """You are an evaluation judge. The classifier got the category RIGHT.
Rate the quality of the match on a 1-5 scale based on how clear-cut and unambiguous
the classification is given the ticket text. 5 = obviously correct, 1 = lucky guess.

Respond with ONLY JSON: {"score": <1-5>, "rationale": "<one sentence>"}"""

JUDGE_WRONG_SYSTEM = """You are an evaluation judge. The classifier got the category WRONG.
Explain in one sentence why the expected category is more appropriate than the predicted one.

Respond with ONLY JSON: {"rationale": "<one sentence>"}"""


@dataclass
class Result:
    ticket: str
    expected: str
    predicted: str
    correct: bool
    judge_score: int | None = None
    judge_rationale: str = ""


def _call_json(system: str, user: str) -> dict:
    msg = CLIENT.messages.create(
        model=MODEL,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = msg.content[0].text.strip()
    # Strip code fences if present.
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def classify(ticket: str) -> str:
    out = _call_json(CLASSIFIER_SYSTEM, f"Ticket: {ticket}")
    return out.get("category", "other")


def judge(result: Result) -> None:
    user = (
        f"Ticket: {result.ticket}\n"
        f"Expected: {result.expected}\n"
        f"Predicted: {result.predicted}"
    )
    if result.correct:
        out = _call_json(JUDGE_CORRECT_SYSTEM, user)
        result.judge_score = int(out.get("score", 0))
        result.judge_rationale = out.get("rationale", "")
    else:
        out = _call_json(JUDGE_WRONG_SYSTEM, user)
        result.judge_rationale = out.get("rationale", "")


def run() -> list[Result]:
    results: list[Result] = []
    for i, ex in enumerate(GOLDEN, 1):
        predicted = classify(ex["ticket"])
        r = Result(
            ticket=ex["ticket"],
            expected=ex["expected"],
            predicted=predicted,
            correct=predicted == ex["expected"],
        )
        judge(r)
        marker = "✓" if r.correct else "✗"
        print(f"  [{i:>2}/{len(GOLDEN)}] {marker} {predicted:<10} (expected {r.expected})")
        results.append(r)
    return results


def report(results: list[Result]) -> None:
    correct = [r for r in results if r.correct]
    failures = [r for r in results if not r.correct]
    n = len(results)
    acc = len(correct) / n * 100

    scores = [r.judge_score for r in correct if r.judge_score is not None]
    avg = sum(scores) / len(scores) if scores else 0.0

    print("\n" + "=" * 60)
    print(f"Accuracy:        {len(correct)}/{n} ({acc:.1f}%)")
    print(f"Judge avg score: {avg:.2f} / 5.0  (over {len(scores)} correct)")
    if failures:
        print("Failures:")
        for r in failures:
            print(f'  - "{r.ticket}"')
            print(f"      predicted: {r.predicted}, expected: {r.expected}")
            print(f"      Judge: {r.judge_rationale}")
    else:
        print("Failures: none")
    print("=" * 60)

    # Persist a JSON dump alongside the script for the README.
    out_path = Path(__file__).parent / "results.json"
    out_path.write_text(
        json.dumps(
            {
                "n": n,
                "correct": len(correct),
                "accuracy": acc,
                "judge_avg": avg,
                "results": [r.__dict__ for r in results],
            },
            indent=2,
        )
    )
    print(f"Wrote {out_path.name}")


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not found in environment / .env")
    print(f"Running {len(GOLDEN)} tickets through {MODEL}...\n")
    report(run())
