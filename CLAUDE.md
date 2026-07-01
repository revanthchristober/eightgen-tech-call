# Interview Session Rules

## Context
Live technical interview. Time budget: 60 minutes total, ~45 minutes building.
Optimize for working, demonstrable output over completeness.

## Workflow — always follow this loop

1. **Explore first.** When I paste a problem, do NOT write code immediately.
   - Restate the problem in 2-3 sentences
   - List assumptions
   - Ask up to 3 clarifying questions
   - Wait for my go-ahead

2. **Plan before coding.** Produce a short markdown checklist:
   - Data model / schema
   - Core logic
   - API layer (if needed)
   - One test
   - Max 5-8 bullet points. No code in this step.

3. **Self-critique gate.** Before any code:
   - What is the riskiest assumption in this plan?
   - What would break first?
   - Wait for my approval before proceeding.

4. **Code in small increments.** One checklist item at a time.
   Never generate the entire solution in one shot.

5. **Always write at least one test.** Run it. Show output.

6. **Eval check before declaring done.**
   Does the output satisfy the acceptance criteria from step 1?

7. **Surface trade-offs.** When 2+ approaches exist, one line: chose X over Y because Z.

## Prompting style I'll use
Spec-first format:
"Build [X]. Input: [Y]. Output: [Z, exact shape]. Constraints: [...]"
Match this format in your responses.

## Tech defaults (flexible)
- **Default stack:** Python 3.11+ / FastAPI / Pydantic v2 / pytest
- **If interviewer specifies a different language or framework** (Node/TS, Go, Java, Django, Flask, Express, etc.), switch immediately — no pushback, no "but Python is better."
- **First message check:** If the problem statement names a language/framework, restate it in the Explore step so we're aligned before Plan.
- Minimal dependencies. Prefer stdlib / built-ins of whatever stack.
- Match idiomatic style of the chosen language (PEP 8 for Python, gofmt for Go, etc.).

## Communication
- Terse. I am narrating live.
- After each step: 1-2 lines on what was built, what's next.
- If something fails, say so and propose the next move immediately.

## Hard rules
- Never skip Explore, Plan, or Self-critique gate.
- Never generate more than one checklist item without pausing.
- Always run tests, never claim they'd pass.
