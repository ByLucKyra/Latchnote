import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import InlineIcon from "./InlineIcon";
import type { InlineIcon as IconData } from "../lib/icon";

export interface DemoLabels {
  sessionTitle: string;
  recording: string;
  finished: string;
  transcript: string;
  structured: string;
  manual: string;
  replay: string;
}

type Entry =
  | { kind: "transcript"; at: string; text: string }
  | { kind: "structured"; at: string; bullets: string[] }
  | { kind: "manual"; at: string; text: string };

/** Course content stays identical in both languages: it is the lecture, not the UI. */
const SCRIPT: Entry[] = [
  {
    kind: "transcript",
    at: "00:12:04",
    text: "Kalau kita buka koneksi baru tiap request, cost-nya mahal banget. That is exactly what connection pooling solves.",
  },
  {
    kind: "structured",
    at: "00:12:40",
    bullets: [
      "Connection pooling reuses open database connections instead of opening one per request",
      "Default pool size in the example is 10, raised through max_overflow",
      "Pool exhaustion shows up as latency, not as an error",
    ],
  },
  {
    kind: "transcript",
    at: "00:13:22",
    text: "Pool size default-nya sepuluh di contoh ini, dan bisa kamu naikin lewat max_overflow.",
  },
  { kind: "manual", at: "00:14:05", text: "cek pool_size default" },
];

const WORD_MS = 55;
const GAP_MS = 700;

export interface DemoIcons {
  pin: IconData;
  replay: IconData;
}

export default function LiveSessionDemo({
  labels,
  icons,
}: {
  labels: DemoLabels;
  icons: DemoIcons;
}) {
  const reduce = useReducedMotion();
  const [step, setStep] = useState(0);
  const [words, setWords] = useState(0);
  const [runId, setRunId] = useState(0);
  const scroller = useRef<HTMLDivElement>(null);

  const done = step >= SCRIPT.length;
  const current = done ? null : SCRIPT[step];

  // Reduced motion gets the finished note straight away, with no timers at all.
  useEffect(() => {
    if (reduce) setStep(SCRIPT.length);
  }, [reduce]);

  useEffect(() => {
    if (reduce || done || !current) return;

    if (current.kind !== "transcript") {
      const timer = window.setTimeout(() => setStep((value) => value + 1), GAP_MS);
      return () => window.clearTimeout(timer);
    }

    const total = current.text.split(" ").length;
    if (words >= total) {
      const timer = window.setTimeout(() => {
        setStep((value) => value + 1);
        setWords(0);
      }, GAP_MS);
      return () => window.clearTimeout(timer);
    }

    const timer = window.setTimeout(() => setWords((value) => value + 1), WORD_MS);
    return () => window.clearTimeout(timer);
  }, [reduce, done, current, words, runId]);

  useEffect(() => {
    const node = scroller.current;
    if (!node) return;
    node.scrollTo({ top: node.scrollHeight, behavior: reduce ? "auto" : "smooth" });
  }, [step, words, reduce]);

  const replay = useCallback(() => {
    setStep(0);
    setWords(0);
    setRunId((value) => value + 1);
  }, []);

  const settled = SCRIPT.slice(0, step);

  return (
    <div className="overflow-hidden rounded-card border border-line bg-raised shadow-[var(--shadow)]">
      <div className="flex items-center gap-3 border-b border-line px-4 py-3">
        <span className="truncate font-mono text-[12px] text-muted">
          {labels.sessionTitle}
        </span>
        <span className="ml-auto flex shrink-0 items-center gap-2 text-[12px] text-muted">
          {done ? (
            labels.finished
          ) : (
            <>
              <span
                className={`size-1.5 rounded-full bg-accent ${reduce ? "" : "animate-pulse"}`}
                aria-hidden="true"
              />
              {labels.recording}
            </>
          )}
        </span>
      </div>

      <div
        ref={scroller}
        className="h-[352px] overflow-y-auto px-4 py-4 sm:h-[392px]"
        aria-live="polite"
        aria-atomic="false"
      >
        <ul className="space-y-5">
          {settled.map((entry, index) => (
            <EntryBlock
              key={`${runId}-${index}`}
              entry={entry}
              labels={labels}
              icons={icons}
              reduce={!!reduce}
            />
          ))}

          {current?.kind === "transcript" && words > 0 && (
            <EntryBlock
              key={`${runId}-live`}
              entry={{ ...current, text: current.text.split(" ").slice(0, words).join(" ") }}
              labels={labels}
              icons={icons}
              reduce={!!reduce}
              live
            />
          )}
        </ul>
      </div>

      <div className="flex items-center justify-between border-t border-line px-4 py-2.5">
        <span className="font-mono text-[11px] text-muted">2026-08-29_Backend Fundamentals.md</span>
        <AnimatePresence>
          {done && (
            <motion.button
              type="button"
              onClick={replay}
              initial={reduce ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-1.5 rounded-control px-2 py-1 text-[12px] text-muted transition-colors hover:bg-sunken hover:text-ink"
            >
              <InlineIcon icon={icons.replay} size={13} />
              {labels.replay}
            </motion.button>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function EntryBlock({
  entry,
  labels,
  icons,
  reduce,
  live = false,
}: {
  entry: Entry;
  labels: DemoLabels;
  icons: DemoIcons;
  reduce: boolean;
  live?: boolean;
}) {
  const label =
    entry.kind === "structured"
      ? labels.structured
      : entry.kind === "manual"
        ? labels.manual
        : labels.transcript;

  return (
    <motion.li
      initial={reduce ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="mb-1.5 flex items-baseline gap-2.5">
        <span className="font-mono text-[11px] text-accent">[{entry.at}]</span>
        <span className="text-[11px] text-muted">{label}</span>
      </div>

      {entry.kind === "transcript" && (
        <p className="text-[14px] leading-relaxed text-ink/90">
          {entry.text}
          {live && <span className="ml-0.5 inline-block h-[1em] w-[2px] translate-y-[2px] bg-accent" />}
        </p>
      )}

      {entry.kind === "structured" && (
        <ul className="space-y-1.5">
          {entry.bullets.map((bullet) => (
            <li key={bullet} className="flex gap-2.5 text-[14px] leading-relaxed text-ink/90">
              <span className="mt-[9px] size-[3px] shrink-0 rounded-full bg-muted" aria-hidden="true" />
              {bullet}
            </li>
          ))}
        </ul>
      )}

      {entry.kind === "manual" && (
        <p className="flex items-center gap-2 rounded-control bg-accent-soft px-2.5 py-1.5 text-[14px] font-medium">
          <InlineIcon icon={icons.pin} size={14} className="shrink-0 text-accent" />
          {entry.text}
        </p>
      )}
    </motion.li>
  );
}
