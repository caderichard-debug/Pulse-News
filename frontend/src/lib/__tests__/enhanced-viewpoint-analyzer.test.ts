/**
 * Test suite for Enhanced Cross-Framework Viewpoint Analyzer
 *
 * This test verifies that the frontend can successfully fetch and display
 * opposing viewpoints using the new cross-framework analysis.
 */

import { describe, it, expect, beforeEach, afterEach } from '@jest/globals'
import { api } from '../api'

// Mock fetch for isolated testing
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('Enhanced Cross-Framework Viewpoint Analyzer', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('Cross-Framework Analysis API', () => {
    it('should fetch opposing viewpoints with framework diversity', async () => {
      // Mock the enhanced analyzer response with cross-framework oppositions
      const mockResponse = {
        status: 'success',
        opposing_viewpoints: [
          {
            opposing_article: {
              id: 981,
              title: 'Biden administration announces new climate policy',
              source: { name: 'Reuters' },
              published_at: '2025-10-20T10:00:00Z',
              summary: 'A different perspective on the climate debate'
            },
            relationship_type: 'framework_opposition',
            opposition_strength: 0.92,
            framework_name: 'National Interest vs. Global Cooperation',
            ai_explanation: 'This article takes a strongly negative position on National Interest vs. Global Cooperation (-5), directly opposing the primary article\'s positive stance (6). The frameworks clash on core values and priorities.',
            primary_position: 6,
            opposing_position: -5
          },
          {
            opposing_article: {
              id: 991,
              title: 'Individual rights advocates challenge new surveillance bill',
              source: { name: 'ACLU' },
              published_at: '2025-10-20T14:30:00Z',
              summary: 'Focus on civil liberties in the digital age'
            },
            relationship_type: 'framework_opposition',
            opposition_strength: 0.84,
            framework_name: 'Individual Liberty vs. Collective Welfare',
            ai_explanation: 'This article presents a \'Individual Liberty vs. Collective Welfare\' perspective (position 6), which opposes the primary article\'s \'National Interest vs. Global Cooperation\' framework (position -3). The 9-point gap represents fundamentally different approaches to this issue.',
            primary_position: -3,
            opposing_position: 6
          },
          {
            opposing_article: {
              id: 4,
              title: 'Federal court blocks key provision of immigration law',
              source: { name: 'New York Times' },
              published_at: '2025-10-20T09:15:00Z',
              summary: 'Judicial review of executive authority'
            },
            relationship_type: 'framework_opposition',
            opposition_strength: 0.84,
            framework_name: 'Individual Liberty vs. Collective Welfare',
            ai_explanation: 'This article presents a \'Individual Liberty vs. Collective Welfare\' perspective (position 6), which opposes the primary article\'s \'National Interest vs. Global Cooperation\' framework (position -3). The 9-point gap represents fundamentally different approaches to this issue.',
            primary_position: -3,
            opposing_position: 6
          }
        ],
        meta: {
          primary_article_frameworks: [
            {
              framework_name: 'National Interest vs. Global Cooperation',
              position: 6,
              relevance_score: 0.85
            },
            {
              framework_name: 'Individual Liberty vs. Collective Welfare',
              position: -3,
              relevance_score: 0.78
            }
          ],
          total_results: 3,
          analysis_method: 'cross_framework_enhanced'
        }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      // Call the API
      const result = await api.getOpposingViewpoints(1014, { max_results: 5 })

      // Verify the request was made correctly
      expect(mockFetch).toHaveBeenCalledWith(
        '/articles/1014/opposing-viewpoints?max_results=5',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      )

      // Verify the response structure
      expect(result).toBeDefined()
      expect(result.status).toBe('success')
      expect(result.opposing_viewpoints).toHaveLength(3)

      // Verify cross-framework diversity
      const frameworks = result.opposing_viewpoints.map(vp => vp.framework_name)
      const uniqueFrameworks = [...new Set(frameworks)]
      expect(uniqueFrameworks.length).toBeGreaterThan(1, 'Should show multiple frameworks, not just one')
      expect(uniqueFrameworks).toContain('National Interest vs. Global Cooperation')
      expect(uniqueFrameworks).toContain('Individual Liberty vs. Collective Welfare')

      // Verify AI explanations are present and meaningful
      result.opposing_viewpoints.forEach(vp => {
        expect(vp.ai_explanation).toBeDefined()
        expect(vp.ai_explanation.length).toBeGreaterThan(50)
        expect(vp.ai_explanation).not.toContain('Cached relationship')
        expect(vp.framework_name).toBeDefined()
        expect(vp.primary_position).toBeDefined()
        expect(vp.opposing_position).toBeDefined()
      })

      // Verify strength scores are reasonable
      result.opposing_viewpoints.forEach(vp => {
        expect(vp.opposition_strength).toBeGreaterThanOrEqual(0)
        expect(vp.opposition_strength).toBeLessThanOrEqual(1)
      })

      console.log('✅ Cross-framework analysis test passed')
      console.log(`   Found ${uniqueFrameworks.length} unique frameworks: ${uniqueFrameworks.join(', ')}`)
    })

    it('should trigger on-demand analysis with enhanced analyzer', async () => {
      // Mock the analysis trigger response
      const mockTriggerResponse = {
        status: 'success',
        article_id: 1014,
        message: 'Viewpoint analysis job started',
        job_id: 'job_12345'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTriggerResponse
      })

      // Trigger the analysis
      const result = await api.triggerViewpointAnalysis(1014)

      // Verify the request
      expect(mockFetch).toHaveBeenCalledWith(
        '/articles/1014/analyze-viewpoints',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      )

      // Verify response
      expect(result.status).toBe('success')
      expect(result.article_id).toBe(1014)
      expect(result.job_id).toBeDefined()

      console.log('✅ On-demand analysis trigger test passed')
    })

    it('should handle cases with no opposing viewpoints found', async () => {
      // Mock empty response for article with no oppositions
      const mockEmptyResponse = {
        status: 'success',
        opposing_viewpoints: [],
        meta: {
          total_results: 0,
          analysis_method: 'cross_framework_enhanced',
          message: 'No strong opposing viewpoints found'
        }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockEmptyResponse
      })

      const result = await api.getOpposingViewpoints(105) // Venezuela article

      expect(result.opposing_viewpoints).toHaveLength(0)
      expect(result.meta.total_results).toBe(0)
      expect(result.meta.message).toContain('No strong opposing viewpoints found')

      console.log('✅ Empty results test passed')
    })
  })

  describe('Framework Diversity Validation', () => {
    it('should detect if all viewpoints show the same framework (regression test)', async () => {
      // Mock a BAD response where all viewpoints have the same framework
      const mockBadResponse = {
        status: 'success',
        opposing_viewpoints: [
          {
            opposing_article: { id: 981, title: 'Article 1' },
            framework_name: 'National Interest vs. Global Cooperation',
            opposition_strength: 0.9
          },
          {
            opposing_article: { id: 105, title: 'Article 2' },
            framework_name: 'National Interest vs. Global Cooperation', // Same framework!
            opposition_strength: 0.8
          },
          {
            opposing_article: { id: 978, title: 'Article 3' },
            framework_name: 'National Interest vs. Global Cooperation', // Same framework!
            opposition_strength: 0.7
          }
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBadResponse
      })

      const result = await api.getOpposingViewpoints(1014)

      // Test validation function
      const frameworks = result.opposing_viewpoints.map(vp => vp.framework_name)
      const uniqueFrameworks = [...new Set(frameworks)]

      // This test should detect the problem
      if (uniqueFrameworks.length === 1) {
        console.warn('⚠️  REGRESSION DETECTED: All viewpoints show the same framework')
        console.warn(`   Framework: ${uniqueFrameworks[0]}`)
        console.warn(`   This indicates the enhanced analyzer is not working properly`)

        // Fail the test to highlight the regression
        expect(uniqueFrameworks.length).toBeGreaterThan(1)
      } else {
        console.log('✅ Framework diversity validation passed')
      }
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal server error' })
      })

      await expect(api.getOpposingViewpoints(1014)).rejects.toThrow()

      console.log('✅ Error handling test passed')
    })
  })
})

// Helper function to validate cross-framework analysis
export function validateCrossFrameworkAnalysis(viewpoints: any[]): {
  isValid: boolean
  issues: string[]
  frameworks: string[]
} {
  const issues: string[] = []
  const frameworks = viewpoints.map(vp => vp.framework_name).filter(Boolean)
  const uniqueFrameworks = [...new Set(frameworks)]

  // Check for framework diversity
  if (uniqueFrameworks.length === 1 && viewpoints.length > 1) {
    issues.push(`All ${viewpoints.length} viewpoints show the same framework: ${uniqueFrameworks[0]}`)
  }

  // Check for AI explanations
  const missingExplanations = viewpoints.filter(vp => !vp.ai_explanation || vp.ai_explanation.includes('Cached relationship'))
  if (missingExplanations.length > 0) {
    issues.push(`${missingExplanations.length} viewpoints have missing or cached explanations`)
  }

  // Check for position data
  const missingPositions = viewpoints.filter(vp => !vp.primary_position || !vp.opposing_position)
  if (missingPositions.length > 0) {
    issues.push(`${missingPositions.length} viewpoints have missing position data`)
  }

  return {
    isValid: issues.length === 0,
    issues,
    frameworks: uniqueFrameworks
  }
}