/**
 * Test setup configuration for Vitest
 * Sets up global test environment for Finance module tests
 */

import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with Jest DOM matchers
expect.extend(matchers)

// Clean up after each test
afterEach(() => {
  cleanup()
})

// Global test mocks
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
})

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/finance',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock Next.js image
vi.mock('next/image', () => ({
  __esModule: true,
  default: ({ src, alt, ...props }: any) => {
    return React.createElement('img', { src, alt, ...props })
  },
}))

// Mock environment variables
vi.mock('next/config', () => ({
  __esModule: true,
  default: () => ({
    publicRuntimeConfig: {
      API_URL: 'http://localhost:8000',
      PAYNOW_MERCHANT_ID: 'test_merchant',
      PAYNOW_MERCHANT_KEY: 'test_key',
    },
  }),
}))

// Mock API responses
global.fetch = vi.fn()

// Helper function to mock API responses
export const mockApiResponse = (data: any, status = 200) => {
  return Promise.resolve({
    ok: status < 400,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  })
}

// Helper function to mock API errors
export const mockApiError = (message: string, status = 500) => {
  return Promise.reject({
    response: {
      data: { detail: message },
      status,
    },
  })
}

// Common test utilities
export const waitFor = (callback: () => void, timeout = 5000) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now()
    const check = () => {
      try {
        callback()
        resolve(undefined)
      } catch (error) {
        if (Date.now() - startTime > timeout) {
          reject(error)
        } else {
          setTimeout(check, 100)
        }
      }
    }
    check()
  })
}

// Mock timers
vi.useFakeTimers()

// Common test data
export const testSchoolId = 'test-school-123'
export const testUserId = 'test-user-456'
export const testAcademicYearId = 'test-ay-2025'

// Test environment setup
process.env.NODE_ENV = 'test'
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_PAYNOW_MERCHANT_ID = 'test_merchant'
process.env.NEXT_PUBLIC_PAYNOW_MERCHANT_KEY = 'test_key'

// Performance monitoring for tests
const performanceObserver = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.duration > 100) {
      console.warn(`Slow test detected: ${entry.name} took ${entry.duration}ms`)
    }
  }
})
performanceObserver.observe({ entryTypes: ['measure'] })

// Global error handler
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
})

// Clean up after all tests
afterAll(() => {
  vi.clearAllMocks()
  vi.resetAllMocks()
  vi.restoreAllMocks()
})

export default undefined