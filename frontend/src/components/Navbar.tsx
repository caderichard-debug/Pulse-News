'use client';

import { useRouter, usePathname } from 'next/navigation';
import { api } from '@/lib/api';

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    api.clearToken();
    router.push('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Feed', path: '/feed', icon: '📰' },
    { name: 'Preferences', path: '/preferences', icon: '⚙️' },
    { name: 'How It Works', path: '/how-it-works', icon: '💡' },
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <button
              onClick={() => router.push('/dashboard')}
              className="text-2xl font-bold text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              Pulse
            </button>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  pathname === item.path
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <span className="mr-1">{item.icon}</span>
                {item.name}
              </button>
            ))}
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
