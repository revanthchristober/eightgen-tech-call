"use client";

import { useState } from "react";
import { ModeToggle, Mode } from "@/components/ModeToggle";
import { ChatPanel } from "@/components/ChatPanel";
import { ResearchPanel } from "@/components/ResearchPanel";

export default function Home() {
  const [mode, setMode] = useState<Mode>("ask");

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-rule px-8 py-6">
        <div className="max-w-5xl mx-auto flex items-baseline justify-between gap-6 flex-wrap">
          <div>
            <h1 className="font-display text-[26px] tracking-tight text-parchment">The Research Desk</h1>
            <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-parchment-dim mt-1">
              Grounded &amp; cited — every figure verified against the source
            </p>
          </div>
          <ModeToggle mode={mode} onChange={setMode} />
        </div>
      </header>

      <main className="flex-1 px-8 py-10">
        {mode === "ask" ? <ChatPanel /> : <ResearchPanel />}
      </main>
    </div>
  );
}
