"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, getResearchJob, startResearch } from "@/lib/api";
import { ResearchJob } from "@/lib/types";
import { GroundedText } from "./GroundedText";
import { StatusStamp } from "./StatusStamp";

const TERMINAL: ResearchJob["status"][] = ["done", "partial", "failed"];
const POLL_INTERVAL_MS = 1200;

export function ResearchPanel() {
  const [brief, setBrief] = useState("");
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const pollHandle = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => stopPolling(), []);

  function stopPolling() {
    if (pollHandle.current) {
      clearInterval(pollHandle.current);
      pollHandle.current = null;
    }
  }

  function pollJob(jobId: string) {
    stopPolling();
    pollHandle.current = setInterval(async () => {
      try {
        const latest = await getResearchJob(jobId);
        setJob(latest);
        if (TERMINAL.includes(latest.status)) stopPolling();
      } catch {
        stopPolling();
      }
    }, POLL_INTERVAL_MS);
  }

  async function submit() {
    const b = brief.trim();
    if (!b || submitting) return;
    setSubmitting(true);
    setSubmitError(null);
    setJob(null);
    try {
      const created = await startResearch(b);
      setJob(created);
      pollJob(created.job_id);
    } catch (e) {
      setSubmitError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  const pct =
    job && job.sub_questions_total > 0
      ? Math.round((job.sub_questions_done / job.sub_questions_total) * 100)
      : 0;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <label className="block font-mono text-[11px] uppercase tracking-[0.12em] text-parchment-dim mb-2">
          Research brief
        </label>
        <textarea
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          rows={3}
          placeholder="Compare the profitability and growth of Northbridge Bank vs Solstice Retail over the last two years and give me a view."
          className="w-full bg-panel border border-rule px-4 py-3 font-serif text-[16px] text-parchment placeholder:text-parchment-dim/60 focus:outline-none focus:border-brass resize-y"
        />
        <button
          onClick={submit}
          disabled={submitting || !brief.trim()}
          className="mt-3 border border-brass text-brass font-mono text-[12px] uppercase tracking-wide px-5 py-2 hover:bg-brass hover:text-ink transition-colors disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-brass cursor-pointer disabled:cursor-default"
        >
          Commission research
        </button>
        {submitError && <p className="mt-2 font-mono text-[13px] text-rust">{submitError}</p>}
      </div>

      {job && (
        <div className="border-t border-rule pt-6">
          <div className="flex items-center gap-3 mb-1">
            <StatusStamp status={job.status} />
            <span className="font-mono text-[11px] text-parchment-dim">job {job.job_id}</span>
          </div>
          <p className="font-serif italic text-[14px] text-parchment-dim mb-2">{job.progress}</p>
          <div className="h-[3px] bg-panel-raised mb-6">
            <div className="h-full bg-brass transition-all duration-300" style={{ width: `${pct}%` }} />
          </div>
          {job.error && <p className="font-mono text-[13px] text-rust mb-4">{job.error}</p>}
          {job.report && <Report report={job.report} />}
        </div>
      )}
    </div>
  );
}

function Report({ report }: { report: NonNullable<ResearchJob["report"]> }) {
  return (
    <div className="space-y-8">
      <Section title="Summary">
        <p className="font-serif text-[17px] leading-relaxed">{report.summary}</p>
      </Section>

      <Section title="Comparison">
        {report.comparison_table.length > 0 ? (
          <table className="w-full font-mono text-[13px]">
            <thead>
              <tr className="text-left text-parchment-dim uppercase text-[10px] tracking-wide">
                <th className="font-normal pb-2 pr-4">Metric</th>
                <th className="font-normal pb-2 pr-4">Company</th>
                <th className="font-normal pb-2 pr-4">Period</th>
                <th className="font-normal pb-2 pr-4">Value</th>
                <th className="font-normal pb-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {report.comparison_table.map((row, i) => (
                <tr key={i} className="border-t border-rule">
                  <td className="py-2 pr-4">{row.metric}</td>
                  <td className="py-2 pr-4">{row.company}</td>
                  <td className="py-2 pr-4">{row.period}</td>
                  <td className="py-2 pr-4 tabular-nums text-brass">{row.value}</td>
                  <td className="py-2 text-parchment-dim">
                    {row.citation.doc_id} · p{row.citation.page}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="font-serif italic text-parchment-dim">No verified comparison rows.</p>
        )}
        {report.dropped_unverified_rows > 0 && (
          <p className="mt-2 font-mono text-[11px] text-rust-dim">
            {report.dropped_unverified_rows} row(s) withheld — failed citation verification.
          </p>
        )}
      </Section>

      <Section title="Trends">
        <p className="font-serif text-[16px] leading-relaxed text-parchment-dim">{report.trends}</p>
      </Section>

      <Section title="Risks">
        <p className="font-serif text-[16px] leading-relaxed text-parchment-dim">{report.risks}</p>
      </Section>

      <Section title="Conclusion">
        <p className="font-serif text-[17px] leading-relaxed">{report.conclusion}</p>
      </Section>

      <Section title="Sub-questions">
        <div className="space-y-5">
          {report.sub_results.map((sr, i) => (
            <div key={i} className="border-l-2 border-rule pl-4">
              <p className="font-mono text-[12px] text-parchment-dim mb-1">{sr.sub_question}</p>
              {sr.answer ? (
                <GroundedText answer={sr.answer.answer} citations={sr.answer.citations} />
              ) : (
                <p className="font-mono text-[12px] text-rust">Failed: {sr.error}</p>
              )}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h3 className="font-mono text-[11px] uppercase tracking-[0.12em] text-brass mb-2">{title}</h3>
      {children}
    </section>
  );
}
