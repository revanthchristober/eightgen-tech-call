from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

from extractor import extract_tasks
from models import PRDInput, Task

app = FastAPI()


@app.post("/extract-tasks", response_model=list[Task])
async def extract_tasks_endpoint(request: Request) -> list[Task]:
    raw = await request.body()
    text = raw.decode("utf-8", errors="replace")

    try:
        prd = PRDInput(text=text)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return extract_tasks(prd.text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claude extraction failed: {exc}") from exc
