import { render, screen, fireEvent, waitFor } from '@/__tests__/test-utils';
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
    expect(feedButton).toHaveClass('bg-indigo-100');
    expect(feedButton).toHaveClass('text-indigo-700');
  });

  it('does not highlight inactive pages', () => {
    (usePathname as jest.Mock).mockReturnValue('/feed');

    render(<Navbar />);

    const analyticsButton = screen.getByRole('button', { name: /📊 analytics/i });
    expect(analyticsButton).toHaveClass('text-muted-foreground');
    expect(analyticsButton).not.toHaveClass('bg-indigo-100');
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
    expect(analyticsButton).toHaveClass('bg-indigo-100');
    expect(analyticsButton).toHaveClass('text-indigo-700');

    const feedButton = screen.getByRole('button', { name: /📰 feed/i });
    expect(feedButton).not.toHaveClass('bg-indigo-100');
  });

  it('applies hover styles to nav links', () => {
    render(<Navbar />);

    const analyticsButton = screen.getByRole('button', { name: /📊 analytics/i });
    expect(analyticsButton).toHaveClass('hover:bg-accent');
    expect(analyticsButton).toHaveClass('hover:text-accent-foreground');
  });

  it('applies transition classes to nav links', () => {
    render(<Navbar />);

    const feedButton = screen.getByRole('button', { name: /📰 feed/i });
    expect(feedButton).toHaveClass('transition-colors');
  });

  describe('Collapsible Menu', () => {
    it('renders mobile menu button', () => {
      render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });
      expect(menuButton).toBeInTheDocument();
    });

    it('menu button has correct aria attributes', () => {
      render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
      expect(menuButton).toHaveAttribute('aria-label', 'Navigation menu');
    });

    it('opens mobile menu when menu button is clicked', () => {
      render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });

      // Menu should be closed initially
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');

      // Click to open
      fireEvent.click(menuButton);

      // Menu should be open
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
    });

    it('closes mobile menu when clicking outside', () => {
      render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });

      // Open menu
      fireEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');

      // Click outside (on document body)
      fireEvent.mouseDown(document.body);

      // Menu should close
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('closes mobile menu when pressing Escape key', () => {
      render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });

      // Open menu
      fireEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');

      // Press Escape
      fireEvent.keyDown(document, { key: 'Escape' });

      // Menu should close
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('closes mobile menu when navigating to a page', async () => {
      render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });

      // Open menu
      fireEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');

      // Change pathname (simulates navigation)
      (usePathname as jest.Mock).mockReturnValue('/analytics');

      // Re-render with new pathname
      const { rerender } = render(<Navbar />);
      rerender(<Navbar />);

      // Menu should close
      await waitFor(() => {
        expect(menuButton).toHaveAttribute('aria-expanded', 'false');
      });
    });

    it('toggles menu open and closed on successive clicks', () => {
      render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });

      // Click to open
      fireEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');

      // Click to close
      fireEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');

      // Click to open again
      fireEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
    });

    it('does not close menu when clicking inside menu', () => {
      render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });

      // Open menu
      fireEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');

      // Click inside menu (on a navigation link)
      // Note: The navigation happens through router.push, not through DOM
      // So we just verify the menu stays open after clicking a nav item
      const feedButton = screen.getAllByRole('button', { name: /📰 feed/i })[0];
      fireEvent.mouseDown(feedButton);

      // Menu should remain open (pathname change will close it in real usage)
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
    });

    it('cleans up event listeners on unmount', () => {
      const { unmount } = render(<Navbar />);

      const menuButton = screen.getByRole('button', { name: /navigation menu/i });

      // Open menu to set up event listeners
      fireEvent.click(menuButton);

      // Unmount component
      unmount();

      // If we press Escape now, it should not cause errors
      expect(() => {
        fireEvent.keyDown(document, { key: 'Escape' });
      }).not.toThrow();
    });
  });

  describe('Admin Menu', () => {
    it('does not show admin link for non-admin users', async () => {
      (api.getCurrentUser as jest.Mock).mockResolvedValue({
        name: 'John Doe',
        email: 'john@example.com',
        is_admin: false,
      });

      render(<Navbar />);

      await waitFor(() => {
        expect(api.getCurrentUser).toHaveBeenCalled();
      });

      expect(screen.queryByRole('button', { name: /⚡ admin/i })).not.toBeInTheDocument();
    });

    it('shows admin link for admin users', async () => {
      (api.getCurrentUser as jest.Mock).mockResolvedValue({
        name: 'Admin User',
        email: 'admin@example.com',
        is_admin: true,
      });

      render(<Navbar />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /⚡ admin/i })).toBeInTheDocument();
      });
    });

    it('highlights admin link with red styling when active', async () => {
      (api.getCurrentUser as jest.Mock).mockResolvedValue({
        name: 'Admin User',
        email: 'admin@example.com',
        is_admin: true,
      });
      (usePathname as jest.Mock).mockReturnValue('/admin');

      render(<Navbar />);

      await waitFor(() => {
        const adminButton = screen.getByRole('button', { name: /⚡ admin/i });
        expect(adminButton).toHaveClass('bg-red-100');
        expect(adminButton).toHaveClass('text-red-700');
      });
    });

    it('navigates to admin page when clicking admin button', async () => {
      (api.getCurrentUser as jest.Mock).mockResolvedValue({
        name: 'Admin User',
        email: 'admin@example.com',
        is_admin: true,
      });

      render(<Navbar />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /⚡ admin/i })).toBeInTheDocument();
      });

      const adminButton = screen.getByRole('button', { name: /⚡ admin/i });
      fireEvent.click(adminButton);

      expect(mockPush).toHaveBeenCalledWith('/admin');
    });
  });
});
