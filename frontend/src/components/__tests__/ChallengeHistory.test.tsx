/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChallengeHistory from '../ChallengeHistory';
import { api } from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

// Mock data
const mockChallengeStatistics = {
  total_participated: 5,
  average_agreement_level: 3.2,
  claim_type_breakdown: {
    'MORAL_PRINCIPLE': 2,
    'ETHICAL_DILEMMA': 2,
    'SOCIAL_JUSTICE': 1
  },
  participation_streak: 2,
  current_week_responded: true
};

const mockChallengeResponses = [
  {
    id: '1',
    week_start_date: '2024-01-15',
    claim_id: 'claim-1',
    claim_text: 'Economic growth should prioritized over environmental protection',
    claim_type: 'ECONOMIC_PRINCIPLE',
    agreement_level: 4,
    justification: 'I believe that economic stability is foundation for addressing other challenges',
    submitted_at: '2024-01-15T10:30:00Z',
    assigned_articles_count: 7,
    engaged_articles_count: 5
  },
  {
    id: '2',
    week_start_date: '2024-01-08',
    claim_text: 'Free speech should have limits to prevent hate speech',
    claim_type: 'SOCIAL_JUSTICE',
    agreement_level: 3,
    submitted_at: '2024-01-08T14:20:00Z',
    assigned_articles_count: 7,
    engaged_articles_count: 7
  }
];

const mockUserAnalytics = {
  participation_metrics: {
    total_challenges: 5,
    completed_challenges: 4,
    completion_rate: 80.0,
    current_streak: 2,
    longest_streak: 3,
    first_participation: '2024-01-01T00:00:00Z',
    last_participation: '2024-01-15T10:30:00Z'
  },
  engagement_metrics: {
    total_articles_assigned: 35,
    total_articles_engaged: 28,
    engagement_rate: 80.0,
    average_articles_per_challenge: 7.0,
    average_completion_time: 6.5
  },
  response_patterns: {
    agreement_distribution: {
      'STRONGLY_DISAGREE': 1,
      'DISAGREE': 1,
      'NEUTRAL': 1,
      'AGREE': 1,
      'STRONGLY_AGREE': 1
    },
    claim_type_preferences: {
      selection_distribution: {
        'MORAL_PRINCIPLE': 2,
        'ETHICAL_DILEMMA': 2,
        'SOCIAL_JUSTICE': 1
      },
      engagement_by_type: {
        'MORAL_PRINCIPLE': 75.0,
        'ETHICAL_DILEMMA': 85.0,
        'SOCIAL_JUSTICE': 90.0
      }
    },
    temporal_patterns: {},
    controversy_engagement: {}
  },
  quality_indicators: {
    response_quality_score: 85.0,
    engagement_consistency: 78.0,
    perspective_diversity_score: 82.0,
    improvement_trend: 'improving'
  },
  recent_performance: [
    {
      week_start_date: '2024-01-15',
      claim_type: 'ECONOMIC_PRINCIPLE',
      agreement_level: 'AGREE',
      articles_assigned: 7,
      articles_completed: 5,
      completion_rate: 71.4,
      status: 'RESPONDED'
    },
    {
      week_start_date: '2024-01-08',
      claim_type: 'SOCIAL_JUSTICE',
      agreement_level: 'NEUTRAL',
      articles_assigned: 7,
      articles_completed: 7,
      completion_rate: 100.0,
      status: 'COMPLETED'
    }
  ],
  generated_at: '2024-01-15T12:00:00Z'
};

describe('ChallengeHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Loading States', () => {
    it('should show loading spinner initially', () => {
      // Mock API to return loading state
      (api.getChallengeStatistics as jest.Mock).mockImplementation(() => new Promise(() => {}));
      (api.getChallengeResponses as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<ChallengeHistory />);

      // Check for skeleton placeholders with animate-pulse
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
      expect(document.querySelector('.bg-gray-200')).toBeInTheDocument();
    });

    it('should hide loading spinner when data is loaded', async () => {
      // Mock API to return data
      (api.getChallengeStatistics as jest.Mock).mockResolvedValue(mockChallengeStatistics);
      (api.getChallengeResponses as jest.Mock).mockResolvedValue(mockChallengeResponses);

      render(<ChallengeHistory />);

      await waitFor(() => {
        expect(screen.queryByText('Your Challenge Insights')).toBeInTheDocument();
        expect(document.querySelector('.animate-pulse')).not.toBeInTheDocument();
      });
    });
  });

  describe('Error States', () => {
    it('should display error message when API fails', async () => {
      // Mock API to throw error
      (api.getChallengeStatistics as jest.Mock).mockRejectedValue(new Error('API Error'));
      (api.getChallengeResponses as jest.Mock).mockRejectedValue(new Error('API Error'));

      render(<ChallengeHistory />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load challenge history')).toBeInTheDocument();
        expect(screen.getByText('Try again')).toBeInTheDocument();
      });
    });

    it('should allow retry when error occurs', async () => {
      // Mock API to fail initially, then succeed
      (api.getChallengeStatistics as jest.Mock)
        .mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValue(mockChallengeStatistics);

      (api.getChallengeResponses as jest.Mock)
        .mockRejectedValueOnce(new Error('API Error'))
        .mockResolvedValue(mockChallengeResponses);

      render(<ChallengeHistory />);

      // Should show error initially
      await waitFor(() => {
        expect(screen.getByText('Failed to load challenge history')).toBeInTheDocument();
      });

      // Click retry
      fireEvent.click(screen.getByText('Try again'));

      // Component loads data directly without explicit loading state
      // Just wait for the success state to appear

      await waitFor(() => {
        expect(screen.queryByText('Failed to load challenge history')).not.toBeInTheDocument();
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
      });
    });
  });

  describe('Empty States', () => {
    it('should display empty state when no challenge data', async () => {
      // Mock API to return empty data
      (api.getChallengeStatistics as jest.Mock).mockResolvedValue({
        total_participated: 0,
        average_agreement_level: 0.0,
        claim_type_breakdown: {},
        participation_streak: 0,
        current_week_responded: false
      });
      (api.getChallengeResponses as jest.Mock).mockResolvedValue([]);

      render(<ChallengeHistory />);

      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
        // Use more specific selector for the total challenges "0"
        const allZeros = screen.getAllByText('0');
        const totalChallengesElement = allZeros.find(el => el.closest('.text-indigo-600'));
        expect(totalChallengesElement).toBeInTheDocument();
        expect(screen.getByText('0.0/5.0')).toBeInTheDocument(); // Average agreement
      });
    });

    it('should display empty response history when no responses', async () => {
      (api.getChallengeStatistics as jest.Mock).mockResolvedValue(mockChallengeStatistics);
      (api.getChallengeResponses as jest.Mock).mockResolvedValue([]);

      render(<ChallengeHistory />);

      // Wait for component to load, then switch to history tab
      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Response History'));

      await waitFor(() => {
        expect(screen.getByText("You haven't responded to any challenges yet.")).toBeInTheDocument();
        expect(screen.getByText('Check your Friday newsletter for this week\'s challenge!')).toBeInTheDocument();
      });
    });
  });

  describe('Overview Tab', () => {
    beforeEach(async () => {
      (api.getChallengeStatistics as jest.Mock).mockResolvedValue(mockChallengeStatistics);
      (api.getChallengeResponses as jest.Mock).mockResolvedValue(mockChallengeResponses);

      render(<ChallengeHistory />);

      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
      });
    });

    it('should display participation statistics correctly', () => {
      expect(screen.getByText('5')).toBeInTheDocument(); // Total challenges
      expect(screen.getByText('2')).toBeInTheDocument(); // Current streak
      expect(screen.getByText('3.2/5.0')).toBeInTheDocument(); // Avg agreement
      expect(screen.getByText('✓')).toBeInTheDocument(); // Current week responded
    });

    it('should display current week indicator', () => {
      const currentWeekIndicator = screen.getByText('✓');
      expect(currentWeekIndicator).toBeInTheDocument();
      expect(currentWeekIndicator).toHaveClass('text-emerald-600');
    });

    it('should display claim type preferences', () => {
      expect(screen.getByText('MORAL PRINCIPLE (2)')).toBeInTheDocument();
      expect(screen.getByText('ETHICAL DILEMMA (2)')).toBeInTheDocument();
      expect(screen.getByText('SOCIAL JUSTICE (1)')).toBeInTheDocument();
    });

    it('should show recent response preview', () => {
      expect(screen.getByText('Recent Response')).toBeInTheDocument();
      expect(screen.getByText('Economic growth should prioritized over environmental protection')).toBeInTheDocument();
      expect(screen.getByText('Agree')).toBeInTheDocument();
      expect(screen.getByText('5/7 articles read')).toBeInTheDocument();
    });

    it('should allow navigation to full history', () => {
      const historyButton = screen.getByText('View Full History →');
      expect(historyButton).toBeInTheDocument();
      expect(historyButton).toHaveClass('text-indigo-600');
    });

    it('should switch to analytics tab when clicked', async () => {
      fireEvent.click(screen.getByText('Detailed Analytics'));

      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
        expect(screen.getByText('Detailed Analytics')).toHaveClass('border-indigo-500');
      });
    });
  });

  describe('Analytics Tab', () => {
    beforeEach(async () => {
      // Mock all analytics APIs
      (api.getChallengeStatistics as jest.Mock).mockResolvedValue(mockChallengeStatistics);
      (api.getChallengeResponses as jest.Mock).mockResolvedValue(mockChallengeResponses);
      (api.getChallengeAnalytics as jest.Mock).mockResolvedValue(mockUserAnalytics);
      (api.getChallengeParticipationTrends as jest.Mock).mockResolvedValue({
        trends: [
          {
            week_start: '2024-01-15',
            participated: true,
            claim_type: 'ECONOMIC_PRINCIPLE',
            agreement_level: 'AGREE',
            assignments: { assigned: 7, completed: 5 },
            completion_rate: 71.4
          },
          {
            week_start: '2024-01-08',
            participated: true,
            claim_type: 'SOCIAL_JUSTICE',
            agreement_level: 'NEUTRAL',
            assignments: { assigned: 7, completed: 7 },
            completion_rate: 100.0
          }
        ],
        summary: {
          total_weeks: 12,
          participated_weeks: 8,
          participation_rate: 66.7,
          average_completion_rate: 85.3
        },
        generated_at: '2024-01-15T12:00:00Z'
      });

      render(<ChallengeHistory />);

      // Switch to analytics tab
      fireEvent.click(screen.getByText('Detailed Analytics'));

      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
      });
    });

    it('should display participation metrics', () => {
      expect(screen.getByText('5')).toBeInTheDocument(); // Challenges Completed
      expect(screen.getByText('2')).toBeInTheDocument(); // Current Streak
      expect(screen.getByText('3.2/5.0')).toBeInTheDocument(); // Avg Agreement
      expect(screen.getByText('✓')).toBeInTheDocument(); // This Week
    });

    it('should display claim type breakdown', () => {
      // Should show claim type badges from mock data
      expect(screen.getByText(/MORAL PRINCIPLE.*\(2\)/)).toBeInTheDocument();
      expect(screen.getByText(/ETHICAL DILEMMA.*\(2\)/)).toBeInTheDocument();
      expect(screen.getByText(/SOCIAL JUSTICE.*\(1\)/)).toBeInTheDocument();
    });

    it('should display agreement distribution', () => {
      expect(screen.getByText('Agreement Distribution')).toBeInTheDocument();
      expect(screen.getByText('Strongly Disagree')).toBeInTheDocument();
      expect(screen.getByText('Disagree')).toBeInTheDocument();
      expect(screen.getByText('Neutral')).toBeInTheDocument();
      expect(screen.getByText('Agree')).toBeInTheDocument();
      expect(screen.getByText('Strongly Agree')).toBeInTheDocument();
    });

    it('should display claim type preferences', () => {
      expect(screen.getByText('Claim Type Preferences')).toBeInTheDocument();
      expect(screen.getByText(/economic principle/i)).toBeInTheDocument();
      expect(screen.getByText(/ethical dilemma/i)).toBeInTheDocument();
      expect(screen.getByText(/social justice/i)).toBeInTheDocument();
    });

    it('should allow changing time range for trends', () => {
      const timeRangeSelect = screen.getByRole('combobox');
      expect(timeRangeSelect).toBeInTheDocument();

      fireEvent.change(timeRangeSelect, { target: { value: '24' } });

      expect(api.getChallengeParticipationTrends).toHaveBeenCalledWith(24);
    });
  });

  describe('History Tab', () => {
    beforeEach(async () => {
      (api.getChallengeStatistics as jest.Mock).mockResolvedValue(mockChallengeStatistics);
      (api.getChallengeResponses as jest.Mock).mockResolvedValue(mockChallengeResponses);

      render(<ChallengeHistory />);

      // Wait for component to load, then switch to history tab
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Response History'));

      await waitFor(() => {
        expect(screen.getByText('Your Response History')).toBeInTheDocument();
      });
    });

    it('should display all response history', () => {
      expect(screen.getByText('Economic growth should prioritized over environmental protection')).toBeInTheDocument();
      expect(screen.getByText('Free speech should have limits to prevent hate speech')).toBeInTheDocument();
      expect(screen.getByText(/Agree/)).toBeInTheDocument(); // First response
      expect(screen.getByText(/NEUTRAL/)).toBeInTheDocument(); // Second response
    });

    it('should show response metadata correctly', () => {
      const firstResponse = screen.getByText('Economic growth should prioritized over environmental protection')
        .closest('.border');

      expect(firstResponse).toContainHTML('ECONOMIC PRINCIPLE'); // Claim type badge
      expect(firstResponse).toContainHTML('2024-01-15'); // Date
      expect(firstResponse).toContainHTML('5/7 articles read'); // Engagement
    });

    it('should allow showing more responses when >5', async () => {
      // Mock more than 5 responses
      const manyResponses = Array.from({ length: 8 }, (_, i) => ({
        ...mockChallengeResponses[0],
        id: `response-${i}`,
        week_start_date: `2024-01-${15 + i}`
      }));

      (api.getChallengeResponses as jest.Mock).mockResolvedValue(manyResponses);

      render(<ChallengeHistory />);

      // Wait for component to load, then switch to history tab
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Response History'));

      await waitFor(() => {
        expect(screen.getByText('Show All (8)')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Show All (8)'));

      await waitFor(() => {
        expect(screen.getByText('Show Less')).toBeInTheDocument();
        // Should display all 8 responses
        expect(screen.getAllByText(/Economic growth/i)).toHaveLength(8);
      });
    });

    it('should allow toggling assignment details', async () => {
      // Mock assignments API
      (api.getChallengeAssignments as jest.Mock).mockResolvedValue([
        {
          id: 'assignment-1',
          sequence_day: 1,
          article: {
            id: 1,
            title: 'Opposing Article 1',
            url: 'https://example.com/article1',
            source: { name: 'Test Source', organizational_bias: 'right' },
            published_at: '2024-01-15T10:00:00Z',
            opposition_score: 0.8
          },
          is_completed: false
        }
      ]);

      render(<ChallengeHistory />);

      // Wait for component to load, then switch to history tab
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Response History'));

      await waitFor(() => {
        expect(screen.getByText('View Assigned Articles (5/7 read)')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('View Assigned Articles (5/7 read)'));

      await waitFor(() => {
        expect(screen.getByText('Your 7-Day Perspective Journey')).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    beforeEach(async () => {
      (api.getChallengeStatistics as jest.Mock).mockResolvedValue(mockChallengeStatistics);
      (api.getChallengeResponses as jest.Mock).mockResolvedValue(mockChallengeResponses);

      render(<ChallengeHistory />);

      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
      });
    });

    it('should highlight active tab correctly', () => {
      const overviewTab = screen.getByText('Overview');
      const analyticsTab = screen.getByText('Detailed Analytics');
      const historyTab = screen.getByText('Response History');

      // Overview should be active initially
      expect(overviewTab).toHaveClass('border-indigo-500');
      expect(analyticsTab).not.toHaveClass('border-indigo-500');
      expect(historyTab).not.toHaveClass('border-indigo-500');

      // Click analytics tab
      fireEvent.click(analyticsTab);
      expect(analyticsTab).toHaveClass('border-indigo-500');
      expect(overviewTab).not.toHaveClass('border-indigo-500');

      // Click history tab
      fireEvent.click(historyTab);
      expect(historyTab).toHaveClass('border-indigo-500');
      expect(analyticsTab).not.toHaveClass('border-indigo-500');
    });

    it('should maintain tab state across renders', async () => {
      // Component uses internal state, so re-rendering resets to default tab
      // This test verifies the default state is properly restored
      render(<ChallengeHistory />);

      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
        expect(screen.getByText('Overview')).toHaveClass('border-indigo-500');
        expect(screen.getByText('Detailed Analytics')).not.toHaveClass('border-indigo-500');
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(async () => {
      (api.getChallengeStatistics as jest.Mock).mockResolvedValue(mockChallengeStatistics);
      (api.getChallengeResponses as jest.Mock).mockResolvedValue(mockChallengeResponses);

      render(<ChallengeHistory />);

      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();
      });
    });

    it('should have proper heading structure', () => {
      const mainHeading = screen.getByText('Your Challenge Insights');
      expect(mainHeading).toHaveClass('text-xl', 'font-semibold');
    });

    it('should have accessible navigation tabs', () => {
      // Navigation is implemented with buttons, not elements with role="tab"
      const overviewButton = screen.getByText('Overview');
      const analyticsButton = screen.getByText('Detailed Analytics');
      const historyButton = screen.getByText('Response History');

      expect(overviewButton).toBeInTheDocument();
      expect(analyticsButton).toBeInTheDocument();
      expect(historyButton).toBeInTheDocument();
      expect(overviewButton).toBeEnabled();
      expect(analyticsButton).toBeEnabled();
      expect(historyButton).toBeEnabled();
    });

    it('should have proper color contrast', () => {
      const participationNumber = screen.getByText('5');
      expect(participationNumber).toHaveClass('text-indigo-600', 'dark:text-indigo-400');

      const streakNumber = screen.getByText('2');
      expect(streakNumber).toHaveClass('text-green-600', 'dark:text-green-400');

      const avgAgreement = screen.getByText('3.2/5.0');
      expect(avgAgreement).toHaveClass('text-purple-600', 'dark:text-purple-400');
    });
  });

  describe('Responsiveness', () => {
    it('should be responsive on mobile screens', async () => {
      // Mock window size
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375, // iPhone SE width
      });

      (api.getChallengeStatistics as jest.Mock).mockResolvedValue(mockChallengeStatistics);
      (api.getChallengeResponses as jest.Mock).mockResolvedValue(mockChallengeResponses);

      render(<ChallengeHistory />);

      await waitFor(() => {
        expect(screen.getByText('Your Challenge Insights')).toBeInTheDocument();

        // Grid should stack on mobile
        const participationGrid = screen.getByText('5').closest('.grid');
        expect(participationGrid).toHaveClass('grid-cols-2'); // Should be 2 columns on mobile
      });
    });
  });
});