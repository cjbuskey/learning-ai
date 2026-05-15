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

@observe(name="judge-score")
def judge_score(brief_text: str, summary: str) -> float:
    user = f"BRIEF:\n{brief_text}\n\nSUMMARY:\n{summary}"
    langfuse.update_current_span(input=user)
    text, _ = claude(JUDGE_SYSTEM, user, max_tokens=10)
    langfuse.update_current_span(output=text)

def main():
    for brief in BRIEFS:
        score = judge_score(brief["text"], "The summary is faithful to the brief.")
        print(f"Score: {score}")

if __name__ == "__main__":
    main()