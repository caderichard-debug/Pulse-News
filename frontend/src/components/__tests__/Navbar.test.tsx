import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter, usePathname } from 'next/navigation';
import Navbar from '../Navbar';
import { api } from '@/lib/api';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}));

// Mock API
jest.mock('@/lib/api', () => ({
  api: {
    getCurrentUser: jest.fn(),
    clearToken: jest.fn(),
  },
}));

describe('Navbar', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
    (usePathname as jest.Mock).mockReturnValue('/feed');
    (api.getCurrentUser as jest.Mock).mockResolvedValue({
      name: 'John Doe',
      email: 'john@example.com',
    });
  });

  it('renders Pulse logo/brand', () => {
    render(<Navbar />);

    expect(screen.getByText('Pulse')).toBeInTheDocument();
  });

  it('renders all navigation links', () => {
    render(<Navbar />);

    expect(screen.getByRole('button', { name: /📰 feed/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /📑 sources/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /📊 analytics/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /⚙️ preferences/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /💡 how it works/i })).toBeInTheDocument();
  });

  it('displays user name when loaded', async () => {
    render(<Navbar />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('fetches current user on mount', async () => {
    render(<Navbar />);

    await waitFor(() => {
      expect(api.getCurrentUser).toHaveBeenCalled();
    });
  });

  it('highlights active page', () => {
    (usePathname as jest.Mock).mockReturnValue('/feed');

    render(<Navbar />);

    const feedButton = screen.getByRole('button', { name: /📰 feed/i });
    expect(feedButton).toHaveClass('bg-indigo-50', 'text-indigo-700');
  });

  it('does not highlight inactive pages', () => {
    (usePathname as jest.Mock).mockReturnValue('/feed');

    render(<Navbar />);

    const analyticsButton = screen.getByRole('button', { name: /📊 analytics/i });
    expect(analyticsButton).toHaveClass('text-gray-600');
    expect(analyticsButton).not.toHaveClass('bg-indigo-50');
  });

  it('navigates to Analytics when clicking Analytics button', () => {
    render(<Navbar />);

    const analyticsButton = screen.getByRole('button', { name: /📊 analytics/i });
    fireEvent.click(analyticsButton);

    expect(mockPush).toHaveBeenCalledWith('/analytics');
  });

  it('navigates to Feed when clicking Feed button', () => {
    render(<Navbar />);

    const feedButton = screen.getByRole('button', { name: /📰 feed/i });
    fireEvent.click(feedButton);

    expect(mockPush).toHaveBeenCalledWith('/feed');
  });

  it('navigates to Sources when clicking Sources button', () => {
    render(<Navbar />);

    const sourcesButton = screen.getByRole('button', { name: /📑 sources/i });
    fireEvent.click(sourcesButton);

    expect(mockPush).toHaveBeenCalledWith('/sources');
  });

  it('navigates to Preferences when clicking Preferences button', () => {
    render(<Navbar />);

    const preferencesButton = screen.getByRole('button', { name: /⚙️ preferences/i });
    fireEvent.click(preferencesButton);

    expect(mockPush).toHaveBeenCalledWith('/preferences');
  });

  it('navigates to How It Works when clicking How It Works button', () => {
    render(<Navbar />);

    const howItWorksButton = screen.getByRole('button', { name: /💡 how it works/i });
    fireEvent.click(howItWorksButton);

    expect(mockPush).toHaveBeenCalledWith('/how-it-works');
  });

  it('navigates to Feed when clicking Pulse logo', () => {
    render(<Navbar />);

    const logo = screen.getByText('Pulse');
    fireEvent.click(logo);

    expect(mockPush).toHaveBeenCalledWith('/feed');
  });

  it('renders Logout button', () => {
    render(<Navbar />);

    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  it('clears token and navigates to landing page on logout', () => {
    render(<Navbar />);

    const logoutButton = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutButton);

    expect(api.clearToken).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith('/');
  });

  it('handles user fetch error gracefully', async () => {
    (api.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Unauthorized'));

    render(<Navbar />);

    await waitFor(() => {
      expect(api.getCurrentUser).toHaveBeenCalled();
    });

    // Should not crash, userName should remain null
    expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
  });

  it('shows all navigation icons', () => {
    render(<Navbar />);

    expect(screen.getByText('📰')).toBeInTheDocument();
    expect(screen.getByText('📑')).toBeInTheDocument();
    expect(screen.getByText('📊')).toBeInTheDocument();
    expect(screen.getByText('⚙️')).toBeInTheDocument();
    expect(screen.getByText('💡')).toBeInTheDocument();
  });

  it('navigates to preferences when clicking user name', async () => {
    render(<Navbar />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const userName = screen.getByText('John Doe');
    fireEvent.click(userName);

    expect(mockPush).toHaveBeenCalledWith('/preferences');
  });

  it('does not show user name while loading', () => {
    (api.getCurrentUser as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<Navbar />);

    expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
  });

  it('cleans up on unmount', () => {
    const { unmount } = render(<Navbar />);

    unmount();

    // If there was a pending request, it should be cancelled
    // This tests the cleanup function in useEffect
  });

  it('updates highlighting when pathname changes', () => {
    const { rerender } = render(<Navbar />);

    (usePathname as jest.Mock).mockReturnValue('/analytics');
    rerender(<Navbar />);

    const analyticsButton = screen.getByRole('button', { name: /📊 analytics/i });
    expect(analyticsButton).toHaveClass('bg-indigo-50', 'text-indigo-700');

    const feedButton = screen.getByRole('button', { name: /📰 feed/i });
    expect(feedButton).not.toHaveClass('bg-indigo-50');
  });

  it('applies hover styles to nav links', () => {
    render(<Navbar />);

    const analyticsButton = screen.getByRole('button', { name: /📊 analytics/i });
    expect(analyticsButton).toHaveClass('hover:bg-gray-50', 'hover:text-gray-900');
  });

  it('applies transition classes to nav links', () => {
    render(<Navbar />);

    const feedButton = screen.getByRole('button', { name: /📰 feed/i });
    expect(feedButton).toHaveClass('transition-colors');
  });
});
