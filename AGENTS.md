# learning-ai

Daily Applied AI Engineer training projects. One ~60-minute brief per weekday, rotating through a 12-topic curriculum across cycles. Goal: prepare for an Anthropic Applied AI Engineer application in early 2027.

## How this repo works

A morning agent reads `curriculum-state.json`, picks the next topic, and generates a brief. The user works the brief in ~60 minutes and commits the artifact here. Each topic recurs every 12 weekdays at a higher rigor bar (foundational → compositional → production → frontier).

Read `curriculum-state.json` at the repo root to see cycle, last topic, and full history of prior builds. Always consult it before starting work — prior cycles for the same topic are the baseline today's brief must advance beyond.

## Repo layout

Organized **by topic**, not by date or cycle. Each topic gets a top-level folder; each instance of that topic gets a subfolder named `cycle-N-day-N-<short-slug>`.

```
learning-ai/
  curriculum-state.json        # canonical state — read before starting work
  briefs/                      # daily briefs (markdown), named YYYY-MM-DD-topic-N.md
  evals/                       # topic 1
  observability/               # topic 2
  agent-architectures/         # topic 3
  agent-output-language/       # topic 4
  agent-skills/                # topic 5
  tool-use/                    # topic 6
  retrieval/                   # topic 7
  context-engineering/         # topic 8
  agent-integration/           # topic 9
  cost-exercises/              # topic 10 (WRITE — memos, not code)
  safety-redteam/              # topic 11
  deployment-patterns/         # topic 12
```

Inside each topic folder:

```
evals/
  cycle-1-day-1-support-tickets/
    README.md         # the brief, plus what was built and what was learned
    ...code...
  cycle-2-day-13-legal-docs/
    ...
```

Cycle 2+ projects often **build on** prior cycle artifacts. When that happens, import or reference the prior folder explicitly rather than copying code — the composition is the point.

## Stack

No global default. Each brief specifies the stack (Python, Node/TS, etc.).

**Python venv:** shared `.venv/` at the repo root, activated for daily work. Each project still ships its own `requirements.txt` as a record of what that day needed (interview-artifact value, future reproducibility). Create a per-project venv only when versions conflict with the shared environment.

## Secrets

**Single `.env` at the repo root**, gitignored. Every project loads from it (e.g., `python-dotenv` with `find_dotenv()`, or `dotenv` in Node pointing at `../../.env`). Do not create per-project `.env` files. Do not commit keys.

Expected keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, plus any topic-specific keys (Langfuse, Braintrust, etc.) added as needed.

## Working a daily brief (the loop)

1. Read `curriculum-state.json` — confirm today's cycle, topic, and prior history for that topic.
2. Read the brief in `briefs/`.
3. **Confirm mode** — ask the user "Pair, Scaffold, or Demo?" if not specified. Default is **Pair** (user types, Claude reviews). See "Working modes" below.
4. Create `<topic-folder>/cycle-N-day-N-<slug>/` and scope the work to fit ~60 minutes. **Scope down rather than overflow.**
5. **Predict (5 min, user-only)** — before running anything, the user writes down what they expect the metric/output/failure modes to be. Claude prompts but does not predict.
6. Work the brief. Capture what was built and the "interview hook" insight in that folder's `README.md`.
7. **Generate `explainer.html`** in the project folder — Mets-themed (navy `#002D72`, orange `#FF5910`, Mulish font). One per day, standing deliverable. Reference template: `evals/cycle-1-day-1-support-tickets/explainer.html`. Keep it concise after Day 1 — reuse the established style; don't rebuild from scratch.
8. **Cold-typing drill (~10 min, in chat)** — Claude poses one small task, blank buffer, no copy-paste from today's repo. User types; Claude pushes back rather than autocompletes. One follow-up twist. Exit when the user has written it cold; if they couldn't, that's tomorrow's warm-up.
9. Mark the day done in `curriculum-state.json` (`done: true` for today's history entry) and commit.

## Working modes

Confirm at the start of every brief:

- **Pair (default)** — user types the implementation; Claude answers questions, reviews diffs, suggests fixes. Claude does NOT write the code unless asked.
- **Scaffold** — Claude writes a skeleton with `# TODO` blocks; user fills them in. Use for unfamiliar SDKs.
- **Demo** — Claude writes the full implementation; user reads/modifies. Reserved for WRITE briefs (cost memos) or topics where typing is not the lesson.

Reviewing builds exposure; typing builds fluency. Default to Pair.

## Constraints to respect

- ~60-minute budget per brief. Stretch goals are optional.
- ~$5 API spend cap per build.
- No sports/betting or Handigraphs domains. Vary domains across the week (support tickets, legal docs, code review, finance, healthcare, content moderation, customer ops, devtools, e-commerce, education, HR).
- Each cycle on a given topic must materially advance prior cycles — pick a fresh domain and state explicitly what's new.

## What to optimize for

Interview-ready artifacts. Each project should have a 60-second story: "I built X to learn Y, and the insight was Z." If a build doesn't yield that, the README should say what fell short and why — negative results are still learning.

## Notes for coding agents

- **Pair mode is the default.** Do not write the implementation unless the user asks or the brief specifies Scaffold/Demo. The user is preparing for an Anthropic Applied AI Engineer interview in early 2027 — typing fluency is the goal, not artifact polish.
- Don't scaffold beyond what the brief asks. Smallest viable artifact wins; production polish is reserved for cycle 3+ briefs that explicitly call for it. **Exception:** the daily `explainer.html` is part of the standing workflow, not scope creep.
- Don't auto-generate boilerplate READMEs. The README is the learning record — write it from what actually happened in the session.
- Prefer editing `curriculum-state.json` directly with a small script or jq over regenerating it.
- When a brief says "build on cycle N's artifact," import or call into that folder; don't fork it.
- During the cold-typing drill, never type the answer into the user's buffer or paste a full solution. Push back with leading questions instead.
