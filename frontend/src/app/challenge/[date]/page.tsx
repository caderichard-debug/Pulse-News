'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import Link from 'next/link';
import { ArrowLeft, Clock, Users, Brain } from 'lucide-react';

interface ChallengeClaim {
  id: number;
  display_order: number;
  claim_text: string;
  claim_type: string;
  background_context?: string;
}

interface Challenge {
  id: number;
  week_start_date: string;
  title: string;
  description?: string;
  challenge_date: string;
  week_end_date: string;
  claims: ChallengeClaim[];
}

interface UserResponse {
  id: number;
  selected_claim_id: number;
  agreement_level: string;
  status: string;
  responded_at?: string;
}

const AGREEMENT_OPTIONS = [
  { value: 'strongly_disagree', label: 'Strongly Disagree', color: 'red' },
  { value: 'disagree', label: 'Disagree', color: 'orange' },
  { value: 'neutral', label: 'Neutral', color: 'yellow' },
  { value: 'agree', label: 'Agree', color: 'green' },
  { value: 'strongly_agree', label: 'Strongly Agree', color: 'emerald' },
];

export default function ChallengePage() {
  const params = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const date = params.date as string;

  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [userResponse, setUserResponse] = useState<UserResponse | null>(null);
  const [selectedClaim, setSelectedClaim] = useState<number | null>(null);
  const [agreementLevel, setAgreementLevel] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);
  const [canRespond, setCanRespond] = useState(true);
  const [responseReason, setResponseReason] = useState('');

  useEffect(() => {
    if (authLoading || !user) return;

    const fetchChallenge = async () => {
      try {
        setLoading(true);
        setError('');

        const response = await api.get(`/challenge/${date}`);
        const data = response.data;

        setChallenge(data.challenge);
        setUserResponse(data.user_response);
        setCanRespond(data.can_respond);
        setResponseReason(data.reason);

        // If user already responded, pre-fill the form
        if (data.user_response) {
          setSelectedClaim(data.user_response.selected_claim_id);
          setAgreementLevel(data.user_response.agreement_level);
        }
      } catch (error: any) {
        console.error('Error fetching challenge:', error);
        setError(error.response?.data?.detail || 'Failed to load challenge');
      } finally {
        setLoading(false);
      }
    };

    fetchChallenge();
  }, [date, user, authLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedClaim || !agreementLevel) {
      setError('Please select a claim and agreement level');
      return;
    }

    if (!canRespond) {
      setError(responseReason);
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await api.post(`/challenge/${date}/respond`, {
        selected_claim_id: selectedClaim,
        agreement_level: agreementLevel,
      });

      setSuccess(true);

      // Redirect to dashboard after a short delay
      setTimeout(() => {
        router.push('/dashboard');
      }, 3000);
    } catch (error: any) {
      console.error('Error submitting response:', error);
      setError(error.response?.data?.detail || 'Failed to submit response');
      setIsSubmitting(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!user) {
    router.push('/login');
    return null;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-4xl mx-auto p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-muted rounded w-1/3 mb-4"></div>
            <div className="h-4 bg-muted rounded w-2/3 mb-8"></div>
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-24 bg-muted rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !challenge) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-4xl mx-auto p-6">
          <Link href="/dashboard" className="flex items-center text-muted-foreground hover:text-foreground mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Link>

          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 text-center">
            <h2 className="text-xl font-semibold text-destructive mb-2">Challenge Not Found</h2>
            <p className="text-muted-foreground">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="max-w-md mx-auto p-6 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Brain className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-foreground mb-2">Response Recorded!</h2>
          <p className="text-muted-foreground mb-4">
            Thank you for participating in this week's challenge. You'll receive articles over the next 7 days that broaden your perspective.
          </p>
          <p className="text-sm text-muted-foreground">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  if (userResponse && userResponse.status === 'completed') {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-4xl mx-auto p-6">
          <Link href="/dashboard" className="flex items-center text-muted-foreground hover:text-foreground mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Link>

          <div className="bg-card border rounded-lg p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-2">Challenge Completed</h2>
            <p className="text-muted-foreground mb-4">
              You have already completed this week's challenge. Check your dashboard for more challenges or explore the latest articles.
            </p>
            <Link href="/dashboard" className="inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90">
              Go to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <Link href="/dashboard" className="flex items-center text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Link>

        {challenge && (
          <>
            {/* Challenge Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-8 text-white mb-8">
              <div className="flex items-center mb-4">
                <Brain className="w-8 h-8 mr-3" />
                <h1 className="text-3xl font-bold">Weekly Ethical Challenge</h1>
              </div>

              <p className="text-lg mb-4 opacity-90">
                {formatDate(challenge.challenge_date)} - {formatDate(challenge.week_end_date)}
              </p>

              <h2 className="text-xl font-semibold mb-2">{challenge.title}</h2>

              {challenge.description && (
                <p className="opacity-80 italic">{challenge.description}</p>
              )}

              <div className="flex items-center mt-6 text-sm opacity-80">
                <Clock className="w-4 h-4 mr-2" />
                <span>Respond by {formatDate(challenge.week_end_date)} to participate</span>
              </div>
            </div>

            {/* Status Messages */}
            {!canRespond && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <p className="text-yellow-800">{responseReason}</p>
              </div>
            )}

            {error && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 mb-6">
                <p className="text-destructive">{error}</p>
              </div>
            )}

            {/* Challenge Form */}
            {canRespond && (
              <form onSubmit={handleSubmit} className="space-y-8">
                {/* Claims Selection */}
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-4">
                    Select the claim that most aligns with your perspective:
                  </h3>

                  <div className="space-y-4">
                    {challenge.claims.map((claim) => (
                      <label
                        key={claim.id}
                        className={`
                          block p-6 border-2 rounded-lg cursor-pointer transition-all
                          ${selectedClaim === claim.id
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50 hover:bg-muted/50'
                          }
                        `}
                      >
                        <div className="flex items-start">
                          <input
                            type="radio"
                            name="selected_claim"
                            value={claim.id}
                            checked={selectedClaim === claim.id}
                            onChange={(e) => setSelectedClaim(parseInt(e.target.value))}
                            className="mt-1 mr-4"
                            disabled={isSubmitting}
                          />
                          <div className="flex-1">
                            <div className="flex items-center mb-2">
                              <span className="font-semibold text-lg text-primary mr-3">
                                {claim.display_order}.
                              </span>
                              <span className="text-sm px-2 py-1 bg-secondary text-secondary-foreground rounded">
                                {claim.claim_type.replace('_', ' ').title()}
                              </span>
                            </div>
                            <p className="text-foreground leading-relaxed">
                              {claim.claim_text}
                            </p>
                            {claim.background_context && (
                              <p className="text-sm text-muted-foreground mt-2 italic">
                                Context: {claim.background_context}
                              </p>
                            )}
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Agreement Level */}
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-4">
                    How strongly do you agree with your selected claim?
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                    {AGREEMENT_OPTIONS.map((option) => (
                      <label
                        key={option.value}
                        className={`
                          block p-4 border-2 rounded-lg cursor-pointer text-center transition-all
                          ${agreementLevel === option.value
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50 hover:bg-muted/50'
                          }
                        `}
                      >
                        <input
                          type="radio"
                          name="agreement_level"
                          value={option.value}
                          checked={agreementLevel === option.value}
                          onChange={(e) => setAgreementLevel(e.target.value)}
                          className="sr-only"
                          disabled={isSubmitting}
                        />
                        <div className={`font-medium ${
                          option.color === 'red' ? 'text-red-600' :
                          option.color === 'orange' ? 'text-orange-600' :
                          option.color === 'yellow' ? 'text-yellow-600' :
                          option.color === 'green' ? 'text-green-600' :
                          'text-emerald-600'
                        }`}>
                          {option.label}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Submit Button */}
                <div className="flex justify-center">
                  <button
                    type="submit"
                    disabled={!selectedClaim || !agreementLevel || isSubmitting}
                    className="px-8 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit Response'}
                  </button>
                </div>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  );
}