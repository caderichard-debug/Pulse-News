import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FeedPage from '../page';
import { api } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  api: {
    getFeedArticles: jest.fn(),
    getFeedTopics: jest.fn(),
    getFeedSources: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/feed',
}));

describe('FeedPage', () => {
  const mockArticles = [
    {
      id: 1,
      title: 'Test Article 1',
      url: 'https://example.com/1',
      published_at: '2025-10-03T10:00:00Z',
      source_name: 'Reuters',
      source_id: 1,
      topic_category: 'Politics',
      summary: 'This is a test article summary',
      sentiment_score: 5.2,
      political_lean: 'center',
      primary_framework: 'Individual Liberty vs Collective Welfare',
      framework_position: 3,
      read_time_minutes: 5,
      stats_count: 3,
      stats_verified_count: 2,
      has_stats: true,
    },
    {
      id: 2,
      title: 'Test Article 2',
      url: 'https://example.com/2',
      published_at: '2025-10-02T15:00:00Z',
      source_name: 'BBC',
      source_id: 2,
      topic_category: 'Technology',
      summary: 'Another test article',
      sentiment_score: -2.5,
      political_lean: 'left',
      primary_framework: null,
      framework_position: null,
      read_time_minutes: null,
      stats_count: 0,
      stats_verified_count: 0,
      has_stats: false,
    },
  ];

  const mockFeedResponse = {
    articles: mockArticles,
    total_count: 50,
    page: 1,
    page_size: 20,
  };

  const mockTopics = [
    { name: 'Politics', article_count: 25 },
    { name: 'Technology', article_count: 15 },
  ];

  const mockSources = [
    { id: 1, name: 'Reuters', url: 'https://reuters.com', article_count: 30 },
    { id: 2, name: 'BBC', url: 'https://bbc.com', article_count: 20 },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (api.getFeedArticles as jest.Mock).mockResolvedValue(mockFeedResponse);
    (api.getFeedTopics as jest.Mock).mockResolvedValue(mockTopics);
    (api.getFeedSources as jest.Mock).mockResolvedValue(mockSources);
    (api.getCurrentUser as jest.Mock).mockResolvedValue({ name: 'Test User' });
  });

  it('should render loading state initially', () => {
    render(<FeedPage />);
    expect(screen.getByText(/loading articles/i)).toBeInTheDocument();
  });

  it('should load and display articles', async () => {
    render(<FeedPage />);

    await waitFor(() => {
      expect(api.getFeedArticles).toHaveBeenCalled();
      expect(api.getFeedTopics).toHaveBeenCalled();
      expect(api.getFeedSources).toHaveBeenCalled();
    });

    expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    expect(screen.getByText('Test Article 2')).toBeInTheDocument();
  });

  it('should display article metadata', async () => {
    render(<FeedPage />);

    await waitFor(() => {
      expect(screen.getByText('Reuters')).toBeInTheDocument();
      expect(screen.getByText('BBC')).toBeInTheDocument();
      expect(screen.getByText('Politics')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });
  });

  it('should display sentiment scores', async () => {
    render(<FeedPage />);

    await waitFor(() => {
      expect(screen.getByText('+5.2')).toBeInTheDocument();
      expect(screen.getByText('-2.5')).toBeInTheDocument();
    });
  });

  it('should display article bias', async () => {
    render(<FeedPage />);

    await waitFor(() => {
      expect(screen.getByText('Center')).toBeInTheDocument();
      expect(screen.getByText('Left')).toBeInTheDocument();
    });
  });

  it('should display results count', async () => {
    render(<FeedPage />);

    await waitFor(() => {
      expect(screen.getByText(/showing 1 - 20 of 50 articles/i)).toBeInTheDocument();
    });
  });

  it('should display statistics section for articles with stats', async () => {
    render(<FeedPage />);

    await waitFor(() => {
      // First article has stats
      expect(screen.getByText('📊 Statistics:')).toBeInTheDocument();
      expect(screen.getByText('3 found')).toBeInTheDocument();
      expect(screen.getByText('2 verified')).toBeInTheDocument();
    });
  });

  it('should not display statistics section for articles without stats', async () => {
    const noStatsResponse = {
      ...mockFeedResponse,
      articles: [mockArticles[1]], // Article 2 has no stats
    };
    (api.getFeedArticles as jest.Mock).mockResolvedValue(noStatsResponse);

    render(<FeedPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Article 2')).toBeInTheDocument();
    });

    // Should not show statistics section
    expect(screen.queryByText('📊 Statistics:')).not.toBeInTheDocument();
  });

  it('should filter by verified statistics when checkbox is checked', async () => {
    const user = userEvent.setup();
    render(<FeedPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });

    // Find and click the verified stats checkbox
    const checkbox = screen.getByLabelText('Show only articles with verified statistics');
    await user.click(checkbox);

    // Should call API with only_verified_stats parameter
    await waitFor(() => {
      expect(api.getFeedArticles).toHaveBeenCalledWith(
        expect.objectContaining({
          only_verified_stats: true,
          page: 1,
        })
      );
    });
  });

  describe('Filters', () => {
    it('should render topic filter with options', async () => {
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Topic')).toBeInTheDocument();
      });

      // Wait for options to load
      await waitFor(() => {
        expect(screen.getByRole('option', { name: /all topics/i })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: /politics \(25\)/i })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: /technology \(15\)/i })).toBeInTheDocument();
      });
    });

    it('should render source filter with options', async () => {
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Source')).toBeInTheDocument();
      });

      // Wait for options to load
      await waitFor(() => {
        expect(screen.getByRole('option', { name: /all sources/i })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: /reuters \(30\)/i })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: /bbc \(20\)/i })).toBeInTheDocument();
      });
    });

    it('should render article bias filter', async () => {
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Political Lean')).toBeInTheDocument();
      });

      expect(screen.getByRole('option', { name: /all leans/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Left' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Center' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Right' })).toBeInTheDocument();
    });

    it('should render sort filter', async () => {
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Sort By')).toBeInTheDocument();
      });

      expect(screen.getByRole('option', { name: /newest/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /oldest/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /most positive/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /most negative/i })).toBeInTheDocument();
    });

    it('should filter by topic', async () => {
      const user = userEvent.setup();
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics (25)')).toBeInTheDocument();
      });

      // Get all selects and find the first one (topic select)
      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[0], 'Politics');

      await waitFor(() => {
        expect(api.getFeedArticles).toHaveBeenCalledWith(
          expect.objectContaining({ topic: 'Politics' })
        );
      });
    });

    it('should filter by source', async () => {
      const user = userEvent.setup();
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Reuters (30)')).toBeInTheDocument();
      });

      // Get all selects and find the second one (source select)
      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[1], '1');

      await waitFor(() => {
        expect(api.getFeedArticles).toHaveBeenCalledWith(
          expect.objectContaining({ source_id: 1 })
        );
      });
    });

    it('should filter by article bias', async () => {
      const user = userEvent.setup();
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Political Lean')).toBeInTheDocument();
      });

      // Get all selects and find the third one (article bias select)
      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[2], 'left');

      await waitFor(() => {
        expect(api.getFeedArticles).toHaveBeenCalledWith(
          expect.objectContaining({ political_lean: 'left' })
        );
      });
    });

    it('should change sort order', async () => {
      const user = userEvent.setup();
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Sort By')).toBeInTheDocument();
      });

      // Get all selects and find the fourth one (sort select)
      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[3], 'sentiment_high');

      await waitFor(() => {
        expect(api.getFeedArticles).toHaveBeenCalledWith(
          expect.objectContaining({ sort_by: 'sentiment_high' })
        );
      });
    });

    it('should reset page when changing filters', async () => {
      const user = userEvent.setup();
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Politics (25)')).toBeInTheDocument();
      });

      // Get topic select and change it
      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[0], 'Politics');

      await waitFor(() => {
        expect(api.getFeedArticles).toHaveBeenCalledWith(
          expect.objectContaining({ page: 1 })
        );
      });
    });
  });

  describe('Pagination', () => {
    it('should render pagination controls when needed', async () => {
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText(/of 3/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /first/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /last/i })).toBeInTheDocument();
      });
    });

    it('should disable previous button on first page', async () => {
      render(<FeedPage />);

      await waitFor(() => {
        const prevButton = screen.getByRole('button', { name: /previous/i });
        expect(prevButton).toBeDisabled();
      });
    });

    it('should enable next button when more pages available', async () => {
      render(<FeedPage />);

      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        expect(nextButton).not.toBeDisabled();
      });
    });

    it('should navigate to next page', async () => {
      const user = userEvent.setup();
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
      });

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(api.getFeedArticles).toHaveBeenCalledWith(
          expect.objectContaining({ page: 2 })
        );
      });
    });

    it('should not render pagination when results fit on one page', async () => {
      (api.getFeedArticles as jest.Mock).mockResolvedValue({
        articles: mockArticles,
        total_count: 2,
        page: 1,
        page_size: 20,
      });

      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Test Article 1')).toBeInTheDocument();
      });

      expect(screen.queryByText(/page/i)).not.toBeInTheDocument();
    });
  });

  describe('Article Navigation', () => {
    it('should navigate to article detail when clicking article card', async () => {
      const user = userEvent.setup();
      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText('Test Article 1')).toBeInTheDocument();
      });

      const articleCard = screen.getByText('Test Article 1').closest('div');
      if (articleCard) {
        await user.click(articleCard);
      }

      expect(mockPush).toHaveBeenCalledWith('/article/1');
    });
  });

  describe('Empty States', () => {
    it('should display "no articles" message when results are empty', async () => {
      (api.getFeedArticles as jest.Mock).mockResolvedValue({
        articles: [],
        total_count: 0,
        page: 1,
        page_size: 20,
      });

      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText(/no articles found with these filters/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when feed fails to load', async () => {
      (api.getFeedArticles as jest.Mock).mockRejectedValue(new Error('Network error'));

      render(<FeedPage />);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it('should handle filter loading errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      (api.getFeedTopics as jest.Mock).mockRejectedValue(new Error('Failed to load topics'));

      render(<FeedPage />);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to load filters:', expect.any(Error));
      });

      consoleSpy.mockRestore();
    });
  });
});
