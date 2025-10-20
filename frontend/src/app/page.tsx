'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Image from 'next/image';
import Footer from '@/components/Footer';

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
    <div className="min-h-screen transition-colors bg-gradient-to-br from-blue-50 dark:from-gray-900 via-indigo-50 dark:via-gray-800 to-purple-50 dark:to-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-foreground mb-4 flex items-center justify-center space-x-3">
            <Image
              src="/pulse-icon.png"
              alt="Pulse Logo"
              width={56}
              height={56}
              className="w-14 h-14"
            />
            <span className="text-primary">Pulse</span>
          </h1>
          <p className="text-2xl text-muted-foreground mb-8">
            News aggregation with ethical clarity
          </p>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-12">
            Get AI-powered summaries, bias detection, and unique framework analysis
            that maps articles to underlying ethical debates. Delivered daily to
            your inbox.
          </p>

          <div className="flex gap-4 justify-center">
            <a
              href="/welcome"
              className="px-8 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors font-semibold text-lg"
            >
              Get Started
            </a>
            <a
              href="/login"
              className="px-8 py-3 bg-card text-primary border-2 border-primary rounded-lg hover:bg-accent transition-colors font-semibold text-lg"
            >
              Log In
            </a>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-card border border-border rounded-lg shadow-lg p-6 transition-colors">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              AI Summaries
            </h3>
            <p className="text-muted-foreground">
              Concise 100-word summaries of top articles, saving you time while
              keeping you informed.
            </p>
          </div>

          <div className="bg-card border border-border rounded-lg shadow-lg p-6 transition-colors">
            <div className="text-4xl mb-4">⚖️</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              Bias Detection
            </h3>
            <p className="text-muted-foreground">
              Sentiment analysis and political lean detection helps you understand
              different perspectives.
            </p>
          </div>

          <div className="bg-card border border-border rounded-lg shadow-lg p-6 transition-colors">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              Framework Mapping
            </h3>
            <p className="text-muted-foreground">
              Our unique feature: articles mapped to ethical debates like &quot;Privacy
              vs. Security&quot; to see the bigger picture.
            </p>
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-card border border-border rounded-lg shadow-lg p-8 mb-16 transition-colors">
          <h2 className="text-3xl font-bold text-foreground mb-8 text-center">
            How It Works
          </h2>

          <div className="space-y-6">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center font-bold mr-4">
                1
              </div>
              <div>
                <h3 className="font-semibold text-lg text-foreground mb-1">
                  Choose Your Topics
                </h3>
                <p className="text-muted-foreground">
                  Select from Politics, Economics, Technology, Culture, and more.
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center font-bold mr-4">
                2
              </div>
              <div>
                <h3 className="font-semibold text-lg text-foreground mb-1">
                  We Aggregate & Analyze
                </h3>
                <p className="text-muted-foreground">
                  Our AI scrapes trusted sources, extracts articles, generates
                  summaries, and maps them to ethical frameworks.
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center font-bold mr-4">
                3
              </div>
              <div>
                <h3 className="font-semibold text-lg text-foreground mb-1">
                  Daily Newsletter Delivered
                </h3>
                <p className="text-muted-foreground">
                  Receive your personalized digest at 7 AM every day with the
                  articles and frameworks most relevant to you.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Trusted Sources */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground mb-6">
            Trusted Sources
          </h2>
          <div className="flex flex-wrap justify-center gap-6 text-muted-foreground">
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
        <div className="mt-16 text-center bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-600 dark:to-purple-700 rounded-lg shadow-xl p-12 text-white transition-colors">
          <h2 className="text-3xl font-bold mb-4">
            Questions? Get in Touch
          </h2>
          <p className="text-xl mb-8 text-indigo-100 dark:text-indigo-200">
            We&apos;d love to hear from you
          </p>
          <a
            href="mailto:support@pulsenews.app"
            className="inline-block px-8 py-3 bg-white text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-semibold text-lg"
          >
            Contact Us
          </a>
        </div>
      </div>
      <Footer />
    </div>
  );
}
