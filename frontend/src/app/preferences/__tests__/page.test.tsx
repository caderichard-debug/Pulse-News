import { render, screen, waitFor } from '@/__tests__/test-utils';
import userEvent from '@testing-library/user-event';
import PreferencesPage from '../page';
import { api } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  api: {
    getPreferences: jest.fn(),
    getSources: jest.fn(),
    getSettings: jest.fn(),
    updatePreferences: jest.fn(),
    updateSourcePreferences: jest.fn(),
    updateSettings: jest.fn(),
    clearToken: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

// Mock next/navigation
const mockPush = jest.fn();
const mockSearchParams = new URLSearchParams();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/preferences',
  useSearchParams: () => mockSearchParams,
}));

describe('PreferencesPage', () => {
  const mockPreferences = {
    user_id: 1,
    topics: [
      { id: 1, name: 'Politics', description: 'Political news', is_active: true },
      { id: 2, name: 'Technology', description: 'Tech news', is_active: false },
    ],
  };

  const mockSources = [
    { source_id: 1, name: 'Reuters', url: 'https://reuters.com', trust_score: 0.95, organizational_bias: null, subscribed: true },
    { source_id: 2, name: 'BBC', url: 'https://bbc.com', trust_score: 0.92, organizational_bias: 'center', subscribed: false },
  ];

  const mockSettings = {
    source_discovery_mode: 'some',
    article_order_preference: 'mixed',
    articles_per_topic_default: 5,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (api.getPreferences as jest.Mock).mockResolvedValue(mockPreferences);
    (api.getSources as jest.Mock).mockResolvedValue(mockSources);
    (api.getSettings as jest.Mock).mockResolvedValue(mockSettings);
    (api.getCurrentUser as jest.Mock).mockResolvedValue({ name: 'Test User' });
  });

  it('should render loading state initially', () => {
    render(<PreferencesPage />);
    expect(screen.getByText(/loading preferences/i)).toBeInTheDocument();
  });

  it('should load and display preferences data', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(api.getPreferences).toHaveBeenCalled();
      expect(api.getSources).toHaveBeenCalled();
      expect(api.getSettings).toHaveBeenCalled();
    });

    expect(screen.getByText('Politics')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
  });

  it('should show active topic count in tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Topics \(1\)/i)).toBeInTheDocument();
    });
  });

  it('should toggle topic active state', async () => {
    const user = userEvent.setup();
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    // Find and click the toggle button for Technology
    const technologySection = screen.getByText('Technology').closest('div[class*="border"]');
    const toggleButton = technologySection?.querySelector('button');

    if (toggleButton) {
      await user.click(toggleButton);
    }

    // The topic should now be active (visual state change - border color changes)
    await waitFor(() => {
      expect(technologySection?.className).toMatch(/border-indigo/);
    });
  });

  it('should save preferences when save button is clicked', async () => {
    const user = userEvent.setup();
    (api.updatePreferences as jest.Mock).mockResolvedValue({ message: 'Success' });

    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText('Politics')).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: /save preferences/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(api.updatePreferences).toHaveBeenCalled();
      expect(screen.getByText(/preferences saved successfully/i)).toBeInTheDocument();
    });
  });

  describe('Sources Tab', () => {
    it('should switch to sources tab', async () => {
      const user = userEvent.setup();
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const sourcesTab = screen.getByRole('button', { name: /sources \(/i });
      await user.click(sourcesTab);

      await waitFor(() => {
        expect(screen.getByText('Reuters')).toBeInTheDocument();
        expect(screen.getByText('BBC')).toBeInTheDocument();
      });
    });

    it('should display trust scores', async () => {
      const user = userEvent.setup();
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const sourcesTab = screen.getByRole('button', { name: /sources \(/i });
      await user.click(sourcesTab);

      await waitFor(() => {
        const trustScores = screen.getAllByText(/trust score: 0.9/i);
        expect(trustScores.length).toBeGreaterThan(0);
      });
    });

    it('should toggle source subscription', async () => {
      const user = userEvent.setup();
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const sourcesTab = screen.getByRole('button', { name: /sources \(/i });
      await user.click(sourcesTab);

      await waitFor(() => {
        const bbcCheckbox = screen.getAllByRole('checkbox').find(cb =>
          cb.closest('div')?.textContent?.includes('BBC')
        );
        expect(bbcCheckbox).not.toBeChecked();
      });
    });

    it('should save source preferences', async () => {
      const user = userEvent.setup();
      (api.updateSourcePreferences as jest.Mock).mockResolvedValue({ subscribed_count: 1 });

      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const sourcesTab = screen.getByRole('button', { name: /sources \(/i });
      await user.click(sourcesTab);

      await waitFor(() => {
        expect(screen.getByText('Reuters')).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /save sources/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(api.updateSourcePreferences).toHaveBeenCalled();
      });
    });
  });

  describe('Settings Tab', () => {
    it('should switch to settings tab', async () => {
      const user = userEvent.setup();
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const settingsTab = screen.getByRole('button', { name: /Settings/i });
      await user.click(settingsTab);

      await waitFor(() => {
        expect(screen.getByText(/source discovery mode/i)).toBeInTheDocument();
        expect(screen.getByText(/article order preference/i)).toBeInTheDocument();
      });
    });

    it('should display current settings values', async () => {
      const user = userEvent.setup();
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const settingsTab = screen.getByRole('button', { name: /Settings/i });
      await user.click(settingsTab);

      await waitFor(() => {
        const discoverySelect = screen.getByDisplayValue(/some - occasionally include new sources/i);
        expect(discoverySelect).toBeInTheDocument();
      });
    });

    it('should save settings', async () => {
      const user = userEvent.setup();
      (api.updateSettings as jest.Mock).mockResolvedValue({ message: 'Success' });

      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const settingsTab = screen.getByRole('button', { name: /Settings/i });
      await user.click(settingsTab);

      await waitFor(() => {
        expect(screen.getByText(/source discovery mode/i)).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /save settings/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(api.updateSettings).toHaveBeenCalled();
      });
    });
  });

  it('should redirect to login on 401 error', async () => {
    (api.getPreferences as jest.Mock).mockRejectedValue(new Error('401'));

    render(<PreferencesPage />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  // Logout functionality is tested in Navbar tests
  it('should render navbar with logout functionality', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText('Politics')).toBeInTheDocument();
    });

    // Navbar should be rendered (logout tested in Navbar.test.tsx)
    expect(screen.getByText('Pulse')).toBeInTheDocument();
  });

  describe('Tab Persistence', () => {
    it('should initialize with topics tab when no URL param is present', async () => {
      mockSearchParams.delete('tab');
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });
    });

    it('should initialize with the tab specified in URL param', async () => {
      mockSearchParams.set('tab', 'sources');
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Reuters')).toBeInTheDocument();
        expect(screen.getByText('BBC')).toBeInTheDocument();
      });
    });

    it('should update URL when switching tabs', async () => {
      mockSearchParams.delete('tab');
      const user = userEvent.setup();
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const sourcesTab = screen.getByRole('button', { name: /sources \(/i });
      await user.click(sourcesTab);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/preferences?tab=sources', { scroll: false });
      });
    });

    it('should update URL when switching to settings tab', async () => {
      mockSearchParams.delete('tab');
      const user = userEvent.setup();
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const settingsTab = screen.getByRole('button', { name: /Settings/i });
      await user.click(settingsTab);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/preferences?tab=settings', { scroll: false });
      });
    });

    it('should update URL when switching to account tab', async () => {
      mockSearchParams.delete('tab');
      const user = userEvent.setup();
      render(<PreferencesPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics')).toBeInTheDocument();
      });

      const accountTab = screen.getByRole('button', { name: /Account/i });
      await user.click(accountTab);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/preferences?tab=account', { scroll: false });
      });
    });
  });
});

// Tests for Sources sub-tabs and dynamic newsletter card
describe('PreferencesPage - Sources Sub-tabs', () => {
  const mockPreferences = {
    user_id: 1,
    topics: [
      { id: 1, name: 'Politics', description: 'Political news', is_active: true },
    ],
  };

  const mockSourcesWithRecommended = [
    { 
      source_id: 1, 
      name: 'Recommended Source', 
      url: 'https://recommended.com', 
      trust_score: 0.95, 
      organizational_bias: 'center', 
      is_recommended: true,
      subscribed: true 
    },
    { 
      source_id: 2, 
      name: 'Community Source', 
      url: 'https://community.com', 
      trust_score: 0.8, 
      organizational_bias: 'left',
      is_recommended: false, 
      subscribed: false 
    },
  ];

  const mockSettings = {
    source_discovery_mode: 'some',
    article_order_preference: 'mixed',
    articles_per_topic_default: 5,
  };

  const mockUser = {
    name: 'Test User',
    email: 'test@example.com',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (api.getPreferences as jest.Mock).mockResolvedValue(mockPreferences);
    (api.getSources as jest.Mock).mockResolvedValue(mockSourcesWithRecommended);
    (api.getSettings as jest.Mock).mockResolvedValue(mockSettings);
    (api.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
    (api.updateSourcePreferences as jest.Mock).mockResolvedValue({});
    (api.createSourceFromURL as jest.Mock).mockResolvedValue({
      message: 'Source created successfully',
      already_existed: false,
      source: { id: 3, name: 'New Source', is_recommended: false },
    });
  });

  it('displays sources sub-tabs when on sources tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const sourcesTab = screen.getByRole('button', { name: /Sources/ });
    await userEvent.click(sourcesTab);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /✅ Recommended/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /🌐 Community/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /➕ Add Source/ })).toBeInTheDocument();
    });
  });

  it('shows recommended sources in recommended sub-tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const sourcesTab = screen.getByRole('button', { name: /Sources/ });
    await userEvent.click(sourcesTab);

    await waitFor(() => {
      expect(screen.getByText('Recommended Source')).toBeInTheDocument();
      expect(screen.queryByText('Community Source')).not.toBeInTheDocument();
    });
  });

  it('shows community sources in community sub-tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const sourcesTab = screen.getByRole('button', { name: /Sources/ });
    await userEvent.click(sourcesTab);

    const communitySubTab = screen.getByRole('button', { name: /🌐 Community/ });
    await userEvent.click(communitySubTab);

    await waitFor(() => {
      expect(screen.getByText('Community Source')).toBeInTheDocument();
      expect(screen.queryByText('Recommended Source')).not.toBeInTheDocument();
    });
  });

  it('shows add source form in add sub-tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const sourcesTab = screen.getByRole('button', { name: /Sources/ });
    await userEvent.click(sourcesTab);

    const addSubTab = screen.getByRole('button', { name: /➕ Add Source/ });
    await userEvent.click(addSubTab);

    await waitFor(() => {
      expect(screen.getByText('Add a News Source')).toBeInTheDocument();
      expect(screen.getByLabelText(/Article URL/)).toBeInTheDocument();
    });
  });

  it('allows subscribing/unsubscribing to sources', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const sourcesTab = screen.getByRole('button', { name: /Sources/ });
    await userEvent.click(sourcesTab);

    await waitFor(() => {
      expect(screen.getByText('Recommended Source')).toBeInTheDocument();
    });

    const checkbox = screen.getByRole('checkbox', { name: /Recommended Source/ });
    await userEvent.click(checkbox);

    const saveButton = screen.getByRole('button', { name: /Save Sources/ });
    await userEvent.click(saveButton);

    await waitFor(() => {
      expect(api.updateSourcePreferences).toHaveBeenCalled();
    });
  });

  it('submits new source from add sub-tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const sourcesTab = screen.getByRole('button', { name: /Sources/ });
    await userEvent.click(sourcesTab);

    const addSubTab = screen.getByRole('button', { name: /➕ Add Source/ });
    await userEvent.click(addSubTab);

    await waitFor(() => {
      expect(screen.getByLabelText(/Article URL/)).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText(/Article URL/);
    await userEvent.type(urlInput, 'https://example.com/article');

    const addButton = screen.getByRole('button', { name: /Add Source/ });
    await userEvent.click(addButton);

    await waitFor(() => {
      expect(api.createSourceFromURL).toHaveBeenCalledWith('https://example.com/article');
    });
  });
});

describe('PreferencesPage - Dynamic Newsletter Card', () => {
  const mockPreferences = {
    user_id: 1,
    topics: [
      { id: 1, name: 'Politics', description: 'Political news', is_active: true },
      { id: 2, name: 'Technology', description: 'Tech news', is_active: true },
    ],
  };

  const mockSources = [
    { source_id: 1, name: 'Reuters', url: 'https://reuters.com', trust_score: 0.95, organizational_bias: null, is_recommended: true, subscribed: true },
    { source_id: 2, name: 'BBC', url: 'https://bbc.com', trust_score: 0.92, organizational_bias: 'center', is_recommended: true, subscribed: true },
  ];

  const mockSettings = {
    source_discovery_mode: 'some',
    article_order_preference: 'mixed',
    articles_per_topic_default: 5,
  };

  const mockUser = {
    name: 'Test User',
    email: 'test@example.com',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (api.getPreferences as jest.Mock).mockResolvedValue(mockPreferences);
    (api.getSources as jest.Mock).mockResolvedValue(mockSources);
    (api.getSettings as jest.Mock).mockResolvedValue(mockSettings);
    (api.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
  });

  it('shows topics card content on topics tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/📚 Your Newsletter Topics/)).toBeInTheDocument();
      expect(screen.getByText(/You're subscribed to/)).toBeInTheDocument();
      expect(screen.getByText(/2/)).toBeInTheDocument();
    });
  });

  it('shows sources card content on sources tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const sourcesTab = screen.getByRole('button', { name: /Sources/ });
    await userEvent.click(sourcesTab);

    await waitFor(() => {
      expect(screen.getByText(/📰 Your Newsletter Sources/)).toBeInTheDocument();
      expect(screen.getByText(/You're subscribed to/)).toBeInTheDocument();
    });
  });

  it('shows settings card content on settings tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const settingsTab = screen.getByRole('button', { name: /Settings/ });
    await userEvent.click(settingsTab);

    await waitFor(() => {
      expect(screen.getByText(/⚙️ Newsletter Settings/)).toBeInTheDocument();
      expect(screen.getByText(/Customize how your daily newsletter/)).toBeInTheDocument();
    });
  });

  it('shows account card content on account tab', async () => {
    render(<PreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText(/Politics/)).toBeInTheDocument();
    });

    const accountTab = screen.getByRole('button', { name: /Account/ });
    await userEvent.click(accountTab);

    await waitFor(() => {
      expect(screen.getByText(/👤 Account Settings/)).toBeInTheDocument();
      expect(screen.getByText(/Manage your profile/)).toBeInTheDocument();
    });
  });
});
