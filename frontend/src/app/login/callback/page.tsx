'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

export default function LoginCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('token');
    const newUser = searchParams.get('new_user');
    const error = searchParams.get('error');

    if (error) {
      // Handle OAuth error
      router.replace('/login?error=oauth_failed');
      return;
    }

    if (token) {
      // Save token from OAuth callback
      api.setToken(token);
      localStorage.setItem('access_token', token);

      // Redirect to feed
      router.push('/feed');
    } else {
      // No token found, redirect to login
      router.replace('/login');
    }
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 dark:from-gray-900 to-indigo-100 dark:to-gray-800 transition-colors flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-300">Completing sign in...</p>
      </div>
    </div>
  );
}