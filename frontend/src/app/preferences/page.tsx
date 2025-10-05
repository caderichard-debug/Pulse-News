'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Navbar from '@/components/Navbar';

interface TopicPreference {
  id: number;
  name: string;
  description: string;
  priority: number;
  is_active: boolean;
}

interface Source {
  source_id: number;
  name: string;
  url: string;
  trust_score: number;
  political_lean: string | null;
  subscribed: boolean;
}

interface Settings {
  source_discovery_mode: string;
  article_order_preference: string;
  articles_per_topic_default: number;
}

export default function PreferencesPage() {
  const router = useRouter();
  const [preferences, setPreferences] = useState<TopicPreference[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [settings, setSettings] = useState<Settings>({
    source_discovery_mode: 'some',
    article_order_preference: 'mixed',
    articles_per_topic_default: 5,
  });
  const [activeTab, setActiveTab] = useState<'topics' | 'sources' | 'settings'>('topics');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadPreferences();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadPreferences = async () => {
    try {
      const [prefsResponse, sourcesResponse, settingsResponse] = await Promise.all([
        api.getPreferences(),
        api.getSources(),
        api.getSettings(),
      ]);
      setPreferences(prefsResponse.topics);
      setSources(sourcesResponse);
      setSettings(settingsResponse);
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

  const updatePriority = (topicId: number, priority: number) => {
    setPreferences(
      preferences.map((pref) =>
        pref.id === topicId ? { ...pref, priority } : pref
      )
    );
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
        priority: pref.priority,
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading preferences...</p>
        </div>
      </div>
    );
  }

  const activeTopics = preferences.filter((p) => p.is_active);
  const subscribedSources = sources.filter((s) => s.subscribed);

  const getPoliticalLeanColor = (lean: string | null) => {
    if (!lean) return 'bg-gray-100 text-gray-700';
    if (lean === 'left') return 'bg-blue-100 text-blue-700';
    if (lean === 'right') return 'bg-red-100 text-red-700';
    return 'bg-gray-100 text-gray-700';
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">⚙️ Preferences</h1>
              <p className="text-gray-600 mt-1">Customize your news experience</p>
            </div>
          </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              <button
                onClick={() => setActiveTab('topics')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'topics'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Topics ({activeTopics.length})
              </button>
              <button
                onClick={() => setActiveTab('sources')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'sources'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Sources ({subscribedSources.length})
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'settings'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Settings
              </button>
            </nav>
          </div>
        </div>

        {/* Summary Card */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg shadow-lg p-6 mb-6 text-white">
          <h2 className="text-xl font-semibold mb-2">Your Newsletter</h2>
          <p className="text-indigo-100">
            You&apos;re subscribed to <strong>{activeTopics.length}</strong> topics.
            Your daily digest will include articles from these topics based on
            your priority settings.
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
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Topic Preferences
              </h2>
              <p className="text-sm text-gray-600 mb-6">
                Toggle topics on/off and adjust their priority (1-10). Higher priority
                topics will appear more frequently in your newsletter.
              </p>

              <div className="space-y-4">
                {preferences.map((pref) => (
                  <div
                    key={pref.id}
                    className={`border rounded-lg p-4 transition-all ${
                      pref.is_active
                        ? 'border-indigo-200 bg-indigo-50'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <button
                            onClick={() => toggleActive(pref.id)}
                            className={`mr-3 w-12 h-6 rounded-full transition-colors relative ${
                              pref.is_active ? 'bg-indigo-600' : 'bg-gray-300'
                            }`}
                          >
                            <span
                              className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                                pref.is_active ? 'translate-x-6' : 'translate-x-0'
                              }`}
                            />
                          </button>

                          <div>
                            <h3 className="font-semibold text-gray-900">
                              {pref.name}
                            </h3>
                            {pref.description && (
                              <p className="text-sm text-gray-600 mt-1">
                                {pref.description}
                              </p>
                            )}
                          </div>
                        </div>

                        {pref.is_active && (
                          <div className="mt-4 ml-15">
                            <label className="text-sm font-medium text-gray-700 block mb-2">
                              Priority: {pref.priority}/10
                            </label>
                            <input
                              type="range"
                              min="1"
                              max="10"
                              value={pref.priority}
                              onChange={(e) =>
                                updatePriority(pref.id, parseInt(e.target.value))
                              }
                              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                              <span>Low</span>
                              <span>High</span>
                            </div>
                          </div>
                        )}
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
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {saving ? 'Saving...' : 'Save Preferences'}
              </button>
            </div>
          </>
        )}

        {activeTab === 'sources' && (
          <>
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Source Preferences
              </h2>
              <p className="text-sm text-gray-600 mb-6">
                Select which news sources you want to receive articles from. Only articles from selected sources will appear in your newsletter.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sources.map((source) => (
                  <div
                    key={source.source_id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      source.subscribed
                        ? 'border-indigo-200 bg-indigo-50'
                        : 'border-gray-200 bg-white hover:border-gray-300'
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
                            className="mr-3 w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
                          />
                          <div>
                            <h3 className="font-semibold text-gray-900">{source.name}</h3>
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {source.url}
                            </a>
                          </div>
                        </div>
                        <div className="mt-2 flex items-center gap-2 ml-8">
                          <span className="text-sm text-gray-600">
                            Trust Score: {source.trust_score?.toFixed(1) || 'N/A'}
                          </span>
                          {source.political_lean && (
                            <span className={`text-xs px-2 py-1 rounded ${getPoliticalLeanColor(source.political_lean)}`}>
                              {source.political_lean}
                            </span>
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
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {saving ? 'Saving...' : 'Save Sources'}
              </button>
            </div>
          </>
        )}

        {activeTab === 'settings' && (
          <>
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Newsletter Settings
              </h2>
              <p className="text-sm text-gray-600 mb-6">
                Customize how your newsletter is generated and delivered.
              </p>

              <div className="space-y-6">
                {/* Source Discovery Mode */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Source Discovery Mode
                  </label>
                  <p className="text-sm text-gray-600 mb-3">
                    Control whether to only use your selected sources or allow discovery of new sources.
                  </p>
                  <select
                    value={settings.source_discovery_mode}
                    onChange={(e) => setSettings({ ...settings, source_discovery_mode: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="none">None - Only use my selected sources</option>
                    <option value="some">Some - Occasionally include new sources</option>
                    <option value="open">Open - Freely discover new sources</option>
                  </select>
                </div>

                {/* Article Order Preference */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Article Order Preference
                  </label>
                  <p className="text-sm text-gray-600 mb-3">
                    Choose how articles are ordered in your newsletter.
                  </p>
                  <select
                    value={settings.article_order_preference}
                    onChange={(e) => setSettings({ ...settings, article_order_preference: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="good_first">Good News First - Positive sentiment first</option>
                    <option value="good_last">Good News Last - Negative sentiment first</option>
                    <option value="mixed">Mixed - Random order</option>
                  </select>
                </div>

                {/* Articles Per Topic */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Articles Per Topic: {settings.articles_per_topic_default}
                  </label>
                  <p className="text-sm text-gray-600 mb-3">
                    How many articles to include per topic in each newsletter (1-10).
                  </p>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={settings.articles_per_topic_default}
                    onChange={(e) => setSettings({ ...settings, articles_per_topic_default: parseInt(e.target.value) })}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
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
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </>
        )}

        {/* Info Card */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">
            📬 Newsletter Delivery
          </h3>
          <p className="text-sm text-blue-800">
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
