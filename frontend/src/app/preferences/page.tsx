'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface TopicPreference {
  id: number;
  name: string;
  description: string;
  priority: number;
  is_active: boolean;
}

export default function PreferencesPage() {
  const router = useRouter();
  const [preferences, setPreferences] = useState<TopicPreference[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadPreferences();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadPreferences = async () => {
    try {
      const response = await api.getPreferences();
      setPreferences(response.topics);
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

  const handleLogout = () => {
    api.clearToken();
    router.push('/login');
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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">⚡ Pulse</h1>
              <p className="text-gray-600 mt-1">Your Newsletter Preferences</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
            >
              Logout
            </button>
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

        {/* Topics List */}
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
  );
}
