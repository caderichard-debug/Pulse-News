'use client';

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

function InsightsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Auto-navigate to specific tab if provided
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'analyze') {
      router.push('/analyze');
    } else if (tab === 'sources') {
      router.push('/sources');
    } else if (tab === 'analytics') {
      router.push('/analytics');
    }
  }, [searchParams, router]);

  const tools = [
    {
      name: 'Analyze',
      icon: '🔍',
      description: 'Submit any article URL for instant AI-powered analysis with summaries, bias detection, and framework mapping.',
      path: '/analyze',
      color: 'from-blue-500 to-indigo-600',
    },
    {
      name: 'Sources',
      icon: '📑',
      description: 'Browse all news sources, view their bias ratings, credibility scores, and recent articles.',
      path: '/sources',
      color: 'from-purple-500 to-pink-600',
    },
    {
      name: 'Analytics',
      icon: '📊',
      description: 'View your reading patterns, sentiment trends, bias exposure, and personalized insights.',
      path: '/analytics',
      color: 'from-green-500 to-teal-600',
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <div className="flex-1">
        <div className="max-w-6xl mx-auto px-4 py-12">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-foreground mb-4">Insights & Tools</h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Explore our suite of tools to analyze articles, discover sources, and understand your reading habits.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {tools.map((tool) => (
              <button
                key={tool.path}
                onClick={() => router.push(tool.path)}
                className="group bg-card border border-border rounded-lg shadow-lg p-8 hover:shadow-xl transition-all hover:-translate-y-1"
              >
                <div className={`text-6xl mb-6 bg-gradient-to-br ${tool.color} bg-clip-text text-transparent group-hover:scale-110 transition-transform`}>
                  {tool.icon}
                </div>
                <h2 className="text-2xl font-bold text-foreground mb-4 group-hover:text-primary transition-colors">
                  {tool.name}
                </h2>
                <p className="text-muted-foreground leading-relaxed">
                  {tool.description}
                </p>
                <div className="mt-6 flex items-center justify-center text-primary group-hover:translate-x-2 transition-transform">
                  <span className="font-medium">Open {tool.name}</span>
                  <span className="ml-2">→</span>
                </div>
              </button>
            ))}
          </div>

          <div className="mt-16 bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-600 dark:to-purple-700 rounded-lg shadow-xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-3">
              Quick Tip
            </h2>
            <p className="text-indigo-100 dark:text-indigo-200">
              Each tool provides unique insights into the news. Use Analyze for deep-dives,
              Sources to discover new perspectives, and Analytics to track your reading patterns over time.
            </p>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default function InsightsPage() {
  return (
    <Suspense>
      <InsightsContent />
    </Suspense>
  );
}
