"use client";

import { useState } from "react";
import { askChat, ApiError } from "@/lib/api";
import { ChatAnswer } from "@/lib/types";
import { GroundedText } from "./GroundedText";

interface Exchange {
  question: string;
  answer?: ChatAnswer;
  error?: string;
}

export function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [exchanges, setExchanges] = useState<Exchange[]>([]);

  async function submit() {
    const q = question.trim();
    if (!q || loading) return;
    setLoading(true);
    setQuestion("");
    setExchanges((prev) => [...prev, { question: q }]);
    try {
      const answer = await askChat(q);
      setExchanges((prev) => prev.map((e, i) => (i === prev.length - 1 ? { ...e, answer } : e)));
    } catch (e) {
      const message = e instanceof ApiError ? e.message : String(e);
      setExchanges((prev) => prev.map((e, i) => (i === prev.length - 1 ? { ...e, error: message } : e)));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <label className="block font-mono text-[11px] uppercase tracking-[0.12em] text-parchment-dim mb-2">
          Query the corpus
        </label>
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="What was Northbridge Bank's NIM in Q4FY24 vs Q4FY23?"
            className="flex-1 bg-panel border border-rule px-4 py-3 font-serif text-[16px] text-parchment placeholder:text-parchment-dim/60 focus:outline-none focus:border-brass"
          />
          <button
            onClick={submit}
            disabled={loading || !question.trim()}
            className="shrink-0 border border-brass text-brass font-mono text-[12px] uppercase tracking-wide px-5 hover:bg-brass hover:text-ink transition-colors disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-brass cursor-pointer disabled:cursor-default"
          >
            Ask
          </button>
        </div>
      </div>

      <div className="space-y-8">
        {exchanges
          .slice()
          .reverse()
          .map((ex, i) => (
            <article key={i} className="border-t border-rule pt-5">
              <h3 className="font-display text-[20px] text-parchment mb-3">{ex.question}</h3>
              {ex.error && (
                <p className="font-mono text-[13px] text-rust border-l-2 border-rust pl-3">
                  Request failed: {ex.error}
                </p>
              )}
              {ex.answer?.insufficient_data && (
                <p className="font-mono text-[13px] text-rust-dim border-l-2 border-rust pl-3">
                  {ex.answer.answer || "Not found in the ingested corpus."}
                </p>
              )}
              {ex.answer && !ex.answer.insufficient_data && (
                <GroundedText answer={ex.answer.answer} citations={ex.answer.citations} />
              )}
              {!ex.answer && !ex.error && (
                <p className="font-serif italic text-[15px] text-parchment-dim">Consulting the corpus…</p>
              )}
            </article>
          ))}
      </div>
    </div>
  );
}
