import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import InlineIcon from "./InlineIcon";
import type { InlineIcon as IconData } from "../lib/icon";

export interface WaitlistLabels {
  pollQuestion: string;
  pollOptions: string[];
  emailLabel: string;
  emailPlaceholder: string;
  emailHelp: string;
  submit: string;
  submitting: string;
  success: string;
  errorGeneric: string;
  errorEmail: string;
  errorPoll: string;
  privacy: string;
  unconfigured: string;
}

type Status = "idle" | "submitting" | "success" | "error";

const ENDPOINT = import.meta.env.PUBLIC_WAITLIST_ENDPOINT as string | undefined;
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export interface WaitlistIcons {
  check: IconData;
  spinner: IconData;
}

export default function WaitlistForm({
  labels,
  icons,
}: {
  labels: WaitlistLabels;
  icons: WaitlistIcons;
}) {
  const reduce = useReducedMotion();
  const [email, setEmail] = useState("");
  const [choice, setChoice] = useState<number | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  const configured = Boolean(ENDPOINT);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (status === "submitting") return;

    if (!EMAIL.test(email.trim())) {
      setStatus("error");
      setMessage(labels.errorEmail);
      return;
    }
    if (choice === null) {
      setStatus("error");
      setMessage(labels.errorPoll);
      return;
    }
    if (!configured) {
      setStatus("error");
      setMessage(labels.unconfigured);
      return;
    }

    setStatus("submitting");
    setMessage("");

    try {
      const response = await fetch(ENDPOINT as string, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          pricing_preference: labels.pollOptions[choice],
          language: document.documentElement.lang,
        }),
      });
      if (!response.ok) throw new Error(`Request failed with ${response.status}`);
      setStatus("success");
    } catch {
      setStatus("error");
      setMessage(labels.errorGeneric);
    }
  }

  if (status === "success") {
    return (
      <motion.div
        initial={reduce ? false : { opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start gap-3 rounded-card border border-line bg-raised p-6 shadow-[var(--shadow)]"
        role="status"
      >
        <InlineIcon icon={icons.check} size={22} className="mt-px shrink-0 text-accent" />
        <p className="text-[15px] leading-relaxed">{labels.success}</p>
      </motion.div>
    );
  }

  return (
    <form
      onSubmit={submit}
      noValidate
      className="rounded-card border border-line bg-raised p-5 shadow-[var(--shadow)] sm:p-7"
    >
      <fieldset>
        <legend className="mb-3 text-[15px] font-medium">{labels.pollQuestion}</legend>
        <div className="grid gap-2">
          {labels.pollOptions.map((option, index) => {
            const active = choice === index;
            return (
              <label
                key={option}
                className={`flex cursor-pointer items-start gap-3 rounded-control border px-3.5 py-3 text-[14px] leading-snug transition-colors ${
                  active ? "border-accent bg-accent-soft" : "border-line hover:bg-sunken"
                }`}
              >
                <input
                  type="radio"
                  name="pricing-preference"
                  value={option}
                  checked={active}
                  onChange={() => setChoice(index)}
                  className="mt-0.5 size-4 shrink-0 accent-[var(--accent)]"
                />
                <span>{option}</span>
              </label>
            );
          })}
        </div>
      </fieldset>

      <div className="mt-6 grid gap-2">
        <label htmlFor="waitlist-email" className="text-[13px] font-medium">
          {labels.emailLabel}
        </label>
        <input
          id="waitlist-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder={labels.emailPlaceholder}
          autoComplete="email"
          aria-describedby="waitlist-help"
          className="w-full rounded-control border border-line bg-bg px-3.5 py-2.5 text-[15px] text-ink placeholder:text-muted focus:border-accent focus:outline-none"
        />
        <p id="waitlist-help" className="text-[12px] text-muted">
          {labels.emailHelp}
        </p>
      </div>

      <button
        type="submit"
        disabled={status === "submitting"}
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-control bg-accent px-5 py-3 text-[15px] font-medium whitespace-nowrap text-accent-fg transition-transform hover:bg-accent-strong active:translate-y-px disabled:opacity-70"
      >
        {status === "submitting" && (
          <InlineIcon icon={icons.spinner} size={16} className="animate-spin" />
        )}
        {status === "submitting" ? labels.submitting : labels.submit}
      </button>

      <AnimatePresence>
        {status === "error" && message && (
          <motion.p
            initial={reduce ? false : { opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            role="alert"
            className="mt-3 text-[13px] text-accent"
          >
            {message}
          </motion.p>
        )}
      </AnimatePresence>

      <p className="mt-4 text-center text-[12px] text-muted">{labels.privacy}</p>
    </form>
  );
}
