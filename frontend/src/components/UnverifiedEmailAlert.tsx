'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function UnverifiedEmailAlert() {
  const [showAlert, setShowAlert] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;

    api.getCurrentUser()
      .then((user) => {
        if (mounted && user) {
          // Show alert only if email is not verified
          setShowAlert(user.email_verified === false);
        }
      })
      .catch(() => {
        // If there's an error fetching user, don't show the alert
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, []);

  // Don't render anything while loading or if alert shouldn't be shown
  if (loading || !showAlert) {
    return null;
  }

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
  <div className="max-w-7xl mx-auto flex justify-center">
    <div className="flex items-center space-x-2 text-center whitespace-nowrap">
      <svg
        className="h-5 w-5 text-yellow-400 flex-shrink-0"
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
      <p className="text-sm text-yellow-700">
        <span className="font-medium">Email not verified.</span> You won&apos;t receive newsletters until you verify your email address. Please check your inbox for a verification link.
      </p>
    </div>
  </div>
</div>

  );
}
