/* eslint-disable react/no-unescaped-entities */
'use client';

import Navbar from '@/components/Navbar';
import UnverifiedEmailAlert from '@/components/UnverifiedEmailAlert';

export default function HowItWorksPage() {
  return (
    <>
      <Navbar />
      <UnverifiedEmailAlert />
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="max-w-5xl mx-auto px-4 py-12">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              How <span className="text-indigo-600">Pulse</span> Works
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Understanding our AI-powered news analysis pipeline, from source selection to delivery
            </p>
          </div>

          {/* Data Pipeline */}
          <section className="mb-16">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <span className="text-4xl">🔄</span>
                The Data Pipeline
              </h2>
              <p className="text-gray-700 mb-6 leading-relaxed">
                Pulse operates a fully automated pipeline that processes news articles 24/7. Here's how it works:
              </p>

              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                    1
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">RSS Scraping</h3>
                    <p className="text-gray-700">
                      Every hour, we fetch the latest articles from trusted news sources via their RSS feeds.
                      Articles are immediately stored in our database with metadata like title, URL, and publication date.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                    2
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">Content Extraction</h3>
                    <p className="text-gray-700">
                      We extract the full article text using Trafilatura (our primary tool) with Readability as a fallback.
                      This gives us clean, readable content stripped of ads and navigation elements.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                    3
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">AI Analysis</h3>
                    <p className="text-gray-700">
                      OpenAI's GPT-4o-mini analyzes each article to generate:
                    </p>
                    <ul className="list-disc list-inside text-gray-700 mt-2 ml-4 space-y-1">
                      <li>100-word summary</li>
                      <li>Sentiment score (-10 to +10)</li>
                      <li>Political lean detection</li>
                      <li>Key statistics extraction</li>
                    </ul>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                    4
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">Framework Mapping</h3>
                    <p className="text-gray-700">
                      AI maps articles to ethical frameworks (like "Individual Liberty vs. Collective Welfare")
                      to help you understand the underlying philosophical debates in the news.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                    5
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">Statistics Verification</h3>
                    <p className="text-gray-700">
                      A 3-stage pipeline traces statistics to their original sources, rates source credibility,
                      and cross-checks with external fact-checking APIs when available.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                    6
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">Context Generation</h3>
                    <p className="text-gray-700">
                      AI generates background information, timelines, key players, and significance analysis
                      to give you the full story behind each article.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                    7
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">Article Clustering</h3>
                    <p className="text-gray-700">
                      Similar articles from different sources are grouped together, allowing you to compare
                      how different outlets cover the same story.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                    8
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-2">Newsletter Generation</h3>
                    <p className="text-gray-700">
                      At 7 AM daily, we compile your personalized newsletter based on your topic preferences
                      and email it to you with all the analysis attached.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Source Selection */}
          <section className="mb-16">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <span className="text-4xl">📰</span>
                How We Choose Sources
              </h2>
              <div className="space-y-4 text-gray-700 leading-relaxed">
                <p>
                  Our source selection process prioritizes <strong>credibility</strong>, <strong>diversity</strong>,
                  and <strong>transparency</strong>. Each source is evaluated on:
                </p>
                <ul className="list-disc list-inside ml-4 space-y-2">
                  <li>
                    <strong>Trust Score (0.0-1.0):</strong> Based on editorial standards, fact-checking practices,
                    and journalistic reputation
                  </li>
                  <li>
                    <strong>Political Lean:</strong> Labeled as left, center, or right to ensure balanced coverage
                  </li>
                  <li>
                    <strong>Fact-Checking:</strong> Preference for sources with dedicated fact-checking teams
                  </li>
                  <li>
                    <strong>Source Diversity:</strong> Mix of wire services (Reuters, AP), traditional media (NYT, BBC),
                    and specialized outlets (Ars Technica, The Atlantic)
                  </li>
                </ul>
                <p className="mt-4">
                  Currently, we track sources including <strong>AP News, Reuters, NPR, BBC, The New York Times,
                  The Atlantic, and Ars Technica</strong>. Each source's RSS feed is monitored hourly for new articles.
                </p>
              </div>
            </div>
          </section>

          {/* Bias & Sentiment */}
          <section className="mb-16">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <span className="text-4xl">⚖️</span>
                Bias & Sentiment Detection
              </h2>
              <div className="space-y-4 text-gray-700 leading-relaxed">
                <h3 className="font-semibold text-lg text-gray-900">How It Works</h3>
                <p>
                  Our AI analyzes the full article text using GPT-4o-mini to extract two key metrics:
                </p>

                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 my-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Sentiment Score (-10 to +10)</h4>
                  <p className="text-sm">
                    Measures the emotional tone of the article. Negative scores indicate pessimistic or critical coverage,
                    while positive scores suggest optimistic or favorable framing.
                  </p>
                  <div className="mt-3 text-sm">
                    <p><strong>Example:</strong></p>
                    <ul className="list-disc list-inside ml-4 mt-1">
                      <li>+7: "Economy soars with record job growth"</li>
                      <li>0: "GDP remains stable at 2% growth"</li>
                      <li>-6: "Unemployment crisis deepens amid layoffs"</li>
                    </ul>
                  </div>
                </div>

                <div className="bg-purple-50 border-l-4 border-purple-500 p-4 my-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Political Lean (Left, Center, Right)</h4>
                  <p className="text-sm">
                    Detects the political framing of the article based on language choices, sources cited,
                    and narrative structure—independent of the publisher's overall bias.
                  </p>
                  <div className="mt-3 text-sm">
                    <p><strong>Note:</strong> An article from a center-leaning source can still have a left or right lean
                    depending on the specific story and how it's framed.</p>
                  </div>
                </div>

                <h3 className="font-semibold text-lg text-gray-900 mt-6">Why This Matters</h3>
                <p>
                  Understanding bias and sentiment helps you:
                </p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li>Recognize how news frames issues emotionally</li>
                  <li>Compare coverage across the political spectrum</li>
                  <li>Make informed decisions about what to believe</li>
                  <li>Understand your own media consumption patterns</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Statistics Verification */}
          <section className="mb-16">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <span className="text-4xl">📊</span>
                Statistics Verification
              </h2>
              <div className="space-y-4 text-gray-700 leading-relaxed">
                <p>
                  When articles cite statistics, we run a 3-stage verification pipeline to trace claims
                  back to their sources:
                </p>

                <div className="space-y-4 mt-6">
                  <div className="border-l-4 border-green-500 bg-green-50 p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Stage 1: Source Tracing</h3>
                    <p className="text-sm">
                      AI extracts statistics from the article and identifies the original source
                      (e.g., "According to Pew Research, 60% of Americans..."). We trace the source name
                      and URL when cited.
                    </p>
                  </div>

                  <div className="border-l-4 border-blue-500 bg-blue-50 p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Stage 2: Credibility Rating</h3>
                    <p className="text-sm">
                      Each source is rated on a 0-5 star scale based on:
                    </p>
                    <ul className="list-disc list-inside ml-4 mt-2 text-sm">
                      <li>Institutional reputation (government agencies, research institutions)</li>
                      <li>Peer review and methodology transparency</li>
                      <li>Historical accuracy and independence from bias</li>
                    </ul>
                    <p className="text-sm mt-2">
                      <strong>Example:</strong> Pew Research (⭐⭐⭐⭐⭐), U.S. Census Bureau (⭐⭐⭐⭐⭐),
                      Think Tank Reports (⭐⭐⭐)
                    </p>
                  </div>

                  <div className="border-l-4 border-yellow-500 bg-yellow-50 p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Stage 3: Fact-Check Integration</h3>
                    <p className="text-sm">
                      When available, we query external fact-checking APIs (Google Fact Check, ClaimBuster)
                      to see if the statistic has been independently verified or disputed.
                    </p>
                  </div>
                </div>

                <div className="bg-gray-100 border border-gray-300 rounded-lg p-6 mt-8">
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <span>❓</span>
                    <span>Why Some Statistics Aren't Verified</span>
                  </h3>
                  <p className="text-sm text-gray-700 mb-3">
                    You may notice that not all statistics in your newsletter have verification badges. Here's why:
                  </p>
                  <ul className="list-disc list-inside ml-4 space-y-2 text-sm text-gray-700">
                    <li>
                      <strong>Source not cited:</strong> The article mentions a number but doesn't attribute it
                      to a specific source (e.g., "Studies show...")
                    </li>
                    <li>
                      <strong>Proprietary data:</strong> The statistic comes from private research or internal
                      company reports that aren't publicly accessible
                    </li>
                    <li>
                      <strong>Breaking news:</strong> The article was just published and our verification pipeline
                      hasn't processed it yet
                    </li>
                    <li>
                      <strong>API rate limits:</strong> External fact-checking services have usage limits, so we
                      prioritize high-impact claims
                    </li>
                    <li>
                      <strong>Qualitative claims:</strong> Some statements aren't pure statistics
                      (e.g., "many experts believe...")
                    </li>
                  </ul>
                  <p className="text-sm text-gray-700 mt-4">
                    <strong>What to do:</strong> Treat unverified statistics with healthy skepticism. Click through
                    to the original article and look for source citations. If a claim seems important, do your own
                    fact-checking using the sources we provide.
                  </p>
                </div>

                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mt-6">
                  <p className="text-sm text-indigo-900">
                    <strong>💡 Pro Tip:</strong> In your newsletter, verified statistics show badges like
                    ✓ (verified), ⚠️ (disputed), or ⏳ (unverified). Hover over badges to see credibility scores
                    and source information.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Ethical Frameworks */}
          <section className="mb-16">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <span className="text-4xl">🎯</span>
                Ethical Framework Mapping
              </h2>
              <div className="space-y-4 text-gray-700 leading-relaxed">
                <p>
                  One of Pulse's unique features is mapping articles to <strong>ethical frameworks</strong>—the
                  underlying philosophical debates that shape how we think about issues.
                </p>
                <p>
                  For example, a story about vaccine mandates might map to:
                </p>
                <ul className="list-disc list-inside ml-4 space-y-1">
                  <li><strong>Individual Liberty vs. Collective Welfare</strong> (personal freedom vs. public health)</li>
                  <li><strong>State Authority vs. Personal Autonomy</strong> (government power vs. individual rights)</li>
                </ul>
                <p className="mt-4">
                  AI assigns each article a position on the framework axis (-10 to +10) and explains why.
                  This helps you understand the deeper values at play in the news, not just the surface-level facts.
                </p>
              </div>
            </div>
          </section>

          {/* Footer CTA */}
          <div className="text-center bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow-xl p-8 text-white">
            <h2 className="text-2xl font-bold mb-3">Ready to Get Started?</h2>
            <p className="text-indigo-100 mb-6">
              Experience news with clarity, context, and critical thinking.
            </p>
            <a
              href="/signup"
              className="inline-block px-6 py-3 bg-white text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors font-semibold"
            >
              Sign Up Now
            </a>
          </div>
        </div>
      </div>
    </>
  );
}
