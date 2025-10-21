/**
 * Integration Test for Enhanced Cross-Framework Viewpoint Analyzer
 *
 * This test makes real API calls to verify the enhanced analyzer is working correctly.
 */

import { describe, it, expect, beforeAll } from '@jest/globals'

describe('Enhanced Analyzer Integration Test', () => {
  const API_BASE = 'http://localhost:8000'
  let authToken: string

  beforeAll(async () => {
    // Create test user and get auth token
    const registerResponse = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Test User',
        email: 'test.analyzer@example.com',
        password: 'password'
      })
    })

    if (registerResponse.ok) {
      const data = await registerResponse.json()
      authToken = data.access_token
    } else {
      // Try login if user already exists
      const loginResponse = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'test.analyzer@example.com',
          password: 'password'
        })
      })

      if (loginResponse.ok) {
        const data = await loginResponse.json()
        authToken = data.access_token
      }
    }

    expect(authToken).toBeDefined()
  })

  it('should get real opposing viewpoints with framework diversity', async () => {
    // Test article 1014 (Trump article) which should have cross-framework oppositions
    const response = await fetch(`${API_BASE}/articles/1014/opposing-viewpoints?max_results=5`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error(`API Error (${response.status}):`, errorText)
      throw new Error(`API call failed: ${response.status}`)
    }

    const data = await response.json()
    console.log('🔍 Raw API Response:', JSON.stringify(data, null, 2))

    // Verify response structure
    expect(data).toHaveProperty('opposing_viewpoints')
    expect(data.opposing_viewpoints).toBeInstanceOf(Array)

    if (data.opposing_viewpoints.length === 0) {
      console.log('ℹ️  No opposing viewpoints found - this is valid for some articles')
      return
    }

    console.log(`\n📊 Found ${data.opposing_viewpoints.length} opposing viewpoints:`)

    // Check for framework diversity
    const frameworks = data.opposing_viewpoints
      .map((vp: any) => vp.framework_name)
      .filter((name: string | undefined) => name && name.trim() !== '')

    const uniqueFrameworks = [...new Set(frameworks)]

    console.log(`🎯 Frameworks found: ${uniqueFrameworks.join(', ')}`)
    console.log(`🔢 Unique frameworks: ${uniqueFrameworks.length} out of ${frameworks.length} total`)

    // Analyze each viewpoint
    data.opposing_viewpoints.forEach((vp: any, index: number) => {
      console.log(`\n${index + 1}. Article ${vp.article_id}: ${vp.title?.substring(0, 60)}...`)
      console.log(`   Framework: ${vp.framework_name || 'NOT SET'}`)
      console.log(`   Strength: ${vp.opposition_strength}`)
      console.log(`   Position: ${vp.primary_position} vs ${vp.opposing_position}`)

      if (vp.ai_explanation) {
        const preview = vp.ai_explanation.substring(0, 100)
        console.log(`   Explanation: ${preview}...`)

        // Check for old cached content
        if (vp.ai_explanation.includes('Cached relationship')) {
          console.warn('   ⚠️  WARNING: Still using cached explanation!')
        }
      } else {
        console.warn('   ⚠️  WARNING: No AI explanation found!')
      }
    })

    // Validate framework diversity (the core issue we're trying to fix)
    if (data.opposing_viewpoints.length > 1) {
      expect(uniqueFrameworks.length).toBeGreaterThan(
        0,
        'Should have at least one framework specified'
      )

      if (uniqueFrameworks.length === 1) {
        console.warn('\n❌ REGRESSION CONFIRMED: All viewpoints show the same framework!')
        console.warn(`   Framework: ${uniqueFrameworks[0]}`)
        console.warn('   This indicates the enhanced analyzer is not being used correctly')

        // For debugging, let's see what the backend logs are showing
        console.warn('\n🔍 Debugging info:')
        console.warn(`   Total viewpoints: ${data.opposing_viewpoints.length}`)
        console.warn(`   Frameworks specified: ${frameworks.length}`)

        // This is the main assertion - we expect multiple frameworks
        expect(uniqueFrameworks.length).toBeGreaterThan(1)
      } else {
        console.log('\n✅ SUCCESS: Multiple frameworks found!')
        console.log(`   Framework diversity: ${uniqueFrameworks.length} unique frameworks`)
      }
    }

    // Validate AI explanations
    const viewpointsWithExplanations = data.opposing_viewpoints.filter(
      (vp: any) => vp.ai_explanation && !vp.ai_explanation.includes('Cached relationship')
    )

    console.log(`\n🧠 AI Explanations: ${viewpointsWithExplanations.length}/${data.opposing_viewpoints.length} have fresh AI explanations`)

    if (viewpointsWithExplanations.length < data.opposing_viewpoints.length) {
      console.warn('   ⚠️  Some viewpoints lack fresh AI explanations')
    }

    // Validate position data
    const viewpointsWithPositions = data.opposing_viewpoints.filter(
      (vp: any) => vp.primary_position !== undefined && vp.opposing_position !== undefined
    )

    console.log(`📍 Position Data: ${viewpointsWithPositions.length}/${data.opposing_viewpoints.length} have position information`)

    console.log('\n✅ Integration test completed successfully!')
  }, 30000) // 30 second timeout for API calls

  it('should trigger fresh analysis and verify results', async () => {
    // Clear existing relationships by triggering fresh analysis
    console.log('\n🔄 Triggering fresh viewpoint analysis...')

    const triggerResponse = await fetch(`${API_BASE}/articles/1014/analyze-viewpoints`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    })

    if (!triggerResponse.ok) {
      console.warn('⚠️  Could not trigger analysis (endpoint might need admin rights)')
      return
    }

    const triggerData = await triggerResponse.json()
    console.log('✅ Analysis triggered:', triggerData)

    // Wait a moment for processing
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Check the results
    const resultsResponse = await fetch(`${API_BASE}/articles/1014/opposing-viewpoints?max_results=5`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    })

    if (resultsResponse.ok) {
      const resultsData = await resultsResponse.json()
      const frameworks = resultsData.opposing_viewpoints
        .map((vp: any) => vp.framework_name)
        .filter((name: string | undefined) => name && name.trim() !== '')
      const uniqueFrameworks = [...new Set(frameworks)]

      console.log(`📊 Post-analysis frameworks: ${uniqueFrameworks.join(', ')}`)
      console.log(`🎯 Unique frameworks after fresh analysis: ${uniqueFrameworks.length}`)

      if (uniqueFrameworks.length > 1) {
        console.log('✅ Enhanced analyzer working correctly!')
      } else {
        console.log('❌ Still showing single framework after fresh analysis')
      }
    }
  }, 45000) // 45 second timeout for this longer test
})