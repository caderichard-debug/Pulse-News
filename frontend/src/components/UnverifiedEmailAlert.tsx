'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function UnverifiedEmailAlert() {
  const [showAlert, setShowAlert] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [resending, setResending] = useState<boolean>(false);
  const [resendMessage, setResendMessage] = useState<string>('');

  useEffect(() => {
    let mounted = true;

    api.getCurrentUser()
      .then((user) => {
        if (mounted) {
          // Show alert only if email is not verified
          setShowAlert(user ? user.email_verified === false : false);
          setLoading(false);
        }
      })
      .catch(() => {
        // If there's an error fetching user, don't show the alert
        if (mounted) {
          setLoading(false);
        }
      });

    return () => { mounted = false; };
  }, []);

  const handleResendEmail = async () => {
    setResending(true);
    setResendMessage('');

    try {
      const response = await api.resendVerificationEmail();
      setResendMessage(response.message || 'Verification email sent! Please check your inbox.');
    } catch (err) {
      setResendMessage(err instanceof Error ? err.message : 'Failed to send verification email.');
    } finally {
      setResending(false);
    }
  };

  // Don't render anything while loading or if alert shouldn't be shown
  if (loading || !showAlert) {
    return null;
  }

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 dark:border-yellow-600 p-4 transition-colors">
      <div className="max-w-7xl mx-auto flex justify-center">
        <div className="flex items-center space-x-3 text-center">
          <svg
            className="h-5 w-5 text-yellow-400 dark:text-yellow-500 flex-shrink-0"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          <div className="flex-1">
            <p className="text-sm text-yellow-700 dark:text-yellow-300">
              <span className="font-medium">Email not verified.</span> You won&apos;t receive newsletters until you verify your email address. Please check your inbox for a verification link.
            </p>
            {resendMessage && (
              <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">{resendMessage}</p>
            )}
          </div>
          <button
            onClick={handleResendEmail}
            disabled={resending}
            className="px-3 py-1.5 text-xs font-medium text-yellow-800 dark:text-yellow-200 bg-yellow-100 dark:bg-yellow-800/50 hover:bg-yellow-200 dark:hover:bg-yellow-800/70 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {resending ? 'Sending...' : 'Resend Email'}
          </button>
        </div>
      </div>
    </div>
  );
}
