import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import UnverifiedEmailAlert from '../UnverifiedEmailAlert';
import { api } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  api: {
    getCurrentUser: jest.fn(),
  },
}));

describe('UnverifiedEmailAlert', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should not render when user email is verified', async () => {
    // Mock API to return verified user
    (api.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      email_verified: true,
    });

    const { container } = render(<UnverifiedEmailAlert />);

    // Wait for the component to finish loading
    await waitFor(() => {
      expect(api.getCurrentUser).toHaveBeenCalled();
    });

    // Alert should not be rendered
    expect(container.firstChild).toBeNull();
  });

  it('should render alert when user email is not verified', async () => {
    // Mock API to return unverified user
    (api.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      email_verified: false,
    });

    render(<UnverifiedEmailAlert />);

    // Wait for the alert to appear
    await waitFor(() => {
      expect(screen.getByText(/Email not verified/i)).toBeInTheDocument();
    });

    // Check that the warning message is displayed
    expect(screen.getByText(/You won't receive newsletters until you verify your email address/i)).toBeInTheDocument();
    expect(screen.getByText(/Please check your inbox for a verification link/i)).toBeInTheDocument();
  });

  it('should not render when API call fails', async () => {
    // Mock API to throw an error
    (api.getCurrentUser as jest.Mock).mockRejectedValue(new Error('API Error'));

    const { container } = render(<UnverifiedEmailAlert />);

    // Wait for the component to finish loading
    await waitFor(() => {
      expect(api.getCurrentUser).toHaveBeenCalled();
    });

    // Alert should not be rendered on error
    expect(container.firstChild).toBeNull();
  });

  it('should not render when user is null', async () => {
    // Mock API to return null (no user logged in)
    (api.getCurrentUser as jest.Mock).mockResolvedValue(null);

    const { container } = render(<UnverifiedEmailAlert />);

    // Wait for the component to finish loading
    await waitFor(() => {
      expect(api.getCurrentUser).toHaveBeenCalled();
    });

    // Alert should not be rendered
    expect(container.firstChild).toBeNull();
  });

  it('should display the correct styling for a warning alert', async () => {
    // Mock API to return unverified user
    (api.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      email_verified: false,
    });

    const { container } = render(<UnverifiedEmailAlert />);

    // Wait for the alert to appear
    await waitFor(() => {
      expect(screen.getByText(/Email not verified/i)).toBeInTheDocument();
    });

    // Check that the alert has the correct styling classes
    const alertDiv = container.querySelector('.bg-yellow-50');
    expect(alertDiv).toBeInTheDocument();
    expect(alertDiv).toHaveClass('border-l-4', 'border-yellow-400');
  });

  it('should clean up on unmount', async () => {
    // Mock API to return unverified user
    (api.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      email_verified: false,
    });

    const { unmount } = render(<UnverifiedEmailAlert />);

    // Wait for the alert to appear
    await waitFor(() => {
      expect(screen.getByText(/Email not verified/i)).toBeInTheDocument();
    });

    // Unmount the component
    unmount();

    // Component should be cleaned up (no assertion needed, just checking no errors occur)
  });
});
