import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DashboardPage from '../page';
import { api } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  api: {
    getUserStats: jest.fn(),
    getSentimentOverTime: jest.fn(),
    getBiasDistribution: jest.fn(),
    clearToken: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/dashboard',
}));

// Mock Recharts to avoid rendering issues in tests
jest.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div data-testid="area-chart">{children}</div>,
  Area: () => <div data-testid="area" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
}));

describe('DashboardPage', () => {
  const mockUserStats = {
    articles_read: 42,
    newsletters_received: 10,
    topics_tracked: 5,
    sources_subscribed: 8,
    views_changed: 3,
  };

  const mockSentimentData = [
    { date: '2025-10-01', values: { Politics: -2.3, Technology: 4.5 } },
    { date: '2025-10-02', values: { Politics: 1.2, Technology: 3.8 } },
  ];

  const mockBiasData = [
    { week: '2025-09-23', left: 10, center: 15, right: 5 },
    { week: '2025-09-30', left: 12, center: 18, right: 8 },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (api.getUserStats as jest.Mock).mockResolvedValue(mockUserStats);
    (api.getSentimentOverTime as jest.Mock).mockResolvedValue(mockSentimentData);
    (api.getBiasDistribution as jest.Mock).mockResolvedValue(mockBiasData);
    (api.getCurrentUser as jest.Mock).mockResolvedValue({ name: 'Test User' });
  });

  it('should render loading state initially', () => {
    render(<DashboardPage />);
    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });

  it('should load and display user statistics', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(api.getUserStats).toHaveBeenCalled();
      expect(api.getSentimentOverTime).toHaveBeenCalled();
      expect(api.getBiasDistribution).toHaveBeenCalled();
    });

    // Check all stat cards are displayed
    expect(screen.getByText('42')).toBeInTheDocument(); // Articles read
    expect(screen.getByText('10')).toBeInTheDocument(); // Newsletters
    expect(screen.getByText('5')).toBeInTheDocument(); // Topics tracked
    expect(screen.getByText('8')).toBeInTheDocument(); // Sources
    expect(screen.getByText('3')).toBeInTheDocument(); // Views changed
  });

  it('should display stat card labels', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Articles Read')).toBeInTheDocument();
      expect(screen.getByText('Newsletters')).toBeInTheDocument();
      expect(screen.getByText('Topics Tracked')).toBeInTheDocument();
      expect(screen.getByText('Sources')).toBeInTheDocument();
      expect(screen.getByText('Views Changed')).toBeInTheDocument();
    });
  });

  it('should render sentiment chart with data', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Sentiment Over Time')).toBeInTheDocument();
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  it('should render bias distribution chart with data', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Source Bias Distribution')).toBeInTheDocument();
      expect(screen.getByTestId('area-chart')).toBeInTheDocument();
    });
  });

  it('should show "no data" message when sentiment data is empty', async () => {
    (api.getSentimentOverTime as jest.Mock).mockResolvedValue([]);

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/no sentiment data available/i)).toBeInTheDocument();
    });
  });

  it('should show "no data" message when bias data is empty', async () => {
    (api.getBiasDistribution as jest.Mock).mockResolvedValue([]);

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/no bias distribution data available/i)).toBeInTheDocument();
    });
  });

  describe('Time Range Selector', () => {
    it('should render time range buttons', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('7d')).toBeInTheDocument();
        expect(screen.getByText('30d')).toBeInTheDocument();
        expect(screen.getByText('90d')).toBeInTheDocument();
      });
    });

    it('should default to 30 days', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(api.getSentimentOverTime).toHaveBeenCalledWith(30);
      });

      await waitFor(() => {
        const button30d = screen.getByText('30d');
        expect(button30d).toHaveClass('bg-indigo-600');
      });
    });

    it('should change time range when clicking 7d button', async () => {
      const user = userEvent.setup();
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('7d')).toBeInTheDocument();
      });

      const button7d = screen.getByText('7d');
      await user.click(button7d);

      await waitFor(() => {
        expect(api.getSentimentOverTime).toHaveBeenCalledWith(7);
      });
    });

    it('should change time range when clicking 90d button', async () => {
      const user = userEvent.setup();
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('90d')).toBeInTheDocument();
      });

      const button90d = screen.getByText('90d');
      await user.click(button90d);

      await waitFor(() => {
        expect(api.getSentimentOverTime).toHaveBeenCalledWith(90);
      });
    });
  });

  describe('Navigation', () => {
    it('should render logout button', async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
      });
    });

    it('should handle logout', async () => {
      const user = userEvent.setup();
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
      });

      const logoutButton = screen.getByRole('button', { name: /logout/i });
      await user.click(logoutButton);

      expect(api.clearToken).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith('/');
    });

    it('should navigate to preferences page', async () => {
      const user = userEvent.setup();
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /preferences/i })).toBeInTheDocument();
      });

      const preferencesButton = screen.getByRole('button', { name: /preferences/i });
      await user.click(preferencesButton);

      expect(mockPush).toHaveBeenCalledWith('/preferences');
    });

    it('should navigate to home page', async () => {
      const user = userEvent.setup();
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /pulse/i })).toBeInTheDocument();
      });

      const homeButton = screen.getByRole('button', { name: /pulse/i });
      await user.click(homeButton);

      expect(mockPush).toHaveBeenCalledWith('/dashboard');
    });
  });

  describe('Error Handling', () => {
    it('should redirect to login on 401 error', async () => {
      (api.getUserStats as jest.Mock).mockRejectedValue(new Error('401'));

      render(<DashboardPage />);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });

    it('should redirect to login on 403 error', async () => {
      (api.getUserStats as jest.Mock).mockRejectedValue(new Error('403'));

      render(<DashboardPage />);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });

    it('should handle generic errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (api.getUserStats as jest.Mock).mockRejectedValue(new Error('Network error'));

      render(<DashboardPage />);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to load dashboard data:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });
});
