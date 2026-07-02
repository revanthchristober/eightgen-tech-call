"use client";

import { useState } from "react";
import { Citation } from "@/lib/types";
import { groundText } from "@/lib/numbers";

export function GroundedText({ answer, citations }: { answer: string; citations: Citation[] }) {
  const [activeFootnote, setActiveFootnote] = useState<number | null>(null);
  const { segments, citedSources } = groundText(answer, citations);

  return (
    <div>
      <p className="font-serif text-[17px] leading-relaxed text-parchment">
        {segments.map((seg, i) =>
          seg.footnoteIndex ? (
            <button
              key={i}
              onClick={() => setActiveFootnote(activeFootnote === seg.footnoteIndex ? null : seg.footnoteIndex)}
              className="font-mono decoration-brass decoration-1 underline underline-offset-4 text-brass hover:text-parchment transition-colors cursor-pointer"
            >
              {seg.text}
              <sup className="ml-0.5 text-[10px]">{seg.footnoteIndex}</sup>
            </button>
          ) : (
            <span key={i}>{seg.text}</span>
          )
        )}
      </p>

      {activeFootnote !== null && citedSources[activeFootnote - 1] && (
        <SourceTicket index={activeFootnote} citation={citedSources[activeFootnote - 1]} onClose={() => setActiveFootnote(null)} />
      )}

      {citedSources.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 border-t border-rule pt-2">
          {citedSources.map((c, i) => (
            <li key={i} className="font-mono text-[11px] text-parchment-dim">
              <sup className="text-brass">{i + 1}</sup> {c.doc_id} · p{c.page}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SourceTicket({ index, citation, onClose }: { index: number; citation: Citation; onClose: () => void }) {
  return (
    <div className="reveal mt-3 border border-brass-dim bg-panel-raised px-4 py-3 relative">
      <button
        onClick={onClose}
        aria-label="Close source"
        className="absolute top-2 right-3 text-parchment-dim hover:text-parchment font-mono text-xs cursor-pointer"
      >
        ✕
      </button>
      <div className="font-mono text-[11px] uppercase tracking-wide text-brass mb-1">
        Source {index} · {citation.doc_id} · page {citation.page}
      </div>
      <p className="font-serif italic text-sm text-parchment-dim leading-snug">&ldquo;{citation.quote}&rdquo;</p>
    </div>
  );
}
