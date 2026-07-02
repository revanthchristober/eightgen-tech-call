import { ChatAnswer, ResearchJob } from "./types";

class ApiError extends Error {}

async function unwrap<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail || res.statusText);
  }
  return res.json();
}

export async function askChat(question: string): Promise<ChatAnswer> {
  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return unwrap<ChatAnswer>(res);
}

export async function startResearch(brief: string): Promise<ResearchJob> {
  const res = await fetch("/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief }),
  });
  return unwrap<ResearchJob>(res);
}

export async function getResearchJob(jobId: string): Promise<ResearchJob> {
  const res = await fetch(`/research/${jobId}`);
  return unwrap<ResearchJob>(res);
}

export { ApiError };
