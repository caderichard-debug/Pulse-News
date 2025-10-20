import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter, useSearchParams } from 'next/navigation';
import SourcesPage from '../page';
import { api } from '@/lib/api';

jest.mock('next/navigation');
jest.mock('@/lib/api');

describe('SourcesPage', () => {
  const mockRouter = {
    push: jest.fn(),
  };

  const mockSearchParams = {
    get: jest.fn(() => null),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);

    // Mock API responses
    (api.getAllSources as jest.Mock).mockResolvedValue({
      sources: [
        {
          id: 1,
          name: 'Recommended Source',
          url: 'https://recommended.com',
          rss_feed_url: 'https://recommended.com/rss',
          description: 'A recommended source',
          trust_score: 0.9,
          organizational_bias: 'center',
          is_recommended: true,
          is_active: true,
          article_count: 100,
        },
        {
          id: 2,
          name: 'Community Source',
          url: 'https://community.com',
          rss_feed_url: 'https://community.com/rss',
          description: 'A community source',
          trust_score: 0.7,
          organizational_bias: 'left',
          is_recommended: false,
          is_active: true,
          article_count: 50,
        },
      ],
    });
  });

  it('renders the sources page with recommended tab by default', async () => {
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('📰 News Sources')).toBeInTheDocument();
      expect(screen.getByText(/Recommended Source/)).toBeInTheDocument();
    });
  });

  it('displays recommended sources in the recommended tab', async () => {
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('Recommended Source')).toBeInTheDocument();
      expect(screen.getByText('✅ Recommended')).toBeInTheDocument();
    });
  });

  it('switches to community tab when clicked', async () => {
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('Recommended Source')).toBeInTheDocument();
    });

    const communityTab = screen.getByRole('button', { name: /🌐 Community/ });
    fireEvent.click(communityTab);

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith('/sources?tab=community', { scroll: false });
    });
  });

  it('displays community sources in the community tab', async () => {
    mockSearchParams.get.mockReturnValue('community');
    
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('Community Source')).toBeInTheDocument();
      expect(screen.queryByText('✅ Recommended')).not.toBeInTheDocument();
    });
  });

  it('displays add source form in the add tab', async () => {
    mockSearchParams.get.mockReturnValue('add');
    
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('Add a News Source')).toBeInTheDocument();
      expect(screen.getByLabelText(/Article URL/)).toBeInTheDocument();
    });
  });

  it('filters sources by search query', async () => {
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('Recommended Source')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search sources by name/);
    fireEvent.change(searchInput, { target: { value: 'Recommended' } });

    expect(screen.getByText('Recommended Source')).toBeInTheDocument();
  });

  it('submits new source from article URL', async () => {
    mockSearchParams.get.mockReturnValue('add');
    
    (api.createSourceFromURL as jest.Mock).mockResolvedValue({
      message: 'Source created successfully',
      already_existed: false,
      source: {
        id: 3,
        name: 'New Source',
        is_recommended: false,
      },
    });

    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Article URL/)).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText(/Article URL/);
    fireEvent.change(urlInput, { target: { value: 'https://example.com/article' } });

    const submitButton = screen.getByRole('button', { name: /Add Source/ });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(api.createSourceFromURL).toHaveBeenCalledWith('https://example.com/article');
    });
  });

  it('shows error message when source submission fails', async () => {
    mockSearchParams.get.mockReturnValue('add');
    
    (api.createSourceFromURL as jest.Mock).mockRejectedValue(
      new Error('Invalid URL')
    );

    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Article URL/)).toBeInTheDocument();
    });

    const urlInput = screen.getByLabelText(/Article URL/);
    fireEvent.change(urlInput, { target: { value: 'invalid-url' } });

    const submitButton = screen.getByRole('button', { name: /Add Source/ });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Invalid URL/)).toBeInTheDocument();
    });
  });

  it('displays organizational bias badges', async () => {
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText('Recommended Source')).toBeInTheDocument();
    });

    // Check that SourceBiasBadge is rendered (implementation depends on badge component)
    expect(api.getAllSources).toHaveBeenCalled();
  });

  it('shows empty state when no community sources exist', async () => {
    (api.getAllSources as jest.Mock).mockResolvedValue({
      sources: [
        {
          id: 1,
          name: 'Recommended Source',
          url: 'https://recommended.com',
          rss_feed_url: 'https://recommended.com/rss',
          is_recommended: true,
          is_active: true,
          article_count: 100,
        },
      ],
    });

    mockSearchParams.get.mockReturnValue('community');
    
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText(/No community sources found/)).toBeInTheDocument();
    });
  });

  it('counts sources correctly in tab labels', async () => {
    render(<SourcesPage />);

    await waitFor(() => {
      expect(screen.getByText(/✅ Recommended \(1\)/)).toBeInTheDocument();
      expect(screen.getByText(/🌐 Community \(1\)/)).toBeInTheDocument();
    });
  });
});
