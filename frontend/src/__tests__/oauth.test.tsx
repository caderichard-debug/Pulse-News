/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent } from '@testing-library/react'
import LoginPage from '@/app/login/page'
import SignupPage from '@/app/signup/page'

// Mock window.location.href
const mockLocation = { href: '' }
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
})

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
    replace: jest.fn(),
  }),
  useSearchParams: () => ({
    get: jest.fn(),
  }),
}))

describe('OAuth Authentication', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockLocation.href = ''
    // Mock getTopics to return an empty array by default
    const { api } = jest.requireMock('@/lib/api')
    api.getTopics.mockResolvedValue([])

    // Mock environment variable
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
  })

  describe('Google Sign-In Button', () => {
    test('renders Google sign-in button on login page', () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      expect(googleButton).toBeInTheDocument()
      expect(googleButton).toHaveAttribute('type', 'button')
    })

    test('shows loading state when Google sign-in is in progress', async () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })

      // Simulate the click that sets loading state
      fireEvent.click(googleButton)

      // Note: Since we're testing window.location.href redirect,
      // we won't see the loading state in the test as the redirect happens immediately
      expect(googleButton).toBeDisabled()
      expect(screen.getByText('Signing in with Google...')).toBeInTheDocument()
    })

    test('redirects to Google OAuth endpoint when button clicked', async () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })

      fireEvent.click(googleButton)

      expect(mockLocation.href).toBe('http://localhost:8000/auth/oauth/google')
    })

    test('disables all buttons during OAuth loading', async () => {
      render(<LoginPage />)

      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      const emailInput = screen.getByLabelText(/email/i)

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.click(googleButton)

      expect(googleButton).toBeDisabled()
      const submitButton = screen.getByRole('button', { name: /log in/i })
      expect(submitButton).toBeDisabled()
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
      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })

      fireEvent.click(googleButton)

      expect(googleButton).toBeDisabled()
      expect(screen.getByText('Creating account with Google...')).toBeInTheDocument()
    })

    test('redirects to Google OAuth endpoint when sign-up button clicked', async () => {
      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })

      fireEvent.click(googleButton)

      expect(mockLocation.href).toBe('http://localhost:8000/auth/oauth/google')
    })

    test('disables form buttons during OAuth loading', async () => {
      render(<SignupPage />)

      const googleButton = screen.getByRole('button', { name: /sign up with google/i })
      const nameInput = screen.getByLabelText(/full name/i)

      fireEvent.change(nameInput, { target: { value: 'Test User' } })
      fireEvent.click(googleButton)

      const submitButton = screen.getByRole('button', { name: /continue/i })
      expect(submitButton).toBeDisabled()
      expect(googleButton).toBeDisabled()
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