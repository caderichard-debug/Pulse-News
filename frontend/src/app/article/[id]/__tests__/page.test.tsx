import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ArticleDetailPage from '../page';
import { api } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  api: {
    getArticleDetail: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

// Mock next/navigation
const mockPush = jest.fn();
const mockParams = { id: '1' };
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useParams: () => mockParams,
  usePathname: () => '/article/1',
}));

describe('ArticleDetailPage', () => {
  const mockArticleDetail = {
    id: 1,
    title: 'Test Article Title',
    url: 'https://example.com/article',
    published_at: '2025-10-03T10:00:00Z',
    source_name: 'Reuters',
    source_url: 'https://reuters.com',
    topic_category: 'Politics',
    content_preview: 'Article content preview...',
    summary: 'This is a comprehensive article summary that provides an overview of the main points discussed.',
    sentiment_score: 5.2,
    political_lean: 'center',
    read_time_minutes: 8,
    statistics: [
      {
        statistic: '50% of Americans support this policy',
        verification_status: 'verified',
        confidence: 0.85,
        source_name: 'Pew Research',
        source_url: 'https://pewresearch.org',
        source_credibility_score: 0.9,
        fact_check_status: null,
        fact_check_source: null,
      },
      {
        statistic: 'GDP grew by 3% this quarter',
        verification_status: 'unverified',
        confidence: null,
        source_name: null,
        source_url: null,
        source_credibility_score: null,
        fact_check_status: null,
        fact_check_source: null,
      },
    ],
    frameworks: [
      {
        framework_id: 1,
        framework_name: 'Individual Liberty vs Collective Welfare',
        left_position: 'Individual Liberty',
        right_position: 'Collective Welfare',
        position_on_axis: 3,
        relevance_score: 0.85,
        explanation: 'This policy leans toward collective welfare over individual freedom.',
      },
    ],
    related_articles: [
      {
        id: 2,
        title: 'Related Article 1',
        source_name: 'BBC',
        published_at: '2025-10-02T15:00:00Z',
        sentiment_score: -2.5,
        political_lean: 'left',
        url: 'https://bbc.com/article',
      },
      {
        id: 3,
        title: 'Related Article 2',
        source_name: 'CNN',
        published_at: '2025-10-01T12:00:00Z',
        sentiment_score: 1.2,
        political_lean: 'center',
        url: 'https://cnn.com/article',
      },
    ],
    context: {
      background: 'Historical context about this issue...',
      key_players: 'Major figures involved include...',
      timeline: 'Key events in chronological order...',
      significance: 'This matters because...',
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (api.getArticleDetail as jest.Mock).mockResolvedValue(mockArticleDetail);
    (api.getCurrentUser as jest.Mock).mockResolvedValue({ name: 'Test User' });
  });

  it('should render loading state initially', () => {
    render(<ArticleDetailPage />);
    expect(screen.getByText(/loading article/i)).toBeInTheDocument();
  });

  it('should load and display article details', async () => {
    render(<ArticleDetailPage />);

    await waitFor(() => {
      expect(api.getArticleDetail).toHaveBeenCalledWith(1);
    });

    expect(screen.getByText('Test Article Title')).toBeInTheDocument();
    expect(screen.getByText('Reuters')).toBeInTheDocument();
    expect(screen.getByText('Politics')).toBeInTheDocument();
  });

  describe('Article Header', () => {
    it('should display article metadata', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Test Article Title')).toBeInTheDocument();
      });

      expect(screen.getByText('Reuters')).toBeInTheDocument();
      expect(screen.getByText('Politics')).toBeInTheDocument();
      expect(screen.getByText('8 min read')).toBeInTheDocument();
    });

    it('should render source link', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const sourceLink = screen.getByRole('link', { name: /reuters/i });
        expect(sourceLink).toHaveAttribute('href', 'https://reuters.com');
        expect(sourceLink).toHaveAttribute('target', '_blank');
      });
    });

    it('should render original article link', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const articleLink = screen.getByRole('link', { name: /read original article/i });
        expect(articleLink).toHaveAttribute('href', 'https://example.com/article');
        expect(articleLink).toHaveAttribute('target', '_blank');
      });
    });
  });

  describe('Analysis Section', () => {
    it('should display sentiment score', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Sentiment Score')).toBeInTheDocument();
        expect(screen.getByText('+5.2')).toBeInTheDocument();
      });
    });

    it('should display political lean', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Political Lean')).toBeInTheDocument();
        expect(screen.getByText('Center')).toBeInTheDocument();
      });
    });
  });

  describe('Summary Section', () => {
    it('should display article summary', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/this is a comprehensive article summary/i)).toBeInTheDocument();
      });
    });
  });

  describe('Verified Statistics', () => {
    it('should display statistics section', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Key Statistics')).toBeInTheDocument();
      });
    });

    it('should display verified statistic with badge', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('50% of Americans support this policy')).toBeInTheDocument();
        expect(screen.getByText('Verified')).toBeInTheDocument();
      });
    });

    it('should display unverified statistic', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('GDP grew by 3% this quarter')).toBeInTheDocument();
        expect(screen.getByText('Pending')).toBeInTheDocument();
      });
    });

    it('should display source information for verified statistics', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const sourceLink = screen.getByRole('link', { name: /pew research/i });
        expect(sourceLink).toHaveAttribute('href', 'https://pewresearch.org');
      });
    });

    it('should display credibility rating as X/5 format', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        // 0.9 * 5 = 4.5
        expect(screen.getByText(/4\.5\/5/)).toBeInTheDocument();
      });
    });

    it('should display confidence percentage', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
      });
    });
  });

  describe('Ethical Framework Analysis', () => {
    it('should display ethical framework section header', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Ethical Framework Analysis')).toBeInTheDocument();
      });
    });

    it('should display framework introduction text', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/understanding these frameworks helps you think critically/i)).toBeInTheDocument();
      });
    });

    it('should display framework name and positions', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Individual Liberty vs Collective Welfare')).toBeInTheDocument();
        expect(screen.getByText('Individual Liberty')).toBeInTheDocument();
        expect(screen.getByText('Collective Welfare')).toBeInTheDocument();
      });
    });

    it('should display relevance percentage badge', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('85% relevant')).toBeInTheDocument();
      });
    });

    it('should display framework explanation', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/this policy leans toward collective welfare/i)).toBeInTheDocument();
      });
    });

    it('should display position on axis with label', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/Position: \+3/)).toBeInTheDocument();
      });
    });

    it('should display position interpretation for right-leaning position', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/Strongly aligned with Collective Welfare/i)).toBeInTheDocument();
      });
    });

    it('should display gradient visual axis', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const framework = screen.getByText('Individual Liberty vs Collective Welfare');
        const container = framework.closest('.bg-gradient-to-br');
        expect(container).toBeInTheDocument();
      });
    });
  });

  describe('Background & Context Section', () => {
    it('should display context section with blue theme', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Background & Context')).toBeInTheDocument();
      });
    });

    it('should display all subsection headers with emojis', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/📖/)).toBeInTheDocument();
        expect(screen.getByText('Background')).toBeInTheDocument();
        expect(screen.getByText(/👥/)).toBeInTheDocument();
        expect(screen.getByText('Key Players')).toBeInTheDocument();
        expect(screen.getByText(/⏱️/)).toBeInTheDocument();
        expect(screen.getByText('Timeline')).toBeInTheDocument();
        expect(screen.getAllByText(/💡/).length).toBeGreaterThan(0);
        expect(screen.getByText('Why This Matters')).toBeInTheDocument();
      });
    });

    it('should display context content', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/historical context about this issue/i)).toBeInTheDocument();
        expect(screen.getByText(/major figures involved include/i)).toBeInTheDocument();
        expect(screen.getByText(/key events in chronological order/i)).toBeInTheDocument();
        expect(screen.getByText(/this matters because/i)).toBeInTheDocument();
      });
    });

    it('should render timeline with visual elements', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const timeline = screen.getByText(/key events in chronological order/i);
        expect(timeline).toBeInTheDocument();
        const container = timeline.closest('div');
        expect(container).toBeInTheDocument();
      });
    });
  });

  describe('Cross-Source Coverage (Coverage Comparison)', () => {
    it('should display coverage comparison section with header', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Cross-Source Coverage')).toBeInTheDocument();
      });
    });

    it('should display source count description', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        // 2 related + 1 current = 3 sources
        expect(screen.getByText(/this story is being covered by 3 sources/i)).toBeInTheDocument();
      });
    });

    it('should display coverage comparison intro text', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/compare how different outlets frame the same story/i)).toBeInTheDocument();
      });
    });

    it('should display related article titles and sources', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Related Article 1')).toBeInTheDocument();
        expect(screen.getByText('Related Article 2')).toBeInTheDocument();
        expect(screen.getByText(/bbc/i)).toBeInTheDocument();
        expect(screen.getByText(/cnn/i)).toBeInTheDocument();
      });
    });

    it('should display sentiment scores for related articles as badges', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('-2.5')).toBeInTheDocument();
        expect(screen.getByText('+1.2')).toBeInTheDocument();
      });
    });

    it('should display political lean badges for related articles', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const leanBadges = screen.getAllByText(/left|center/i);
        expect(leanBadges.length).toBeGreaterThan(0);
      });
    });

    it('should navigate to related article when clicked', async () => {
      const user = userEvent.setup();
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Related Article 1')).toBeInTheDocument();
      });

      const relatedCard = screen.getByText('Related Article 1').closest('div');
      if (relatedCard) {
        await user.click(relatedCard);
      }

      expect(mockPush).toHaveBeenCalledWith('/article/2');
    });

    it('should apply purple theme styling to coverage section', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const coverageHeader = screen.getByText('Cross-Source Coverage');
        const container = coverageHeader.closest('.bg-purple-50');
        expect(container).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('should render back to feed button', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getAllByText(/back to feed/i).length).toBeGreaterThan(0);
      });
    });

    it('should navigate back to feed when clicking back button', async () => {
      const user = userEvent.setup();
      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Test Article Title')).toBeInTheDocument();
      });

      const backButtons = screen.getAllByText(/back to feed/i);
      await user.click(backButtons[0]);

      expect(mockPush).toHaveBeenCalledWith('/feed');
    });
  });

  describe('Empty States', () => {
    it('should not render statistics section when empty', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        statistics: [],
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Test Article Title')).toBeInTheDocument();
      });

      expect(screen.queryByText('Key Statistics')).not.toBeInTheDocument();
    });

    it('should not render frameworks section when empty', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        frameworks: [],
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Test Article Title')).toBeInTheDocument();
      });

      expect(screen.queryByText('Ethical Framework Analysis')).not.toBeInTheDocument();
    });

    it('should not render related articles section when empty', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        related_articles: [],
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Test Article Title')).toBeInTheDocument();
      });

      expect(screen.queryByText('Cross-Source Coverage')).not.toBeInTheDocument();
    });

    it('should not render context section when null', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        context: null,
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Test Article Title')).toBeInTheDocument();
      });

      expect(screen.queryByText('Background & Context')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when article fails to load', async () => {
      (api.getArticleDetail as jest.Mock).mockRejectedValue(new Error('Failed to load article'));

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load article/i)).toBeInTheDocument();
      });
    });

    it('should show back to feed button on error', async () => {
      (api.getArticleDetail as jest.Mock).mockRejectedValue(new Error('Network error'));

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/back to feed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Verification Badges', () => {
    it('should display verified badge', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const verifiedBadge = screen.getByText('Verified');
        expect(verifiedBadge).toHaveClass('text-green-800');
      });
    });

    it('should display pending badge for unverified statistics', async () => {
      render(<ArticleDetailPage />);

      await waitFor(() => {
        const pendingBadge = screen.getByText('Pending');
        expect(pendingBadge).toHaveClass('text-gray-800');
      });
    });

    it('should display disputed badge for disputed statistics', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        statistics: [
          {
            statistic: 'Disputed claim',
            verification_status: 'disputed',
            confidence: null,
            source_name: null,
            source_url: null,
            source_credibility_score: null,
            fact_check_status: null,
            fact_check_source: null,
          },
        ],
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('Disputed')).toBeInTheDocument();
      });
    });

    it('should display false badge for false statistics', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        statistics: [
          {
            statistic: 'False claim',
            verification_status: 'false',
            confidence: null,
            source_name: null,
            source_url: null,
            source_credibility_score: null,
            fact_check_status: null,
            fact_check_source: null,
          },
        ],
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText('False')).toBeInTheDocument();
      });
    });
  });

  describe('Timeline Visualization', () => {
    it('should render timeline with visual dots when timeline data exists', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        context: {
          background: 'Background text',
          key_players: null,
          timeline: 'Event 1: First thing happened\nEvent 2: Second thing happened\nEvent 3: Third thing happened',
          significance: 'Significance text',
        },
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/Event 1: First thing happened/i)).toBeInTheDocument();
        expect(screen.getByText(/Event 2: Second thing happened/i)).toBeInTheDocument();
        expect(screen.getByText(/Event 3: Third thing happened/i)).toBeInTheDocument();
      });
    });

    it('should split timeline by newlines', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        context: {
          background: null,
          key_players: null,
          timeline: '2020: First event\n2021: Second event\n2022: Third event',
          significance: null,
        },
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/2020: First event/i)).toBeInTheDocument();
        expect(screen.getByText(/2021: Second event/i)).toBeInTheDocument();
        expect(screen.getByText(/2022: Third event/i)).toBeInTheDocument();
      });
    });
  });

  describe('Framework Position Interpretation', () => {
    it('should show "Balanced perspective" for position 0', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        frameworks: [
          {
            ...mockArticleDetail.frameworks[0],
            position_on_axis: 0,
          },
        ],
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/Balanced perspective/i)).toBeInTheDocument();
      });
    });

    it('should show left lean for negative positions', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        frameworks: [
          {
            ...mockArticleDetail.frameworks[0],
            position_on_axis: -2,
          },
        ],
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/Leans toward Individual Liberty/i)).toBeInTheDocument();
      });
    });

    it('should show strongly left for very negative positions', async () => {
      (api.getArticleDetail as jest.Mock).mockResolvedValue({
        ...mockArticleDetail,
        frameworks: [
          {
            ...mockArticleDetail.frameworks[0],
            position_on_axis: -5,
          },
        ],
      });

      render(<ArticleDetailPage />);

      await waitFor(() => {
        expect(screen.getByText(/Strongly aligned with Individual Liberty/i)).toBeInTheDocument();
      });
    });
  });
});
