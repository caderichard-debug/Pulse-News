import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AnalyticsPage from '../page';
import { api } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  api: {
    getSentimentOverTime: jest.fn(),
    getBiasDistribution: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/analytics',
}));

// Mock Recharts
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

describe('AnalyticsPage', () => {
  const mockSentimentData = [
    {
      date: '2025-10-01',
      values: {
        Politics: 5.2,
        Technology: -2.1,
      },
    },
    {
      date: '2025-10-02',
      values: {
        Politics: 6.8,
        Technology: 3.4,
      },
    },
  ];

  const mockBiasData = [
    {
      week: 'Week 1',
      left: 10,
      center: 20,
      right: 5,
    },
    {
      week: 'Week 2',
      left: 15,
      center: 25,
      right: 10,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (api.getSentimentOverTime as jest.Mock).mockResolvedValue(mockSentimentData);
    (api.getBiasDistribution as jest.Mock).mockResolvedValue(mockBiasData);
    (api.getCurrentUser as jest.Mock).mockResolvedValue({
      name: 'John Doe',
      email: 'john@example.com',
    });
  });

  it('renders loading state initially', () => {
    render(<AnalyticsPage />);

    expect(screen.getByText(/loading analytics/i)).toBeInTheDocument();
  });

  it('loads and displays analytics data', async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('📊 Data Analysis')).toBeInTheDocument();
    });

    expect(api.getSentimentOverTime).toHaveBeenCalledWith(30);
    expect(api.getBiasDistribution).toHaveBeenCalledWith(4);
  });

  it('displays sentiment over time chart', async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('Sentiment Over Time')).toBeInTheDocument();
    });

    expect(screen.getByText(/Track daily sentiment trends across different political leans/)).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('displays bias distribution chart', async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('Source Bias Distribution')).toBeInTheDocument();
    });

    expect(screen.getByText(/This chart shows the political lean of articles from your news sources/)).toBeInTheDocument();
    expect(screen.getByTestId('area-chart')).toBeInTheDocument();
  });

  it('displays time range selector with default 30 days', async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('📊 Data Analysis')).toBeInTheDocument();
    });

    const thirtyDayButton = screen.getByRole('button', { name: '30d' });
    expect(thirtyDayButton).toHaveClass('bg-indigo-600', 'text-white');
  });

  it('changes time range when clicking buttons', async () => {
    const user = userEvent.setup();
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('📊 Data Analysis')).toBeInTheDocument();
    });

    const sevenDayButton = screen.getByRole('button', { name: '7d' });
    await user.click(sevenDayButton);

    expect(api.getSentimentOverTime).toHaveBeenCalledWith(7);
  });

  it('handles API errors gracefully', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    (api.getSentimentOverTime as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to load analytics data:', expect.any(Error));
    });

    consoleErrorSpy.mockRestore();
  });

  it('displays empty state when no sentiment data is available', async () => {
    (api.getSentimentOverTime as jest.Mock).mockResolvedValue([]);

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('No sentiment data available for this time range')).toBeInTheDocument();
    });
  });

  it('displays empty state when no bias data is available', async () => {
    (api.getBiasDistribution as jest.Mock).mockResolvedValue([]);

    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('No bias distribution data available')).toBeInTheDocument();
    });
  });

  it('shows all time range options', async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('📊 Data Analysis')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: '7d' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '30d' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '90d' })).toBeInTheDocument();
  });

  it('renders Navbar component', async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText('Pulse')).toBeInTheDocument();
    });
  });
});
