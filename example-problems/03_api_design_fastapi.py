"""
Problem: URL Shortener API
Input: POST /shorten {url: str} -> {short_code: str}
       GET  /{short_code}       -> redirect or 404
Constraints: in-memory store, no auth, FastAPI + Pydantic v2
"""
import random
import string
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

app = FastAPI()
store: dict[str, str] = {}


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_code: str


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


@app.post("/shorten", response_model=ShortenResponse)
def shorten(req: ShortenRequest):
    code = _generate_code()
    store[code] = str(req.url)
    return ShortenResponse(short_code=code)


@app.get("/{short_code}")
def redirect(short_code: str):
    url = store.get(short_code)
    if not url:
        raise HTTPException(status_code=404, detail="Not found")
    return RedirectResponse(url=url)


# --- tests (use pytest + httpx) ---
from fastapi.testclient import TestClient

client = TestClient(app)

def test_shorten_and_redirect():
    r = client.post("/shorten", json={"url": "https://example.com"})
    assert r.status_code == 200
    code = r.json()["short_code"]
    assert len(code) == 6

def test_unknown_code_returns_404():
    r = client.get("/doesnotexist", follow_redirects=False)
    assert r.status_code == 404
