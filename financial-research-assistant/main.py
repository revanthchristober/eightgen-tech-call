from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException

import chat
from models import ChatAnswer, ChatRequest, ResearchJob, ResearchRequest
from research import JobStore, run_research_job

# UI lives in web/ (Next.js), talking to this API via next.config.ts rewrites.
app = FastAPI()
store = JobStore()

# asyncio.create_task() schedules but doesn't retain a strong reference --
# without this set, tasks can be garbage-collected mid-run.
_background_tasks: set[asyncio.Task] = set()


@app.post("/chat", response_model=ChatAnswer)
async def chat_endpoint(body: ChatRequest) -> ChatAnswer:
    try:
        return await asyncio.to_thread(chat.answer, body.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Answer generation failed: {exc}") from exc


@app.post("/research", status_code=202, response_model=ResearchJob)
async def start_research(body: ResearchRequest) -> ResearchJob:
    job = store.create(body.brief)
    task = asyncio.create_task(run_research_job(job.job_id, store))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return job


@app.get("/research/{job_id}", response_model=ResearchJob)
async def get_research(job_id: str) -> ResearchJob:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job
