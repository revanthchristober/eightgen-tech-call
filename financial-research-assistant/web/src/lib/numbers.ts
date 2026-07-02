import { Citation } from "./types";

// Mirrors chat.py's NUMBER_PATTERN so the client can highlight exactly the
// figures the backend already verified verbatim against a source chunk.
const NUMBER_PATTERN =
  /[₹$]\(?-?[\d,]+(?:\.\d+)?\)?(?:\s?(?:crore|million|billion|bn|mn))?|\d+(?:\.\d+)?\s?(?:basis points|bps)|-?\(?\d[\d,]*(?:\.\d+)?\)?%|\d+(?:\.\d+)?x\b/g;

export interface TextSegment {
  text: string;
  citation: Citation | null;
  footnoteIndex: number | null;
}

export interface GroundedResult {
  segments: TextSegment[];
  citedSources: Citation[];
}

export function groundText(answer: string, citations: Citation[]): GroundedResult {
  const citedSources: Citation[] = [];
  const footnoteOf = new Map<string, number>();

  const segments: TextSegment[] = [];
  let lastIndex = 0;

  for (const match of answer.matchAll(NUMBER_PATTERN)) {
    const value = match[0];
    const index = match.index ?? 0;
    const source = citations.find((c) => c.quote.includes(value));

    if (index > lastIndex) {
      segments.push({ text: answer.slice(lastIndex, index), citation: null, footnoteIndex: null });
    }

    if (source) {
      const key = `${source.doc_id}:${source.page}`;
      let footnoteIndex = footnoteOf.get(key);
      if (footnoteIndex === undefined) {
        citedSources.push(source);
        footnoteIndex = citedSources.length;
        footnoteOf.set(key, footnoteIndex);
      }
      segments.push({ text: value, citation: source, footnoteIndex });
    } else {
      segments.push({ text: value, citation: null, footnoteIndex: null });
    }

    lastIndex = index + value.length;
  }

  if (lastIndex < answer.length) {
    segments.push({ text: answer.slice(lastIndex), citation: null, footnoteIndex: null });
  }

  return { segments, citedSources };
}
