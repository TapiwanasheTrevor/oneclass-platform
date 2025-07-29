/**
 * Integration tests for authentication middleware
 * Tests subdomain routing, tenant isolation, and school context
 */

import { describe, it, expect, beforeEach, vi, type MockedFunction } from 'vitest'
import { NextRequest, NextResponse } from 'next/server'
import { middleware } from '@/middleware'

// Mock dependencies
vi.mock('@/lib/api', () => ({
  getSchoolBySubdomain: vi.fn(),
}))

vi.mock('@/lib/auth', () => ({
  verifyToken: vi.fn(),
  extractTokenFromRequest: vi.fn(),
}))

import { getSchoolBySubdomain } from '@/lib/api'
import { verifyToken, extractTokenFromRequest } from '@/lib/auth'

const mockGetSchoolBySubdomain = getSchoolBySubdomain as MockedFunction<typeof getSchoolBySubdomain>
const mockVerifyToken = verifyToken as MockedFunction<typeof verifyToken>
const mockExtractTokenFromRequest = extractTokenFromRequest as MockedFunction<typeof extractTokenFromRequest>

describe('Authentication Middleware', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Subdomain Extraction', () => {
    it('should extract subdomain from valid hostname', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: {
          branding: {
            primary_color: '#2563eb',
            logo_url: 'https://example.com/logo.png'
          },
          features: {
            enabled_modules: ['sis', 'finance', 'academic']
          }
        },
        subscription_tier: 'professional'
      })

      mockExtractTokenFromRequest.mockReturnValue('valid-jwt-token')
      mockVerifyToken.mockResolvedValue({
        user_id: 'user-123',
        school_id: 'school-123',
        role: 'teacher',
        permissions: ['sis:read', 'academic:manage']
      })

      const response = await middleware(request)
      
      expect(mockGetSchoolBySubdomain).toHaveBeenCalledWith('peterhouse')
      expect(response).toBeInstanceOf(NextResponse)
    })

    it('should handle invalid subdomain', async () => {
      const request = new NextRequest('https://invalid-school.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockResolvedValue(null)
      
      const response = await middleware(request)
      
      expect(response?.status).toBe(302) // Redirect to 404
      expect(response?.headers.get('location')).toContain('/404')
    })

    it('should handle www subdomain correctly', async () => {
      const request = new NextRequest('https://www.oneclass.ac.zw/dashboard')
      
      // Should not call getSchoolBySubdomain for www
      const response = await middleware(request)
      
      expect(mockGetSchoolBySubdomain).not.toHaveBeenCalled()
      expect(response?.headers.get('location')).toContain('/select-school')
    })
  })

  describe('Authentication Validation', () => {
    it('should allow access with valid authentication', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'basic'
      })

      mockExtractTokenFromRequest.mockReturnValue('valid-jwt-token')
      mockVerifyToken.mockResolvedValue({
        user_id: 'user-123',
        school_id: 'school-123',
        role: 'student',
        permissions: ['sis:read']
      })

      const response = await middleware(request)
      
      // Should pass through (no redirect)
      expect(response).toBeUndefined()
    })

    it('should redirect unauthorized user', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'basic'
      })

      mockExtractTokenFromRequest.mockReturnValue(null)
      
      const response = await middleware(request)
      
      expect(response?.status).toBe(302)
      expect(response?.headers.get('location')).toContain('/login')
    })

    it('should handle wrong school access', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'basic'
      })

      mockExtractTokenFromRequest.mockReturnValue('valid-jwt-token')
      mockVerifyToken.mockResolvedValue({
        user_id: 'user-123',
        school_id: 'different-school-456', // Wrong school
        role: 'teacher',
        permissions: ['sis:manage']
      })

      const response = await middleware(request)
      
      expect(response?.status).toBe(302)
      expect(response?.headers.get('location')).toContain('/unauthorized?error=wrong_school')
    })
  })

  describe('Route Protection', () => {
    it('should allow access to public routes', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/login')
      
      // Public routes should not require authentication
      const response = await middleware(request)
      
      expect(mockVerifyToken).not.toHaveBeenCalled()
      expect(response).toBeUndefined()
    })

    it('should protect admin routes', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/admin/users')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'basic'
      })

      mockExtractTokenFromRequest.mockReturnValue('valid-jwt-token')
      mockVerifyToken.mockResolvedValue({
        user_id: 'user-123',
        school_id: 'school-123',
        role: 'student', // Not admin
        permissions: ['sis:read']
      })

      const response = await middleware(request)
      
      expect(response?.status).toBe(302)
      expect(response?.headers.get('location')).toContain('/unauthorized?error=insufficient_permissions')
    })

    it('should check feature access for modules', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/finance/invoices')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: { 
          features: { 
            enabled_modules: ['sis'] // Finance not enabled
          } 
        },
        subscription_tier: 'basic'
      })

      mockExtractTokenFromRequest.mockReturnValue('valid-jwt-token')
      mockVerifyToken.mockResolvedValue({
        user_id: 'user-123',
        school_id: 'school-123',
        role: 'admin',
        permissions: ['finance:manage']
      })

      const response = await middleware(request)
      
      expect(response?.status).toBe(302)
      expect(response?.headers.get('location')).toContain('/unauthorized?error=module_not_available')
    })
  })

  describe('School Status Validation', () => {
    it('should redirect suspended schools', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'suspended', // School suspended
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'basic'
      })

      const response = await middleware(request)
      
      expect(response?.status).toBe(302)
      expect(response?.headers.get('location')).toContain('/suspended')
    })

    it('should redirect inactive schools', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'inactive',
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'basic'
      })

      const response = await middleware(request)
      
      expect(response?.status).toBe(302)
      expect(response?.headers.get('location')).toContain('/suspended?reason=inactive')
    })
  })

  describe('Header Injection', () => {
    it('should inject school context headers', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      const schoolData = {
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'professional'
      }

      mockGetSchoolBySubdomain.mockResolvedValue(schoolData)
      mockExtractTokenFromRequest.mockReturnValue('valid-jwt-token')
      mockVerifyToken.mockResolvedValue({
        user_id: 'user-123',
        school_id: 'school-123',
        role: 'teacher',
        permissions: ['sis:read']
      })

      const response = await middleware(request)
      
      // Should pass through with headers
      expect(response).toBeUndefined()
      
      // Check if school context would be available in request headers
      expect(mockGetSchoolBySubdomain).toHaveBeenCalledWith('peterhouse')
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockRejectedValue(new Error('API Error'))
      
      const response = await middleware(request)
      
      expect(response?.status).toBe(302)
      expect(response?.headers.get('location')).toContain('/error')
    })

    it('should handle malformed tokens', async () => {
      const request = new NextRequest('https://peterhouse.oneclass.ac.zw/dashboard')
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'basic'
      })

      mockExtractTokenFromRequest.mockReturnValue('invalid-token')
      mockVerifyToken.mockRejectedValue(new Error('Invalid token'))
      
      const response = await middleware(request)
      
      expect(response?.status).toBe(302)
      expect(response?.headers.get('location')).toContain('/login')
    })
  })

  describe('Performance Considerations', () => {
    it('should handle concurrent requests efficiently', async () => {
      const requests = Array.from({ length: 10 }, (_, i) => 
        new NextRequest(`https://peterhouse.oneclass.ac.zw/dashboard?req=${i}`)
      )
      
      mockGetSchoolBySubdomain.mockResolvedValue({
        id: 'school-123',
        name: 'Peterhouse School',
        subdomain: 'peterhouse',
        status: 'active',
        configuration: { features: { enabled_modules: ['sis'] } },
        subscription_tier: 'basic'
      })

      mockExtractTokenFromRequest.mockReturnValue('valid-jwt-token')
      mockVerifyToken.mockResolvedValue({
        user_id: 'user-123',
        school_id: 'school-123',
        role: 'teacher',
        permissions: ['sis:read']
      })

      const responses = await Promise.all(
        requests.map(request => middleware(request))
      )
      
      // All requests should complete successfully
      responses.forEach(response => {
        expect(response).toBeUndefined() // Pass through
      })
      
      // Should cache school data (called once per subdomain)
      expect(mockGetSchoolBySubdomain).toHaveBeenCalledTimes(1)
    })
  })
})