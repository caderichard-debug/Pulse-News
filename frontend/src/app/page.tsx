'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in and redirect to feed
    api.getCurrentUser()
      .then(user => {
        if (user && user.id) {
          router.push('/feed'); // logged-in → feed
        }
      })
      .catch(err => {
      if (err.status === 403 || err.message === 'Not authenticated') {
        // not logged in → stay on landing page (no need to log)
        // Silently handle - this is expected behavior
      } else {
        console.error(err);
      }
    });
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="max-w-6xl mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-gray-900 mb-4">
            ⚡ <span className="text-indigo-600">Pulse</span>
          </h1>
          <p className="text-2xl text-gray-600 mb-8">
            News aggregation with ethical clarity
          </p>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-12">
            Get AI-powered summaries, bias detection, and unique framework analysis
            that maps articles to underlying ethical debates. Delivered daily to
            your inbox.
          </p>

          <div className="flex gap-4 justify-center">
            <a
              href="/signup"
              className="px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-semibold text-lg"
            >
              Get Started
            </a>
            <a
              href="/login"
              className="px-8 py-3 bg-white text-indigo-600 border-2 border-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-semibold text-lg"
            >
              Log In
            </a>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              AI Summaries
            </h3>
            <p className="text-gray-600">
              Concise 100-word summaries of top articles, saving you time while
              keeping you informed.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-4xl mb-4">⚖️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Bias Detection
            </h3>
            <p className="text-gray-600">
              Sentiment analysis and political lean detection helps you understand
              different perspectives.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Framework Mapping
            </h3>
            <p className="text-gray-600">
              Our unique feature: articles mapped to ethical debates like &quot;Privacy
              vs. Security&quot; to see the bigger picture.
            </p>
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            How It Works
          </h2>

          <div className="space-y-6">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                1
              </div>
              <div>
                <h3 className="font-semibold text-lg text-gray-900 mb-1">
                  Choose Your Topics
                </h3>
                <p className="text-gray-600">
                  Select from Politics, Economics, Technology, Culture, and more.
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                2
              </div>
              <div>
                <h3 className="font-semibold text-lg text-gray-900 mb-1">
                  We Aggregate & Analyze
                </h3>
                <p className="text-gray-600">
                  Our AI scrapes trusted sources, extracts articles, generates
                  summaries, and maps them to ethical frameworks.
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                3
              </div>
              <div>
                <h3 className="font-semibold text-lg text-gray-900 mb-1">
                  Daily Newsletter Delivered
                </h3>
                <p className="text-gray-600">
                  Receive your personalized digest at 7 AM every day with the
                  articles and frameworks most relevant to you.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Trusted Sources */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Trusted Sources
          </h2>
          <div className="flex flex-wrap justify-center gap-6 text-gray-600">
            <span>AP News</span>
            <span>•</span>
            <span>Reuters</span>
            <span>•</span>
            <span>NPR</span>
            <span>•</span>
            <span>BBC</span>
            <span>•</span>
            <span>NYT</span>
            <span>•</span>
            <span>The Atlantic</span>
            <span>•</span>
            <span>Ars Technica</span>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-16 text-center bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow-xl p-12 text-white">
          <h2 className="text-3xl font-bold mb-4">
            Start Your Free Newsletter Today
          </h2>
          <p className="text-xl mb-8 text-indigo-100">
            Join readers who value clarity and depth in their news
          </p>
          <a
            href="/signup"
            className="inline-block px-8 py-3 bg-white text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-semibold text-lg"
          >
            Sign Up Now
          </a>
        </div>
      </div>
    </div>
  );
}
