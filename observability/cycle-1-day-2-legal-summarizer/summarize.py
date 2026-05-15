from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from anthropic import Anthropic
from langfuse import get_client, observe
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

from sample_briefs import BRIEFS

AnthropicInstrumentor().instrument()

CLIENT = Anthropic()
langfuse = get_client()
MODEL = "claude-haiku-4-5-20251001"

EXTRACT_SYSTEM = (
    "You are a legal analyst. Read the brief the user provides and extract "
    "the three most important legal claims or issues. Return exactly three "
    "bullet points, one per line, each starting with '- '. No preamble."
)

SUMMARY_SYSTEM = (
    "You are a legal analyst. The user will give you three claims extracted "
    "from a legal brief. Write a single-paragraph executive summary (4-6 "
    "sentences) that an attorney could read in 30 seconds. No preamble, no bullets."
)

JUDGE_SYSTEM = (
    "You are a strict legal-fact-checker. You will be given a legal brief and a "
    "summary of that brief. Score the summary's faithfulness on a 0.0-1.0 scale: "
    "1.0 = every fact in the summary is supported by the brief; 0.0 = the summary "
    "introduces unsupported facts. Respond ONLY with a single decimal number."
)


def claude(system: str, user_content: str, max_tokens: int = 400) -> tuple[str, dict]:
    msg = CLIENT.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    text = msg.content[0].text
    usage = {"input": msg.usage.input_tokens, "output": msg.usage.output_tokens}
    return text, usage


@observe(name="extract-claims")
def extract_claims(brief_text: str) -> tuple[str, dict]:
    langfuse.update_current_span(input=brief_text)
    text, usage = claude(EXTRACT_SYSTEM, brief_text)
    langfuse.update_current_span(output=text)
    return text, usage


@observe(name="write-summary")
def write_summary(claims: str) -> tuple[str, dict]:
    langfuse.update_current_span(input=claims)
    text, usage = claude(SUMMARY_SYSTEM, claims)
    langfuse.update_current_span(output=text)
    return text, usage


@observe(name="judge-faithfulness")
def judge_faithfulness(brief_text: str, summary: str) -> float:
    user = f"BRIEF:\n{brief_text}\n\nSUMMARY:\n{summary}"
    langfuse.update_current_span(input=user)
    text, _ = claude(JUDGE_SYSTEM, user, max_tokens=10)
    langfuse.update_current_span(output=text)
    import re
    m = re.search(r"\d*\.?\d+", text)
    return float(m.group()) if m else 0.0


@observe(name="legal-summarize")
def process_brief(brief: dict) -> dict:
    langfuse.update_current_span(
        input=brief["text"],
        metadata={"brief_id": brief["id"]},
    )

    claims, claims_usage = extract_claims(brief["text"])
    summary, summary_usage = write_summary(claims)
    faithfulness = judge_faithfulness(brief["text"], summary)
    compression_ratio = len(summary) / len(brief["text"])

    langfuse.update_current_span(output=summary)
    langfuse.score_current_trace(name="compression_ratio", value=round(compression_ratio, 3))
    langfuse.score_current_trace(name="faithfulness", value=faithfulness)

    return {
        "brief_id": brief["id"],
        "claims_tokens": claims_usage["output"],
        "summary_tokens": summary_usage["output"],
        "compression_ratio": round(compression_ratio, 3),
        "faithfulness": faithfulness,
    }


def print_table(rows: list[dict]) -> None:
    headers = ["brief_id", "claims_tokens", "summary_tokens", "compression_ratio", "faithfulness"]
    print(" | ".join(headers))
    print("-" * 80)
    for r in rows:
        print(" | ".join(str(r[h]) for h in headers))


if __name__ == "__main__":
    print("langfuse auth:", langfuse.auth_check())
    results = [process_brief(b) for b in BRIEFS]
    print_table(results)
    langfuse.flush()
