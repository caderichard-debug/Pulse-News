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
      is_admin: false,
    });
  });

  describe('Authenticated User', () => {
    it('renders Pulse logo/brand', () => {
      render(<Navbar />);

      expect(screen.getByText('Pulse')).toBeInTheDocument();
    });

    it('renders main navigation links for authenticated users', async () => {
      render(<Navbar />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /📰.*feed/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /🔍.*insights/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /⚙️.*preferences/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /💡.*how it works/i })).toBeInTheDocument();
      });
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

    it('highlights active page', async () => {
      (usePathname as jest.Mock).mockReturnValue('/feed');

      render(<Navbar />);

      await waitFor(() => {
        const feedButton = screen.getByRole('button', { name: /📰.*feed/i });
        expect(feedButton).toHaveClass('bg-indigo-100');
      });
    });

    it('navigates to Feed when clicking Feed button', async () => {
      render(<Navbar />);

      await waitFor(() => {
        const feedButton = screen.getByRole('button', { name: /📰.*feed/i });
        fireEvent.click(feedButton);
      });

      expect(mockPush).toHaveBeenCalledWith('/feed');
    });

    it('navigates to Preferences when clicking Preferences button', async () => {
      render(<Navbar />);

      await waitFor(() => {
        const preferencesButton = screen.getByRole('button', { name: /⚙️.*preferences/i });
        fireEvent.click(preferencesButton);
      });

      expect(mockPush).toHaveBeenCalledWith('/preferences');
    });

    it('navigates to How It Works when clicking How It Works button', async () => {
      render(<Navbar />);

      await waitFor(() => {
        const howItWorksButton = screen.getByRole('button', { name: /💡.*how it works/i });
        fireEvent.click(howItWorksButton);
      });

      expect(mockPush).toHaveBeenCalledWith('/how-it-works');
    });

    it('navigates to landing page when clicking Pulse logo', async () => {
      render(<Navbar />);

      const logo = screen.getByRole('button', { name: /pulse logo/i });
      fireEvent.click(logo);

      expect(mockPush).toHaveBeenCalledWith('/');
    });

    it('renders Logout button', async () => {
      render(<Navbar />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
      });
    });

    it('clears token and navigates to landing page on logout', async () => {
      render(<Navbar />);

      await waitFor(() => {
        const logoutButton = screen.getByRole('button', { name: /logout/i });
        fireEvent.click(logoutButton);
      });

      expect(api.clearToken).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith('/');
    });

    it('shows Insights dropdown menu when Insights button is clicked', async () => {
      render(<Navbar />);

      await waitFor(() => {
        const insightsButton = screen.getByRole('button', { name: /🔍.*insights/i });
        fireEvent.click(insightsButton);
      });

      // Should show dropdown items
      await waitFor(() => {
        expect(screen.getByText('Analyze')).toBeInTheDocument();
        expect(screen.getByText('Sources')).toBeInTheDocument();
        expect(screen.getByText('Analytics')).toBeInTheDocument();
      });
    });
  });

  describe('Unauthenticated User', () => {
    beforeEach(() => {
      (api.getCurrentUser as jest.Mock).mockRejectedValue({
        status: 403,
        message: 'Not authenticated',
      });
    });

    it('shows Log In button for unauthenticated users', async () => {
      render(<Navbar />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
      });
    });

    it('shows limited navigation for unauthenticated users', async () => {
      render(<Navbar />);

      await waitFor(() => {
        // Should show public pages
        expect(screen.getByRole('button', { name: /🔍.*insights/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /💡.*how it works/i })).toBeInTheDocument();

        // Should not show authenticated pages
        expect(screen.queryByRole('button', { name: /📰.*feed/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /⚙️.*preferences/i })).not.toBeInTheDocument();
      });
    });

    it('navigates to login when clicking Log In button', async () => {
      render(<Navbar />);

      await waitFor(() => {
        const loginButton = screen.getByRole('button', { name: /log in/i });
        fireEvent.click(loginButton);
      });

      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  describe('Admin User', () => {
    beforeEach(() => {
      (api.getCurrentUser as jest.Mock).mockResolvedValue({
        name: 'Admin User',
        email: 'admin@example.com',
        is_admin: true,
      });
    });

    it('shows Admin link for admin users', async () => {
      render(<Navbar />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /⚡.*admin/i })).toBeInTheDocument();
      });
    });
  });
});
