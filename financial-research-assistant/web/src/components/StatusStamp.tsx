import { JobStatus } from "@/lib/types";

const LABEL: Record<JobStatus, string> = {
  pending: "Queued",
  running: "In Progress",
  partial: "Partial",
  done: "Verified",
  failed: "Failed",
};

const STYLE: Record<JobStatus, string> = {
  pending: "border-parchment-dim text-parchment-dim",
  running: "border-brass text-brass",
  partial: "border-brass text-brass",
  done: "border-brass text-brass",
  failed: "border-rust text-rust",
};

export function StatusStamp({ status }: { status: JobStatus }) {
  return (
    <span
      className={`inline-block font-mono text-[11px] uppercase tracking-[0.12em] border px-2 py-0.5 -rotate-1 ${STYLE[status]}`}
    >
      {LABEL[status]}
    </span>
  );
}
