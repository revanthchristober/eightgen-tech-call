from __future__ import annotations

import os
from anthropic import Anthropic
from models import Task, TaskList

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = (
    "You are a PRD analysis assistant. Read the product requirements document "
    "and extract a list of concrete, actionable engineering tasks. For each task, "
    "infer a priority (high, medium, low) from language cues in the PRD "
    "(e.g. 'must have' / 'critical' -> high, 'should have' -> medium, "
    "'nice to have' / 'optional' -> low). If no priority cue exists, default to medium."
)


def extract_tasks(
    prd_text: str,
    client: Anthropic | None = None,
    model: str = DEFAULT_MODEL,
) -> list[Task]:
    client = client or Anthropic()
    message = client.messages.parse(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prd_text}],
        output_format=TaskList,
    )
    parsed = message.parsed_output
    if parsed is None:
        raise ValueError("Claude did not return a parseable structured output")
    return parsed.tasks
