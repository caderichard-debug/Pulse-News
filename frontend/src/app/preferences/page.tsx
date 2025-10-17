'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';
import SourceBiasBadge from '@/components/SourceBiasBadge';
import UnverifiedEmailAlert from '@/components/UnverifiedEmailAlert';
import DarkModeToggle from '@/components/DarkModeToggle';

interface TopicPreference {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
}

interface Source {
  source_id: number;
  name: string;
  url: string;
  trust_score: number;
  organizational_bias: string | null;
  subscribed: boolean;
}

interface Settings {
  source_discovery_mode: string;
  article_order_preference: string;
  articles_per_topic_default: number;
}

function PreferencesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [preferences, setPreferences] = useState<TopicPreference[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [settings, setSettings] = useState<Settings>({
    source_discovery_mode: 'some',
    article_order_preference: 'mixed',
    articles_per_topic_default: 5,
  });
  const [userInfo, setUserInfo] = useState<{ name: string; email: string }>({
    name: '',
    email: '',
  });

  // Initialize activeTab from URL or default to 'topics'
  const getInitialTab = (): 'topics' | 'sources' | 'settings' | 'account' => {
    const tab = searchParams.get('tab');
    if (tab === 'topics' || tab === 'sources' || tab === 'settings' || tab === 'account') {
      return tab;
    }
    return 'topics';
  };

  const [activeTab, setActiveTab] = useState<'topics' | 'sources' | 'settings' | 'account'>(getInitialTab());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadPreferences();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update activeTab when URL changes
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'topics' || tab === 'sources' || tab === 'settings' || tab === 'account') {
      setActiveTab(tab);
    }
  }, [searchParams]);

  // Helper function to update the tab and URL
  const handleTabChange = (tab: 'topics' | 'sources' | 'settings' | 'account') => {
    setActiveTab(tab);
    router.push(`/preferences?tab=${tab}`, { scroll: false });
  };

  const loadPreferences = async () => {
    try {
      const [prefsResponse, sourcesResponse, settingsResponse, userResponse] = await Promise.all([
        api.getPreferences(),
        api.getSources(),
        api.getSettings(),
        api.getCurrentUser(),
      ]);
      setPreferences(prefsResponse.topics);
      setSources(sourcesResponse);
      setSettings(settingsResponse);
      if (userResponse) {
        setUserInfo({
          name: userResponse.name || '',
          email: userResponse.email || '',
        });
      } else {
        setUserInfo({ name: '', email: '', })
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '';
      if (errorMessage.includes('401')) {
        // Not authenticated, redirect to login
        router.push('/login');
      } else {
        setMessage({ type: 'error', text: 'Failed to load preferences' });
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleActive = (topicId: number) => {
    setPreferences(
      preferences.map((pref) =>
        pref.id === topicId ? { ...pref, is_active: !pref.is_active } : pref
      )
    );
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const preferencesData = preferences.map((pref) => ({
        topic_id: pref.id,
        is_active: pref.is_active,
      }));

      await api.updatePreferences(preferencesData);
      setMessage({ type: 'success', text: 'Preferences saved successfully!' });
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to save preferences' });
    } finally {
      setSaving(false);
    }
  };

  const toggleSource = (sourceId: number) => {
    setSources(
      sources.map((source) =>
        source.source_id === sourceId ? { ...source, subscribed: !source.subscribed } : source
      )
    );
  };

  const handleSaveSources = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const subscribedSourceIds = sources.filter((s) => s.subscribed).map((s) => s.source_id);
      await api.updateSourcePreferences(subscribedSourceIds);
      setMessage({ type: 'success', text: 'Source preferences saved successfully!' });
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to save sources' });
    } finally {
      setSaving(false);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    setMessage(null);

    try {
      await api.updateSettings(settings);
      setMessage({ type: 'success', text: 'Settings saved successfully!' });
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };


  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading preferences...</p>
        </div>
      </div>
    );
  }

  const activeTopics = preferences.filter((p) => p.is_active);
  const subscribedSources = sources.filter((s) => s.subscribed);

  return (
    <>
      <Navbar />
      <UnverifiedEmailAlert />
      <div className="min-h-screen bg-background transition-colors">
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="bg-card rounded-lg shadow-sm p-6 mb-6 border border-border">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground">⚙️ Preferences</h1>
                <p className="text-muted-foreground mt-1">Customize your news experience</p>
              </div>
              <DarkModeToggle />
            </div>
          </div>

        {/* Tabs */}
        <div className="bg-card rounded-lg shadow-sm mb-6 border border-border">
          <div className="border-b border-border">
            <nav className="-mb-px flex">
              <button
                onClick={() => handleTabChange('topics')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'topics'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Topics ({activeTopics.length})
              </button>
              <button
                onClick={() => handleTabChange('sources')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'sources'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Sources ({subscribedSources.length})
              </button>
              <button
                onClick={() => handleTabChange('settings')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'settings'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Settings
              </button>
              <button
                onClick={() => handleTabChange('account')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'account'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Account
              </button>
            </nav>
          </div>
        </div>

        {/* Summary Card */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow-lg p-6 mb-6 text-white">
          <h2 className="text-xl font-semibold mb-2">Your Newsletter</h2>
          <p className="text-indigo-100">
            You&apos;re subscribed to <strong>{activeTopics.length}</strong> topics.
            Your daily digest will include articles from these topics.
          </p>
        </div>

        {/* Message */}
        {message && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {message.text}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'topics' && (
          <>
            <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">
                Topic Preferences
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Toggle topics on/off to customize your newsletter content.
              </p>

              <div className="space-y-4">
                {preferences.map((pref) => (
                  <div
                    key={pref.id}
                    className={`border rounded-lg p-4 transition-all ${
                      pref.is_active
                        ? 'border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-border bg-secondary dark:bg-muted'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <button
                            onClick={() => toggleActive(pref.id)}
                            className={`mr-3 w-12 h-6 rounded-full transition-colors relative ${
                              pref.is_active ? 'bg-primary' : 'bg-muted dark:bg-gray-600'
                            }`}
                          >
                            <span
                              className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white dark:bg-gray-100 rounded-full transition-transform ${
                                pref.is_active ? 'translate-x-6' : 'translate-x-0'
                              }`}
                            />
                          </button>

                          <div>
                            <h3 className="font-semibold text-foreground">
                              {pref.name}
                            </h3>
                            {pref.description && (
                              <p className="text-sm text-muted-foreground mt-1">
                                {pref.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {saving ? 'Saving...' : 'Save Preferences'}
              </button>
            </div>
          </>
        )}

        {activeTab === 'sources' && (
          <>
            <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">
                Source Preferences
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Select which news sources you want to receive articles from. Only articles from selected sources will appear in your newsletter.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sources.map((source) => (
                  <div
                    key={source.source_id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      source.subscribed
                        ? 'border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-border bg-card hover:border-primary/50 dark:hover:border-primary/50'
                    }`}
                    onClick={() => toggleSource(source.source_id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={source.subscribed}
                            onChange={() => toggleSource(source.source_id)}
                            className="mr-3 w-5 h-5 text-primary rounded focus:ring-primary accent-primary"
                          />
                          <div>
                            <h3 className="font-semibold text-foreground">{source.name}</h3>
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {source.url}
                            </a>
                          </div>
                        </div>
                        <div className="mt-2 flex items-center gap-2 ml-8">
                          <span className="text-sm text-muted-foreground">
                            Trust Score: {source.trust_score?.toFixed(1) || 'N/A'}
                          </span>
                          {source.organizational_bias && (
                            <SourceBiasBadge bias={source.organizational_bias} size="sm" />
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
              <button
                onClick={handleSaveSources}
                disabled={saving}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {saving ? 'Saving...' : 'Save Sources'}
              </button>
            </div>
          </>
        )}

        {activeTab === 'settings' && (
          <>
            <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">
                Newsletter Settings
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Customize how your newsletter is generated and delivered.
              </p>

              <div className="space-y-6">
                {/* Source Discovery Mode */}
                <div>
                  <label className="block text-sm font-medium text-card-foreground mb-2">
                    Source Discovery Mode
                  </label>
                  <p className="text-sm text-muted-foreground mb-3">
                    Control whether to only use your selected sources or allow discovery of new sources.
                  </p>
                  <select
                    value={settings.source_discovery_mode}
                    onChange={(e) => setSettings({ ...settings, source_discovery_mode: e.target.value })}
                    className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-foreground"
                  >
                    <option value="none">None - Only use my selected sources</option>
                    <option value="some">Some - Occasionally include new sources</option>
                    <option value="open">Open - Freely discover new sources</option>
                  </select>
                </div>

                {/* Article Order Preference */}
                <div>
                  <label className="block text-sm font-medium text-card-foreground mb-2">
                    Article Order Preference
                  </label>
                  <p className="text-sm text-muted-foreground mb-3">
                    Choose how articles are ordered in your newsletter.
                  </p>
                  <select
                    value={settings.article_order_preference}
                    onChange={(e) => setSettings({ ...settings, article_order_preference: e.target.value })}
                    className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-foreground"
                  >
                    <option value="good_first">Good News First - Positive sentiment first</option>
                    <option value="good_last">Good News Last - Negative sentiment first</option>
                    <option value="mixed">Mixed - Random order</option>
                  </select>
                </div>

                {/* Articles Per Topic */}
                <div>
                  <label className="block text-sm font-medium text-card-foreground mb-2">
                    Default Articles Per Topic: {settings.articles_per_topic_default}
                  </label>
                  <p className="text-sm text-muted-foreground mb-3">
                    How many articles to include per topic in each newsletter (1-10).
                  </p>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={settings.articles_per_topic_default}
                    onChange={(e) => setSettings({ ...settings, articles_per_topic_default: parseInt(e.target.value) })}
                    className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer accent-primary"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>1 article</span>
                    <span>10 articles</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
              <button
                onClick={handleSaveSettings}
                disabled={saving}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </>
        )}

        {activeTab === 'account' && (
          <>
            <div className="bg-card rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-foreground mb-4">
                Account Settings
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Manage your account information and security.
              </p>

              <div className="space-y-6">
                {/* User Information */}
                <div>
                  <h3 className="text-lg font-medium text-foreground mb-4">Profile Information</h3>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-card-foreground mb-2">
                        Name
                      </label>
                      <input
                        id="name"
                        type="text"
                        value={userInfo.name}
                        onChange={(e) => setUserInfo({ ...userInfo, name: e.target.value })}
                        className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-foreground"
                        placeholder="Your name"
                      />
                    </div>

                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-card-foreground mb-2">
                        Email Address
                      </label>
                      <input
                        id="email"
                        type="email"
                        value={userInfo.email}
                        disabled
                        className="w-full px-4 py-2 border border-border rounded-lg bg-background text-muted-foreground cursor-not-allowed"
                      />
                      <p className="mt-1 text-xs text-muted-foreground">
                        Email address cannot be changed
                      </p>
                    </div>
                  </div>
                </div>

                {/* Security Section */}
                <div className="pt-6 border-t border-border">
                  <h3 className="text-lg font-medium text-foreground mb-2">
                    Security
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Manage your password and account security.
                  </p>
                  <button
                    onClick={() => router.push('/forgot-password')}
                    className="px-4 py-2 border border-border text-card-foreground rounded-lg hover:bg-background transition-colors font-medium"
                  >
                    Change Password
                  </button>
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
              <button
                onClick={async () => {
                  setSaving(true);
                  setMessage(null);
                  try {
                    // TODO: Implement updateUserInfo API call
                    // await api.updateUserInfo(userInfo);
                    setMessage({ type: 'success', text: 'Account information saved successfully!' });
                  } catch (err) {
                    setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Failed to save account information' });
                  } finally {
                    setSaving(false);
                  }
                }}
                disabled={saving}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {saving ? 'Saving...' : 'Save Account Info'}
              </button>
            </div>
          </>
        )}

        {/* Info Card */}
        <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 transition-colors">
          <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
            📬 Newsletter Delivery
          </h3>
          <p className="text-sm text-blue-800 dark:text-blue-300">
            Your personalized newsletter arrives daily at 7 AM with articles from
            your selected topics. Each newsletter also includes our unique
            &quot;ethical framework&quot; analysis, helping you understand the underlying
            debates behind current events.
          </p>
        </div>
      </div>
    </div>
    </>
  );
}

export default function PreferencesPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading preferences...</p>
        </div>
      </div>
    }>
      <PreferencesContent />
    </Suspense>
  );
}
