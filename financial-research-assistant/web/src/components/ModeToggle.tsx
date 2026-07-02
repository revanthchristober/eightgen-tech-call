"use client";

export type Mode = "ask" | "research";

export function ModeToggle({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  return (
    <div className="inline-flex border border-rule">
      {(
        [
          ["ask", "Ask"],
          ["research", "Deep Research"],
        ] as const
      ).map(([value, label]) => (
        <button
          key={value}
          onClick={() => onChange(value)}
          className={`px-5 py-2 font-mono text-[12px] uppercase tracking-wide cursor-pointer transition-colors ${
            mode === value ? "bg-brass text-ink" : "text-parchment-dim hover:text-parchment"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
