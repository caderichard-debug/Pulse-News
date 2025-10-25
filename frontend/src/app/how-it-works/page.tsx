/* eslint-disable react/no-unescaped-entities */
'use client';

import Navbar from '@/components/Navbar';
import UnverifiedEmailAlert from '@/components/UnverifiedEmailAlert';
import Footer from '@/components/Footer';

export default function HowItWorksPage() {
  return (
    <>
      <Navbar />
      <UnverifiedEmailAlert />
      <div className="min-h-screen transition-colors bg-gradient-to-br from-blue-50 dark:from-gray-900 via-indigo-50 dark:via-gray-800 to-purple-50 dark:to-gray-900">
        <div className="max-w-5xl mx-auto px-4 py-12">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-foreground mb-4">
              How <span className="text-primary">Pulse</span> Works
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Understanding our AI-powered news analysis pipeline, from source selection to delivery
            </p>
          </div>

          {/* Data Pipeline */}
          <section className="mb-16">
            <div className="bg-card rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-foreground mb-6 flex items-center gap-3">
                <span className="text-4xl">🔄</span>
                The Data Pipeline
              </h2>
              <p className="text-card-foreground mb-6 leading-relaxed">
                Pulse operates a fully automated pipeline that processes news articles 24/7. Here's how it works:
              </p>

              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-primary rounded-full flex items-center justify-center font-bold text-lg">
                    1
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-foreground mb-2">RSS Scraping</h3>
                    <p className="text-card-foreground">
                      Every hour, we fetch the latest articles from trusted news sources via their RSS feeds.
                      Articles are immediately stored in our database with metadata like title, URL, and publication date.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-primary rounded-full flex items-center justify-center font-bold text-lg">
                    2
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-foreground mb-2">Content Extraction</h3>
                    <p className="text-card-foreground">
                      We extract the full article text using Trafilatura (our primary tool) with Readability as a fallback.
                      This gives us clean, readable content stripped of ads and navigation elements.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-primary rounded-full flex items-center justify-center font-bold text-lg">
                    3
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-foreground mb-2">AI Analysis</h3>
                    <p className="text-card-foreground">
                      OpenAI's GPT-4o-mini analyzes each article to generate:
                    </p>
                    <ul className="list-disc list-inside text-card-foreground mt-2 ml-4 space-y-1">
                      <li>100-word summary</li>
                      <li>Sentiment score (-10 to +10)</li>
                      <li>Political lean detection</li>
                      <li>Key statistics extraction</li>
                    </ul>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-primary rounded-full flex items-center justify-center font-bold text-lg">
                    4
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-foreground mb-2">Framework Mapping</h3>
                    <p className="text-card-foreground">
                      AI maps articles to ethical frameworks (like "Individual Liberty vs. Collective Welfare")
                      to help you understand the underlying philosophical debates in the news.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-primary rounded-full flex items-center justify-center font-bold text-lg">
                    5
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-foreground mb-2">Statistics Verification</h3>
                    <p className="text-card-foreground">
                      A 3-stage pipeline traces statistics to their original sources, rates source credibility,
                      and cross-checks with external fact-checking APIs when available.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-primary rounded-full flex items-center justify-center font-bold text-lg">
                    6
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-foreground mb-2">Context Generation</h3>
                    <p className="text-card-foreground">
                      AI generates background information, timelines, key players, and significance analysis
                      to give you the full story behind each article.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-primary rounded-full flex items-center justify-center font-bold text-lg">
                    7
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-foreground mb-2">Article Clustering</h3>
                    <p className="text-card-foreground">
                      Similar articles from different sources are grouped together, allowing you to compare
                      how different outlets cover the same story.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 text-primary rounded-full flex items-center justify-center font-bold text-lg">
                    8
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-foreground mb-2">Newsletter Generation</h3>
                    <p className="text-card-foreground">
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
            <div className="bg-card rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-foreground mb-6 flex items-center gap-3">
                <span className="text-4xl">📰</span>
                How We Choose Sources
              </h2>
              <div className="space-y-4 text-card-foreground leading-relaxed">
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
            <div className="bg-card rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-foreground mb-6 flex items-center gap-3">
                <span className="text-4xl">⚖️</span>
                Bias & Sentiment Detection
              </h2>
              <div className="space-y-4 text-card-foreground leading-relaxed">
                <h3 className="font-semibold text-lg text-foreground">How It Works</h3>
                <p>
                  Our AI analyzes the full article text using GPT-4o-mini to extract two key metrics:
                </p>

                <div className="bg-context-section border-l-4 border-blue-500 p-4 my-4">
                  <h4 className="font-semibold text-foreground mb-2">Sentiment Score (-10 to +10)</h4>
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

                <div className="bg-purple-card border-l-4 border-purple-500 p-4 my-4">
                  <h4 className="font-semibold text-foreground mb-2">Political Lean (Left, Center, Right)</h4>
                  <p className="text-sm">
                    Detects the political framing of the article based on language choices, sources cited,
                    and narrative structure—independent of the publisher's overall bias.
                  </p>
                  <div className="mt-3 text-sm">
                    <p><strong>Note:</strong> An article from a center-leaning source can still have a left or right lean
                    depending on the specific story and how it's framed.</p>
                  </div>
                </div>

                <h3 className="font-semibold text-lg text-foreground mt-6">Why This Matters</h3>
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
            <div className="bg-card rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-foreground mb-6 flex items-center gap-3">
                <span className="text-4xl">📊</span>
                Statistics Verification
              </h2>
              <div className="space-y-4 text-card-foreground leading-relaxed">
                <p>
                  When articles cite statistics, we run a 3-stage verification pipeline to trace claims
                  back to their sources:
                </p>

                <div className="space-y-4 mt-6">
                  <div className="bg-success border-l-4 border-green-500 bg-green-50 p-4">
                    <h3 className="font-semibold text-foreground mb-2">Stage 1: Source Tracing</h3>
                    <p className="text-sm">
                      AI extracts statistics from the article and identifies the original source
                      (e.g., "According to Pew Research, 60% of Americans..."). We trace the source name
                      and URL when cited.
                    </p>
                  </div>

                  <div className="bg-context-section border-l-4 border-blue-500 bg-blue-50 p-4">
                    <h3 className="font-semibold text-foreground mb-2">Stage 2: Credibility Rating</h3>
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

                  <div className="bg-stats-section border-l-4 border-yellow-500 bg-yellow-50 p-4">
                    <h3 className="font-semibold text-foreground mb-2">Stage 3: Fact-Check Integration</h3>
                    <p className="text-sm">
                      When available, we query external fact-checking APIs (Google Fact Check, ClaimBuster)
                      to see if the statistic has been independently verified or disputed.
                    </p>
                  </div>
                </div>

                <div className="bg-secondary border border-border rounded-lg p-6 mt-8">
                  <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                    <span>❓</span>
                    <span>Why Some Statistics Aren't Verified</span>
                  </h3>
                  <p className="text-sm text-card-foreground mb-3">
                    You may notice that not all statistics in your newsletter have verification badges. Here's why:
                  </p>
                  <ul className="list-disc list-inside ml-4 space-y-2 text-sm text-card-foreground">
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
                  <p className="text-sm text-card-foreground mt-4">
                    <strong>What to do:</strong> Treat unverified statistics with healthy skepticism. Click through
                    to the original article and look for source citations. If a claim seems important, do your own
                    fact-checking using the sources we provide.
                  </p>
                </div>

                <div className="bg-info border border-indigo-200 rounded-lg p-4 mt-6">
                  <p className="text-sm text-info">
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
            <div className="bg-card rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-foreground mb-6 flex items-center gap-3">
                <span className="text-4xl">🎯</span>
                Ethical Framework Mapping
              </h2>
              <div className="space-y-4 text-card-foreground leading-relaxed">
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

          {/* Chrome Extension */}
          <section className="mb-16">
            <div className="bg-card rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-foreground mb-6 flex items-center gap-3">
                <span className="text-4xl">🚀</span>
                Chrome Extension: Instant Article Analysis
              </h2>
              <div className="space-y-4 text-card-foreground leading-relaxed">
                <p>
                  Our Chrome extension brings Pulse's powerful analysis directly to your browser, allowing you to analyze any article instantly while browsing.
                </p>

                <div className="bg-context-section border border-context rounded-lg p-6 my-6">
                  <h3 className="font-semibold text-lg text-foreground mb-4">How It Works</h3>
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold text-sm">
                        1
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground">Click the Extension Icon</h4>
                        <p className="text-sm text-muted-foreground">
                          While reading any article on the web, click the Pulse extension icon in your browser toolbar.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold text-sm">
                        2
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground">Sidebar Opens</h4>
                        <p className="text-sm text-muted-foreground">
                          A convenient sidebar opens on the right side of your screen, showing the complete analysis without navigating away from the article.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold text-sm">
                        3
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground">Get Full Analysis</h4>
                        <p className="text-sm text-muted-foreground">
                          View the same comprehensive analysis as the main platform: summary, bias detection, statistics verification, and ethical framework mapping.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <h3 className="font-semibold text-lg text-foreground">What Problem It Solves</h3>
                <p>
                  The Chrome extension addresses a common problem: you come across interesting articles while browsing and want immediate analysis without leaving your reading flow.
                </p>
                <ul className="list-disc list-inside ml-4 space-y-2 mt-3">
                  <li><strong>No Context Switching:</strong> Get insights without opening new tabs or navigating away from your article</li>
                  <li><strong>Instant Credibility Check:</strong> Quickly assess if an article is trustworthy before sharing or believing it</li>
                  <li><strong>Bias Awareness:</strong> Understand the political framing and emotional tone in real-time</li>
                  <li><strong>Statistical Verification:</strong> Check if cited statistics have been verified and trace their sources</li>
                  <li><strong>Ethical Context:</strong> See the deeper philosophical debates underlying the news story</li>
                </ul>

                <div className="bg-info border border-info rounded-lg p-4 mt-6">
                  <h3 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                    <span>⚡</span>
                    <span>Use Cases</span>
                  </h3>
                  <ul className="text-sm text-card-foreground space-y-1">
                    <li><strong>Social Media:</strong> Analyze articles shared on Twitter/X, Facebook, or LinkedIn before engaging</li>
                    <li><strong>News Browsing:</strong> Get instant analysis while reading news on publisher websites</li>
                    <li><strong>Research:</strong> Quickly evaluate sources for academic or professional research</li>
                    <li><strong>Media Literacy:</strong> Build critical thinking skills by seeing bias and framing patterns</li>
                  </ul>
                </div>

                <div className="text-center mt-8">
                  <a
                    href="https://chromewebstore.google.com/detail/gcfamjhnhdhoobgcmnkepjibcmhafpfp?utm_source=item-share-cb"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-all font-medium shadow-lg"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                    </svg>
                    Install Chrome Extension
                  </a>
                  <p className="text-sm text-muted-foreground mt-2">
                    Other browsers coming soon!
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Open Source & Documentation */}
          <section className="mb-16">
            <div className="bg-card rounded-lg shadow-lg p-8">
              <h2 className="text-3xl font-bold text-foreground mb-6 flex items-center gap-3">
                <span className="text-4xl">📚</span>
                Open Source & Documentation
              </h2>
              <div className="space-y-4 text-card-foreground leading-relaxed">
                <p>
                  Pulse is built with transparency and open source principles. Our code, methods, and documentation are publicly available for anyone to review and learn from.
                </p>

                <div className="grid md:grid-cols-2 gap-6 mt-8">
                  <div className="bg-background border border-border rounded-lg p-6">
                    <h3 className="font-semibold text-lg text-foreground mb-3 flex items-center gap-2">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                      </svg>
                      Source Code
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Explore our complete codebase, contribute to development, or see exactly how our AI analysis works under the hood.
                    </p>
                    <a
                      href="https://github.com/caderichard-debug/Pulse-News"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors font-medium text-sm"
                    >
                      View on GitHub
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>

                  <div className="bg-background border border-border rounded-lg p-6">
                    <h3 className="font-semibold text-lg text-foreground mb-3 flex items-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                      Documentation
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Comprehensive guides, API references, architecture docs, and setup instructions for developers and users.
                    </p>
                    <a
                      href="https://pulse-news.readthedocs.io/en/latest/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors font-medium text-sm"
                    >
                      Read Documentation
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                </div>

                <div className="bg-secondary border border-border rounded-lg p-6 mt-6">
                  <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                    <span>🔍</span>
                    <span>Why Open Source Matters</span>
                  </h3>
                  <ul className="text-sm text-card-foreground space-y-2">
                    <li><strong>Transparency:</strong> You can verify exactly how our AI analysis works and trust that our methods are sound</li>
                    <li><strong>Accountability:</strong> Public code means public scrutiny - we're accountable for our algorithms and decisions</li>
                    <li><strong>Collaboration:</strong> Developers can contribute improvements, report issues, and build on our work</li>
                    <li><strong>Learning:</strong> Students and researchers can study our implementation for educational purposes</li>
                    <li><strong>Trust:</strong> No hidden algorithms or black boxes - everything is explainable and verifiable</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Footer CTA */}
          <div className="text-center bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-600 dark:to-purple-700 rounded-lg shadow-xl p-8 text-white">
            <h2 className="text-2xl font-bold mb-3">Have Questions?</h2>
            <p className="text-indigo-100 dark:text-indigo-200 mb-6">
              We're here to help. Reach out with any questions or feedback.
            </p>
            <a
              href="mailto:support@pulsenews.app"
              className="inline-block px-6 py-3 bg-white text-primary rounded-lg hover:bg-indigo-50 transition-colors font-semibold"
            >
              Contact Us
            </a>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
}
