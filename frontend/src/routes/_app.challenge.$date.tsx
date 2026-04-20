import { createFileRoute, useParams } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { Calendar, Check } from "lucide-react";

type Claim = {
  id: string | number;
  text: string;
  is_true?: boolean;
};

type Challenge = {
  id?: string | number;
  date?: string;
  title?: string;
  intro?: string;
  claims?: Claim[];
};

export const Route = createFileRoute("/_app/challenge/$date")({
  head: () => ({ meta: [{ title: "Weekly challenge — Pulse" }] }),
  component: ChallengePage,
});

function ChallengePage() {
  const { date } = useParams({ from: "/_app/challenge/$date" });
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [responses, setResponses] = useState<Record<string, boolean>>({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<Challenge>(`/challenge/${date}`)
      .then(setChallenge)
      .catch(() => setChallenge(null))
      .finally(() => setLoading(false));
  }, [date]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!challenge?.id) return;
    try {
      await api(`/challenge/${challenge.id}/responses`, {
        method: "POST",
        body: { responses },
      });
      setSubmitted(true);
      toast.success("Answers submitted");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not submit");
    }
  }

  if (loading) {
    return <div className="max-w-[760px] mx-auto px-6 py-16 text-muted-foreground">Loading challenge…</div>;
  }
  if (!challenge) {
    return (
      <div className="max-w-[760px] mx-auto px-6 py-16 text-center">
        <h1 className="font-serif text-3xl font-medium">No challenge for {date}</h1>
        <p className="mt-3 text-muted-foreground">Check back next week.</p>
      </div>
    );
  }

  return (
    <div className="max-w-[760px] mx-auto px-6 py-12">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">
        <Calendar className="size-3.5" /> Week of {challenge.date || date}
      </div>
      <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight leading-tight text-balance">
        {challenge.title || "Weekly news challenge"}
      </h1>
      {challenge.intro && (
        <p className="mt-4 text-lg text-muted-foreground leading-relaxed">{challenge.intro}</p>
      )}

      <form onSubmit={onSubmit} className="mt-12 space-y-6">
        {(challenge.claims || []).map((c) => (
          <fieldset key={c.id} className="border border-border rounded-lg p-5">
            <legend className="px-2 text-xs uppercase tracking-wider text-muted-foreground">
              Claim
            </legend>
            <p className="font-serif text-xl font-medium mb-4">{c.text}</p>
            <div className="flex gap-3">
              {([
                { v: true, label: "True" },
                { v: false, label: "False" },
              ] as const).map((opt) => {
                const selected = responses[String(c.id)] === opt.v;
                return (
                  <button
                    type="button"
                    key={String(opt.v)}
                    onClick={() =>
                      setResponses((prev) => ({ ...prev, [String(c.id)]: opt.v }))
                    }
                    className={`flex-1 py-2.5 rounded-md border transition-colors ${
                      selected
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-border hover:bg-accent"
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
            {submitted && c.is_true !== undefined && (
              <p
                className={`mt-3 text-sm ${
                  responses[String(c.id)] === c.is_true ? "text-sent-pos" : "text-sent-neg"
                }`}
              >
                <Check className="inline size-4 mr-1" />
                Correct answer: {c.is_true ? "True" : "False"}
              </p>
            )}
          </fieldset>
        ))}
        {!submitted && (challenge.claims?.length ?? 0) > 0 && (
          <button className="px-5 py-3 rounded-md bg-primary text-primary-foreground font-medium">
            Submit answers
          </button>
        )}
      </form>
    </div>
  );
}
