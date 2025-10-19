'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';

export default function PrivacyPolicyPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCurrentUser()
      .then(user => {
        setIsAuthenticated(!!user);
      })
      .catch(() => {
        setIsAuthenticated(false);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="min-h-screen bg-background" />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {isAuthenticated && <Navbar />}

      {!isAuthenticated && (
        <header className="border-b border-border bg-card">
          <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <span className="text-2xl font-bold text-primary">⚡ Pulse</span>
            </a>
            <div className="flex gap-3">
              <a
                href="/login"
                className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                Log In
              </a>
              <a
                href="/signup"
                className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors"
              >
                Sign Up
              </a>
            </div>
          </div>
        </header>
      )}

      <main className="flex-1 max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-foreground mb-6">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground mb-8">
          Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
        </p>

        <div className="prose prose-slate dark:prose-invert max-w-none">
          {/* Template placeholder - replace with actual privacy policy */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-8">
            <p className="text-blue-900 dark:text-blue-200 font-medium mb-2">
              📝 Privacy Policy Template
            </p>
            <p className="text-blue-800 dark:text-blue-300 text-sm">
              This is a template placeholder. Replace this section with your actual privacy policy content.
              You can use a privacy policy generator or consult with legal counsel to create a comprehensive policy.
            </p>
            <p className="text-blue-800 dark:text-blue-300 text-sm mt-2">
              Suggested resource: <a href="https://www.termsfeed.com/privacy-policy-generator/" target="_blank" rel="noopener noreferrer" className="underline">TermsFeed Privacy Policy Generator</a>
            </p>
          </div>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              1. Information We Collect
            </h2>
            <p className="text-card-foreground mb-4">
              We collect information you provide directly to us when you create an account and use our services:
            </p>
            <ul className="list-disc list-inside text-card-foreground space-y-2 ml-4">
              <li>Account information (name, email address)</li>
              <li>Topic and source preferences for newsletter customization</li>
              <li>Reading history and article interactions</li>
              <li>Newsletter delivery preferences and settings</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              2. How We Use Your Information
            </h2>
            <p className="text-card-foreground mb-4">
              We use the information we collect to:
            </p>
            <ul className="list-disc list-inside text-card-foreground space-y-2 ml-4">
              <li>Provide, maintain, and improve our services</li>
              <li>Send you personalized daily newsletters based on your preferences</li>
              <li>Analyze and understand how you use our services</li>
              <li>Communicate with you about service updates and support</li>
              <li>Detect and prevent fraud and abuse</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              3. Data Storage and Security
            </h2>
            <p className="text-card-foreground mb-4">
              We implement appropriate technical and organizational measures to protect your personal information:
            </p>
            <ul className="list-disc list-inside text-card-foreground space-y-2 ml-4">
              <li>Data stored in encrypted PostgreSQL databases</li>
              <li>Secure authentication using JWT tokens</li>
              <li>Regular security audits and updates</li>
              <li>Limited access to personal data by authorized personnel only</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              4. Your Rights and Choices
            </h2>
            <p className="text-card-foreground mb-4">
              You have the following rights regarding your personal information:
            </p>
            <ul className="list-disc list-inside text-card-foreground space-y-2 ml-4">
              <li><strong>Access:</strong> You can access your account information through your account settings</li>
              <li><strong>Update:</strong> You can update your preferences and personal information at any time</li>
              <li><strong>Delete:</strong> You can delete your account and all associated data through account settings</li>
              <li><strong>Opt-out:</strong> You can unsubscribe from newsletters at any time</li>
              <li><strong>Data portability:</strong> You can request a copy of your data</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              5. Third-Party Services
            </h2>
            <p className="text-card-foreground mb-4">
              We use the following third-party services to operate Pulse:
            </p>
            <ul className="list-disc list-inside text-card-foreground space-y-2 ml-4">
              <li><strong>OpenAI:</strong> For AI-powered article analysis and summarization</li>
              <li><strong>Resend:</strong> For email delivery of newsletters</li>
              <li><strong>PostgreSQL:</strong> For secure data storage</li>
              <li><strong>Hosting Provider:</strong> For application infrastructure</li>
            </ul>
            <p className="text-card-foreground mt-4">
              These services may collect and process data according to their own privacy policies.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              6. Cookies and Tracking
            </h2>
            <p className="text-card-foreground mb-4">
              We use minimal cookies and local storage to:
            </p>
            <ul className="list-disc list-inside text-card-foreground space-y-2 ml-4">
              <li>Maintain your authentication session</li>
              <li>Remember your theme preferences (light/dark mode)</li>
              <li>Improve your user experience</li>
            </ul>
            <p className="text-card-foreground mt-4">
              We do not use third-party advertising cookies or tracking scripts.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              7. Data Retention
            </h2>
            <p className="text-card-foreground">
              We retain your personal information for as long as your account is active or as needed to provide you services.
              When you delete your account, we permanently delete all your personal data, including:
            </p>
            <ul className="list-disc list-inside text-card-foreground space-y-2 ml-4 mt-4">
              <li>Account information and preferences</li>
              <li>Reading history and interactions</li>
              <li>Newsletter history</li>
              <li>All associated data</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              8. Children's Privacy
            </h2>
            <p className="text-card-foreground">
              Our services are not directed to children under 13 years of age. We do not knowingly collect personal
              information from children under 13. If you believe we have collected information from a child under 13,
              please contact us immediately.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              9. Changes to This Privacy Policy
            </h2>
            <p className="text-card-foreground">
              We may update this privacy policy from time to time. We will notify you of any changes by posting the
              new privacy policy on this page and updating the "Last updated" date. We encourage you to review this
              privacy policy periodically for any changes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              10. Contact Us
            </h2>
            <p className="text-card-foreground mb-4">
              If you have any questions about this privacy policy or our privacy practices, please contact us:
            </p>
            <div className="bg-card border border-border rounded-lg p-4">
              <p className="text-card-foreground">
                <strong>Email:</strong> <a href="mailto:support@pulsenews.app" className="text-primary hover:underline">support@pulsenews.app</a>
              </p>
              <p className="text-card-foreground mt-2">
                <strong>Website:</strong> <a href="https://pulsenews.app" className="text-primary hover:underline">pulsenews.app</a>
              </p>
            </div>
          </section>

          <section className="mt-12 pt-8 border-t border-border">
            <p className="text-sm text-muted-foreground">
              This privacy policy is effective as of the date stated at the top of this page. Your continued use of
              our services after any changes to this privacy policy constitutes your acceptance of such changes.
            </p>
          </section>
        </div>
      </main>

      {isAuthenticated && (
        <footer className="border-t border-border bg-card mt-auto">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-6 text-sm text-muted-foreground">
              <a href="mailto:support@pulsenews.app" className="hover:text-foreground transition-colors">
                Contact Us
              </a>
              <span className="hidden sm:inline">•</span>
              <a href="/preferences?tab=account" className="hover:text-foreground transition-colors">
                Account Settings
              </a>
              <span className="hidden sm:inline">•</span>
              <a href="/preferences?tab=topics" className="hover:text-foreground transition-colors">
                Newsletter Preferences
              </a>
              <span className="hidden sm:inline">•</span>
              <a href="/how-it-works" className="hover:text-foreground transition-colors">
                How It Works
              </a>
              <span className="hidden sm:inline">•</span>
              <a href="/privacy-policy" className="hover:text-foreground transition-colors">
                Privacy Policy
              </a>
            </div>
            <div className="text-center text-xs text-muted-foreground mt-4">
              © {new Date().getFullYear()} Pulse News. All rights reserved.
            </div>
          </div>
        </footer>
      )}

      {!isAuthenticated && (
        <footer className="border-t border-border bg-card mt-auto">
          <div className="max-w-4xl mx-auto px-4 py-6 text-center">
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} Pulse News. All rights reserved.
            </p>
          </div>
        </footer>
      )}
    </div>
  );
}
