import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import InlineIcon from "./InlineIcon";
import type { InlineIcon as IconData } from "../lib/icon";

export interface HotkeyLabels {
  hintDesktop: string;
  hintTouch: string;
  inputLabel: string;
  inputPlaceholder: string;
  submit: string;
  cancel: string;
  emptyState: string;
}

interface Note {
  id: number;
  at: string;
  text: string;
}

const MAX_NOTES = 4;

function elapsed(startedAt: number): string {
  const seconds = Math.floor((Date.now() - startedAt) / 1000);
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${pad(Math.floor(seconds / 3600))}:${pad(Math.floor(seconds / 60) % 60)}:${pad(seconds % 60)}`;
}

export default function HotkeyDemo({
  labels,
  pinIcon,
}: {
  labels: HotkeyLabels;
  pinIcon: IconData;
}) {
  const reduce = useReducedMotion();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [notes, setNotes] = useState<Note[]>([]);
  const [touch, setTouch] = useState(false);
  const started = useRef(Date.now());
  const input = useRef<HTMLInputElement>(null);
  const section = useRef<HTMLDivElement>(null);
  const inView = useRef(false);

  useEffect(() => {
    setTouch(window.matchMedia("(hover: none)").matches);
  }, []);

  // The shortcut is captured only while this section is on screen, so the page
  // never steals Ctrl+Space from an input method editor elsewhere.
  useEffect(() => {
    const node = section.current;
    if (!node || !("IntersectionObserver" in window)) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        inView.current = entry.isIntersecting;
      },
      { threshold: 0.4 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && open) {
        setOpen(false);
        setDraft("");
        return;
      }
      if (!inView.current || open) return;
      if (event.ctrlKey && event.code === "Space") {
        event.preventDefault();
        setOpen(true);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);

  const submit = useCallback(
    (event: React.FormEvent) => {
      event.preventDefault();
      const text = draft.trim();
      if (!text) return;
      setNotes((current) =>
        [...current, { id: Date.now(), at: elapsed(started.current), text }].slice(-MAX_NOTES),
      );
      setDraft("");
      setOpen(false);
    },
    [draft],
  );

  return (
    <div ref={section} className="relative">
      <div className="rounded-card border border-line bg-raised p-5 shadow-[var(--shadow)] sm:p-6">
        <div className="min-h-[132px]">
          {notes.length === 0 ? (
            <p className="py-6 text-center text-[14px] text-muted">{labels.emptyState}</p>
          ) : (
            <ul className="space-y-2">
              <AnimatePresence initial={false}>
                {notes.map((note) => (
                  <motion.li
                    key={note.id}
                    layout={!reduce}
                    initial={reduce ? false : { opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                    className="flex items-center gap-3 rounded-control bg-accent-soft px-3 py-2"
                  >
                    <span className="font-mono text-[11px] text-accent">[{note.at}]</span>
                    <InlineIcon icon={pinIcon} size={14} className="shrink-0 text-accent" />
                    <span className="truncate text-[14px] font-medium">{note.text}</span>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
          )}
        </div>

        <div className="mt-4 border-t border-line pt-4">
          {touch ? (
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="w-full rounded-control bg-accent px-4 py-2.5 text-[14px] font-medium text-accent-fg transition-transform active:translate-y-px"
            >
              {labels.hintTouch}
            </button>
          ) : (
            <p className="flex items-center justify-center gap-2 text-[13px] text-muted">
              <kbd className="rounded border border-line bg-sunken px-1.5 py-0.5 font-mono text-[11px] text-ink">
                Ctrl
              </kbd>
              <kbd className="rounded border border-line bg-sunken px-1.5 py-0.5 font-mono text-[11px] text-ink">
                Space
              </kbd>
              {labels.hintDesktop}
            </p>
          )}
        </div>
      </div>

      {/* Mirrors the desktop popup: small, near the action, dismissed with Esc. */}
      <AnimatePresence>
        {open && (
          <motion.form
            onSubmit={submit}
            initial={reduce ? false : { opacity: 0, scale: 0.97, y: 6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 420, damping: 32 }}
            className="absolute inset-x-4 bottom-4 z-10 rounded-card border border-line bg-raised p-3 shadow-[var(--shadow)] sm:inset-x-auto sm:right-6 sm:bottom-6 sm:w-[320px]"
          >
            <label
              htmlFor="latchnote-micronote"
              className="mb-1.5 block text-[11px] font-medium text-muted"
            >
              {labels.inputLabel}
            </label>
            <input
              id="latchnote-micronote"
              ref={input}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={labels.inputPlaceholder}
              maxLength={64}
              autoComplete="off"
              className="w-full rounded-control border border-line bg-bg px-3 py-2 text-[14px] text-ink placeholder:text-muted focus:border-accent focus:outline-none"
            />
            <div className="mt-2.5 flex items-center justify-between gap-3">
              <span className="text-[11px] text-muted">{labels.cancel}</span>
              <button
                type="submit"
                className="rounded-control bg-accent px-3 py-1.5 text-[13px] font-medium text-accent-fg transition-transform active:translate-y-px"
              >
                {labels.submit}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}
