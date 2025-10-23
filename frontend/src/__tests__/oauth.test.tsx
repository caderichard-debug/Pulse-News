/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import LoginPage from '@/app/login/page'
import SignupPage from '@/app/signup/page'
import { signIn } from 'next-auth/react'

// Mock NextAuth.js
jest.mock('next-auth/react', () => ({
  signIn: jest.fn(),
  useSession: jest.fn(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => children,
}))

// Mock API
jest.mock('@/lib/api', () => ({
  api: {
    login: jest.fn(),
    register: jest.fn(),
    setToken: jest.fn(),
    getTopics: jest.fn(),
  },
}))

// Mock BrandCard component
jest.mock('@/components/BrandCard', () => {
  return function BrandCard({ size }: { size: string }) {
    return <div data-testid="brand-card" data-size={size}>Brand Card</div>
  }
})

// Mock router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

describe('OAuth Authentication', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(signIn as jest.Mock).mockResolvedValue({
      ok: true,
      error: null,
    })
    // Mock getTopics to return an empty array by default
    const { api } = jest.requireMock('@/lib/api')
    api.getTopics.mockResolvedValue([])
  })

  describe('Google Sign-In Button', () => {
    test('renders Google sign-in button on login page', () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      expect(googleButton).toBeInTheDocument()
      expect(googleButton).toHaveAttribute('type', 'button')
    })

    test('shows loading state when Google sign-in is in progress', async () => {
      ;(signIn as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })

      fireEvent.click(googleButton)

      await waitFor(() => {
        expect(googleButton).toBeDisabled()
        expect(screen.getByText('Signing in with Google...')).toBeInTheDocument()
      })
    })

    test('calls signIn with Google provider when button clicked', async () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })

      fireEvent.click(googleButton)

      await waitFor(() => {
        expect(signIn).toHaveBeenCalledWith('google', {
          redirect: false,
          callbackUrl: '/feed',
        })
      })
    })

    test('displays error message when Google sign-in fails', async () => {
      ;(signIn as jest.Mock).mockResolvedValue({
        ok: false,
        error: 'OAuthSignin',
      })

      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })

      fireEvent.click(googleButton)

      await waitFor(() => {
        expect(screen.getByText(/Google sign-in failed: OAuthSignin/)).toBeInTheDocument()
      })
    })

    test('disables all buttons during OAuth loading', async () => {
      ;(signIn as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      const emailInput = screen.getByLabelText(/email/i)

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.click(googleButton)

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /log in/i })
        expect(submitButton).toBeDisabled()
        expect(googleButton).toBeDisabled()
      })
    })
  })

  describe('Google Sign-Up Button', () => {
    test('renders Google sign-up button on signup page', () => {
      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })
      expect(googleButton).toBeInTheDocument()
      expect(googleButton).toHaveAttribute('type', 'button')
    })

    test('shows loading state when Google sign-up is in progress', async () => {
      ;(signIn as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })

      fireEvent.click(googleButton)

      await waitFor(() => {
        expect(googleButton).toBeDisabled()
        expect(screen.getByText('Creating account with Google...')).toBeInTheDocument()
      })
    })

    test('calls signIn with Google provider when sign-up button clicked', async () => {
      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })

      fireEvent.click(googleButton)

      await waitFor(() => {
        expect(signIn).toHaveBeenCalledWith('google', {
          redirect: false,
          callbackUrl: '/preferences',
        })
      })
    })

    test('displays error message when Google sign-up fails', async () => {
      ;(signIn as jest.Mock).mockResolvedValue({
        ok: false,
        error: 'OAuthSignin',
      })

      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })

      fireEvent.click(googleButton)

      await waitFor(() => {
        expect(screen.getByText(/Google sign-up failed: OAuthSignin/)).toBeInTheDocument()
      })
    })

    test('disables form buttons during OAuth loading', async () => {
      ;(signIn as jest.Mock).mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })
      const nameInput = screen.getByLabelText(/full name/i)

      fireEvent.change(nameInput, { target: { value: 'Test User' } })
      fireEvent.click(googleButton)

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /continue/i })
        expect(submitButton).toBeDisabled()
        expect(googleButton).toBeDisabled()
      })
    })
  })

  describe('OAuth Button Accessibility', () => {
    test('Google sign-in button has proper ARIA attributes', () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      expect(googleButton).toHaveAttribute('type', 'button')
    })

    test('Google sign-up button has proper ARIA attributes', () => {
      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })
      expect(googleButton).toHaveAttribute('type', 'button')
    })

    test('buttons are keyboard accessible', () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      expect(googleButton).not.toHaveAttribute('disabled')

      // Simulate keyboard interaction
      googleButton.focus()
      expect(googleButton).toHaveFocus()
    })
  })

  describe('OAuth Button Visual Elements', () => {
    test('Google button contains Google logo SVG', () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      const svg = googleButton.querySelector('svg')

      expect(svg).toBeInTheDocument()
      expect(svg).toHaveAttribute('viewBox', '0 0 24 24')
    })

    test('Google button has correct styling classes', () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      expect(googleButton).toHaveClass('border', 'border-gray-300', 'shadow-sm')
    })

    test('OAuth buttons are positioned before email forms', () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      const divider = screen.getByText(/or continue with email/i)
      const emailInput = screen.getByLabelText(/email/i)

      expect(googleButton.compareDocumentPosition(divider) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
      expect(divider.compareDocumentPosition(emailInput) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    })
  })
})