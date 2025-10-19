'use client';

import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Footer from '@/components/Footer';

export default function WelcomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 dark:from-gray-900 via-indigo-50 dark:via-gray-800 to-purple-50 dark:to-gray-900 transition-colors">
      {/* Simple Header */}
      <header className="border-b border-border bg-card/50 dark:bg-card/30 backdrop-blur transition-colors">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <button
              onClick={() => router.push('/feed')}
              className="flex items-center gap-2 text-2xl font-bold text-primary hover:text-primary-hover transition-colors"
            >
              <Image
                src="/pulse-icon.png"
                alt="Pulse Logo"
                width={32}
                height={32}
                className="w-8 h-8 object-contain"
              />
              <span className="hidden sm:inline">Pulse</span>
            </button>
          </div>
          <div className="flex gap-3">
            <a
              href="/login"
              className="px-6 py-2 text-sm font-medium bg-card dark:bg-card text-primary border-2 border-primary rounded-lg hover:bg-accent dark:hover:bg-accent transition-colors"
            >
              Log In
            </a>
            <a
              href="/signup"
              className="px-6 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors shadow-md"
            >
              Sign Up
            </a>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-foreground mb-4">
            Welcome to <span className="text-primary">Pulse</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            AI-powered news aggregation with ethical clarity
          </p>
        </div>

        {/* How It Works Section */}
        <div className="bg-card border border-border rounded-lg shadow-lg p-8 mb-12 transition-colors">
          <h2 className="text-3xl font-bold text-foreground mb-8 text-center">
            How It Works
          </h2>

          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div className="text-center">
              <div className="text-4xl mb-4">📰</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">1. We Gather</h3>
              <p className="text-muted-foreground">
                Our system scrapes articles from trusted news sources via RSS feeds, collecting diverse perspectives.
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">2. AI Analyzes</h3>
              <p className="text-muted-foreground">
                GPT-4o-mini generates summaries, detects bias, verifies statistics, and maps articles to ethical frameworks.
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">📬</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">3. You Read</h3>
              <p className="text-muted-foreground">
                Receive a personalized daily newsletter with curated articles based on your topic preferences.
              </p>
            </div>
          </div>

          <div className="border-t border-border pt-8">
            <h3 className="text-2xl font-semibold text-foreground mb-4 text-center">
              Our Unique Features
            </h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-background border border-border rounded-lg p-6">
                <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                  <span>⚖️</span> Bias Detection
                </h4>
                <p className="text-sm text-muted-foreground">
                  Every article analyzed for political lean and organizational bias, helping you understand different perspectives.
                </p>
              </div>
              <div className="bg-background border border-border rounded-lg p-6">
                <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                  <span>📊</span> Statistics Verification
                </h4>
                <p className="text-sm text-muted-foreground">
                  AI traces statistics to their sources, rates credibility, and flags disputed claims.
                </p>
              </div>
              <div className="bg-background border border-border rounded-lg p-6">
                <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                  <span>🎯</span> Framework Mapping
                </h4>
                <p className="text-sm text-muted-foreground">
                  Articles mapped to underlying ethical debates like "Privacy vs. Security" to reveal the bigger picture.
                </p>
              </div>
              <div className="bg-background border border-border rounded-lg p-6">
                <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                  <span>🔍</span> Context Generation
                </h4>
                <p className="text-sm text-muted-foreground">
                  AI provides background information, historical context, and significance analysis for complex stories.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Open Source Section */}
        <div className="bg-card border border-border rounded-lg shadow-lg p-8 mb-12 transition-colors">
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              Open Source & Transparent
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-6">
              Pulse is built in the open. Our code is public, our methods are transparent, and our AI analysis is explainable.
            </p>
            <a
              href="https://github.com/caderichard-debug/Pulse-News"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gray-800 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors font-medium"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
              View on GitHub
            </a>
          </div>
        </div>

        {/* Contact Section */}
        <div className="bg-card border border-border rounded-lg shadow-lg p-8 mb-12 transition-colors">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              Get in Touch
            </h2>
            <p className="text-lg text-muted-foreground mb-6">
              Have questions or feedback? We'd love to hear from you.
            </p>
            <a
              href="mailto:support@pulsenews.app"
              className="inline-flex items-center gap-2 px-6 py-3 border-2 border-primary text-primary rounded-lg hover:bg-primary hover:text-white transition-colors font-medium"
            >
              ✉️ Contact Us
            </a>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <h2 className="text-3xl font-bold text-foreground mb-4">
            Ready to get started?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Create your free account and start receiving personalized news today.
          </p>
          <div className="flex gap-4 justify-center">
            <a
              href="/signup"
              className="px-8 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors font-semibold text-lg shadow-md"
            >
              Sign Up Free
            </a>
            <a
              href="/login"
              className="px-8 py-3 bg-card dark:bg-card text-primary border-2 border-primary rounded-lg hover:bg-accent dark:hover:bg-accent transition-colors font-semibold text-lg"
            >
              Log In
            </a>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
