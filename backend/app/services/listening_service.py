import random
import uuid

from app.data.listening_passages import FIXED_PASSAGES
from app.models.speaking import ListeningPassage
from app.services.anthropic_client import structured_completion

GENERATE_SYSTEM_PROMPT = (
    "You are an item writer for the Trinity College London ISE II exam (CEFR B2), "
    "Independent Listening task. You write ORIGINAL 180-220 word scripts meant to be "
    "read aloud naturally (like a short radio talk or podcast segment) on an "
    "everyday, work, or social-issue topic — never a dry academic text. Follow it "
    "with one gist ('general') question answerable after a single listen, and one "
    "detail question that requires a specific piece of information from the script "
    "and needs a longer, more developed spoken answer."
)

GENERATE_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "text": {"type": "string"},
        "general_question": {"type": "string"},
        "detail_question": {"type": "string"},
    },
    "required": ["topic", "text", "general_question", "detail_question"],
}


def get_fixed_passage(passage_id: str | None = None) -> ListeningPassage:
    if passage_id:
        match = next((p for p in FIXED_PASSAGES if p["id"] == passage_id), None)
        if match is None:
            raise ValueError(f"Unknown passage id: {passage_id}")
    else:
        match = random.choice(FIXED_PASSAGES)
    return ListeningPassage(**match, source="fixed")


def generate_passage() -> ListeningPassage:
    result = structured_completion(
        system=GENERATE_SYSTEM_PROMPT,
        user_content="Write one new B2-level listening script with its two questions.",
        tool_name="submit_passage",
        tool_description="Submit the generated listening script and its two questions.",
        input_schema=GENERATE_TOOL_SCHEMA,
        max_tokens=1200,
    )
    return ListeningPassage(id=f"generated-{uuid.uuid4().hex[:8]}", source="generated", **result)
