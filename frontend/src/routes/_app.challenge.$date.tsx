import { createFileRoute, useParams } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { Calendar, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

type Claim = {
  id: string | number;
  claim_text: string;
  is_true?: boolean;
};

type Challenge = {
  id?: string | number;
  week_start_date?: string;
  title?: string;
  description?: string;
  claims?: Claim[];
};

type ChallengePayload = {
  challenge?: Challenge;
  can_respond?: boolean;
  reason?: string;
};

type AgreementLevel = "agree" | "disagree";

export const Route = createFileRoute("/_app/challenge/$date")({
  head: () => ({ meta: [{ title: "Weekly challenge — Pulse" }] }),
  component: ChallengePage,
});

function ChallengePage() {
  const { date } = useParams({ from: "/_app/challenge/$date" });
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [canRespond, setCanRespond] = useState(true);
  const [responseReason, setResponseReason] = useState<string | null>(null);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [agreementLevel, setAgreementLevel] = useState<AgreementLevel | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api<ChallengePayload>(`/challenge/${date}`)
      .then((payload) => {
        setChallenge(payload.challenge ?? null);
        setCanRespond(payload.can_respond ?? true);
        setResponseReason(payload.reason ?? null);
      })
      .catch(() => {
        setChallenge(null);
        setCanRespond(false);
        setResponseReason(null);
      })
      .finally(() => setLoading(false));
  }, [date]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedClaimId || !agreementLevel) {
      toast.error("Select a claim and whether you agree or disagree");
      return;
    }
    try {
      await api(`/challenge/${date}/respond`, {
        method: "POST",
        body: {
          selected_claim_id: Number(selectedClaimId),
          agreement_level: agreementLevel,
        },
      });
      setSubmitted(true);
      toast.success("Answers submitted");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not submit");
    }
  }

  if (loading) {
    return (
      <div className="max-w-[760px] mx-auto px-6 py-16 text-muted-foreground">
        Loading challenge…
      </div>
    );
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
        <Calendar className="size-3.5" /> Week of {challenge.week_start_date || date}
      </div>
      <h1 className="font-serif text-4xl md:text-5xl font-medium tracking-tight leading-tight text-balance">
        {challenge.title || "Weekly news challenge"}
      </h1>
      {challenge.description && (
        <p className="mt-4 text-lg text-muted-foreground leading-relaxed">
          {challenge.description}
        </p>
      )}

      <form onSubmit={onSubmit} className="mt-12 space-y-6">
        {(challenge.claims || []).map((c) => (
          <fieldset key={c.id} className="border border-border rounded-lg p-5">
            <legend className="px-2 text-xs uppercase tracking-wider text-muted-foreground">
              Claim
            </legend>
            <p className="font-serif text-xl font-medium mb-4">{c.claim_text}</p>
            <div className="flex gap-3">
              <Button
                type="button"
                onClick={() => {
                  setSelectedClaimId(String(c.id));
                  setAgreementLevel("agree");
                }}
                variant="outline"
                className={`flex-1 py-2.5 rounded-md border transition-colors ${
                  selectedClaimId === String(c.id) && agreementLevel === "agree"
                    ? "bg-accent border-foreground text-foreground"
                    : ""
                }`}
                aria-pressed={selectedClaimId === String(c.id) && agreementLevel === "agree"}
              >
                I agree
              </Button>
              <Button
                type="button"
                onClick={() => {
                  setSelectedClaimId(String(c.id));
                  setAgreementLevel("disagree");
                }}
                variant="outline"
                className={`flex-1 py-2.5 rounded-md border transition-colors ${
                  selectedClaimId === String(c.id) && agreementLevel === "disagree"
                    ? "bg-accent border-foreground text-foreground"
                    : ""
                }`}
                aria-pressed={selectedClaimId === String(c.id) && agreementLevel === "disagree"}
              >
                I disagree
              </Button>
            </div>
            {submitted && selectedClaimId === String(c.id) && (
              <p className="mt-3 text-sm text-sent-pos">
                <Check className="inline size-4 mr-1" />
                Your response has been recorded.
              </p>
            )}
          </fieldset>
        ))}
        {!submitted && canRespond && (challenge.claims?.length ?? 0) > 0 && (
          <Button className="h-11 px-5">Submit answers</Button>
        )}
        {!canRespond && (
          <p className="text-sm text-muted-foreground">
            {responseReason || "You cannot respond to this challenge right now."}
          </p>
        )}
      </form>
    </div>
  );
}
