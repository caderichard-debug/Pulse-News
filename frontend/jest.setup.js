import '@testing-library/jest-dom'

// Suppress React act() warnings for async state updates in tests
// These warnings occur when React state updates happen outside of the testing framework's control
// In many cases, these are harmless and occur during component initialization
const originalError = console.error
beforeAll(() => {
  console.error = (...args) => {
    const message = typeof args[0] === 'string' ? args[0] : ''

    // Suppress React act() warnings
    if (
      message.includes('update to') &&
      message.includes('inside a test was not wrapped in act')
    ) {
      return
    }

    // Suppress intentional API error messages from tests
    if (
      message.includes('Error fetching viewpoints:') ||
      message.includes('Failed to load challenge data:') ||
      message.includes('Failed to load analytics data:') ||
      message.includes('Cannot complete this request right now. OpenAI API is unavailable.')
    ) {
      return
    }

    originalError.call(console, ...args)
  }
})

// Suppress console.warn messages for intentional test warnings
const originalWarn = console.warn
beforeAll(() => {
  console.warn = (...args) => {
    const message = typeof args[0] === 'string' ? args[0] : ''

    // Suppress intentional test warnings
    if (
      message.includes('Skipping test - no auth token available') ||
      message.includes('REGRESSION DETECTED: All viewpoints show the same framework')
    ) {
      return
    }

    originalWarn.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
  console.warn = originalWarn
})

// Mock global fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: async () => ({}),
    text: async () => '',
    status: 200,
    statusText: 'OK',
  })
)

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    }
  },
  useSearchParams() {
    return {
      get: jest.fn(),
    }
  },
  useParams() {
    return {}
  },
  usePathname() {
    return ''
  },
}))

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})
