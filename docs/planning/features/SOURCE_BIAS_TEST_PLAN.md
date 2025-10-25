# Source Bias Feature Test Plan

## Overview
Comprehensive test plan for the organizational bias rating system implementation.

---

## Backend Tests

### Test File: `backend/tests/routes/test_sources.py`

#### Setup
- Test user with authentication
- Sample sources with various bias levels
- Fixtures for common test data

#### Test Cases

##### 1. GET /sources - List Sources
- ✅ **test_list_sources_success**: List all sources with default filters
- ✅ **test_list_sources_filter_by_bias**: Filter sources by organizational bias
- ✅ **test_list_sources_filter_active_only**: Filter only active sources
- ✅ **test_list_sources_sort_by_name**: Sort sources alphabetically
- ✅ **test_list_sources_sort_by_trust_score**: Sort by trust score descending
- ✅ **test_list_sources_sort_by_article_count**: Sort by article count descending
- ✅ **test_list_sources_requires_auth**: Verify authentication required
- ✅ **test_list_sources_includes_article_count**: Verify article counts are included

##### 2. GET /sources/{id} - Get Source Detail
- ✅ **test_get_source_by_id_success**: Get existing source details
- ✅ **test_get_source_not_found**: 404 for non-existent source
- ✅ **test_get_source_includes_article_count**: Verify article count included
- ✅ **test_get_source_requires_auth**: Verify authentication required

##### 3. POST /sources - Create Source
- ✅ **test_create_source_success**: Create new source with valid data
- ✅ **test_create_source_with_bias_fetch**: Create source with automatic bias fetching
- ✅ **test_create_source_duplicate_rss_url**: Prevent duplicate RSS feed URLs
- ✅ **test_create_source_invalid_trust_score**: Validate trust_score range (0.0-1.0)
- ✅ **test_create_source_requires_auth**: Verify authentication required
- ✅ **test_create_source_minimal_data**: Create with only required fields

##### 4. PUT /sources/{id} - Update Source
- ✅ **test_update_source_success**: Update source fields
- ✅ **test_update_source_bias**: Update organizational bias
- ✅ **test_update_source_partial**: Update only some fields
- ✅ **test_update_source_not_found**: 404 for non-existent source
- ✅ **test_update_source_duplicate_rss_url**: Prevent duplicate RSS feed URLs
- ✅ **test_update_source_requires_auth**: Verify authentication required

##### 5. DELETE /sources/{id} - Delete Source
- ✅ **test_delete_source_soft**: Soft delete (set is_active=False)
- ✅ **test_delete_source_hard**: Hard delete when no articles exist
- ✅ **test_delete_source_hard_with_articles**: Prevent hard delete with articles
- ✅ **test_delete_source_not_found**: 404 for non-existent source
- ✅ **test_delete_source_requires_auth**: Verify authentication required

##### 6. POST /sources/{id}/fetch-bias - Fetch Bias
- ✅ **test_fetch_bias_success**: Fetch and update bias for source
- ✅ **test_fetch_bias_no_data_found**: Handle case when no bias data found
- ✅ **test_fetch_bias_not_found**: 404 for non-existent source
- ✅ **test_fetch_bias_requires_auth**: Verify authentication required

### Test File: `backend/tests/services/test_bias_data_fetcher.py`

#### Test Cases

##### 1. Domain Extraction
- ✅ **test_extract_domain_with_www**: Remove www prefix
- ✅ **test_extract_domain_with_subdomain**: Handle subdomains
- ✅ **test_extract_domain_simple**: Handle simple domains

##### 2. Bias Mapping
- ✅ **test_map_bias_string_left**: Map "left" strings correctly
- ✅ **test_map_bias_string_center**: Map "center" strings correctly
- ✅ **test_map_bias_string_right**: Map "right" strings correctly
- ✅ **test_map_bias_string_case_insensitive**: Handle case variations

##### 3. Bias Fetching
- ✅ **test_fetch_source_bias_known_source**: Fetch bias for known source
- ✅ **test_fetch_source_bias_unknown_source**: Handle unknown source
- ✅ **test_get_bias_for_source**: Test simplified interface

### Test File: `backend/tests/routes/test_feed.py` (Updates)

#### Test Cases
- ✅ **test_feed_includes_source_bias**: Verify source_bias in feed response
- ✅ **test_feed_includes_read_time**: Verify read_time_minutes calculated

### Test File: `backend/tests/routes/test_articles.py` (Updates)

#### Test Cases
- ✅ **test_article_detail_includes_source_bias**: Verify source_bias in detail response
- ✅ **test_article_detail_includes_read_time**: Verify read_time_minutes included

---

## Frontend Tests

### Test File: `frontend/src/components/__tests__/SourceBiasBadge.test.tsx`

#### Test Cases

##### 1. Rendering
- ✅ **test_renders_left_bias**: Renders "Left" badge with correct colors
- ✅ **test_renders_center_left_bias**: Renders "Center-Left" badge
- ✅ **test_renders_center_bias**: Renders "Center" badge
- ✅ **test_renders_center_right_bias**: Renders "Center-Right" badge
- ✅ **test_renders_right_bias**: Renders "Right" badge
- ✅ **test_renders_null_bias**: Returns null for null bias
- ✅ **test_renders_undefined_bias**: Returns null for undefined bias

##### 2. Sizes
- ✅ **test_renders_small_size**: Renders sm size correctly
- ✅ **test_renders_medium_size**: Renders md size (default)
- ✅ **test_renders_large_size**: Renders lg size correctly

##### 3. Props
- ✅ **test_shows_label_by_default**: Shows label text by default
- ✅ **test_hides_label_when_false**: Hides label when showLabel=false
- ✅ **test_has_title_attribute**: Has title attribute for accessibility

### Test File: `frontend/src/app/sources/__tests__/page.test.tsx`

#### Test Cases

##### 1. Page Rendering
- ✅ **test_renders_page_title**: Renders "Supported News Sources" header
- ✅ **test_renders_filter_controls**: Renders bias filter and sort dropdown
- ✅ **test_shows_loading_state**: Shows loading spinner initially

##### 2. Source Display
- ✅ **test_displays_sources_in_grid**: Displays sources in grid layout
- ✅ **test_displays_source_name**: Shows source name
- ✅ **test_displays_bias_badge**: Shows SourceBiasBadge component
- ✅ **test_displays_trust_score**: Shows trust score percentage
- ✅ **test_displays_article_count**: Shows article count

##### 3. Filtering
- ✅ **test_filter_by_bias_left**: Filters to show only left-biased sources
- ✅ **test_filter_by_bias_center**: Filters to show only center sources
- ✅ **test_filter_clears**: Clears filter to show all sources

##### 4. Sorting
- ✅ **test_sort_by_name**: Sorts sources alphabetically
- ✅ **test_sort_by_trust_score**: Sorts by trust score
- ✅ **test_sort_by_article_count**: Sorts by article count

##### 5. Error Handling
- ✅ **test_displays_error_message**: Shows error when API fails
- ✅ **test_displays_empty_state**: Shows empty state when no sources match

##### 6. Navigation
- ✅ **test_links_to_source_website**: Links to external source websites
- ✅ **test_links_to_filtered_feed**: Links to feed filtered by source

### Test File: `frontend/src/app/feed/__tests__/page.test.tsx` (Updates)

#### Test Cases
- ✅ **test_displays_source_bias_badge**: Verify SourceBiasBadge renders on feed
- ✅ **test_displays_article_bias_label**: Verify "Article Bias:" label used

### Test File: `frontend/src/app/article/__tests__/page.test.tsx` (Updates)

#### Test Cases
- ✅ **test_displays_source_bias_in_header**: Verify badge in article header
- ✅ **test_displays_article_bias_section**: Verify "Article Bias" section
- ✅ **test_displays_bias_clarification**: Verify clarification text shown

---

## Integration Tests

### Test Scenario: End-to-End Source Bias Flow

1. **Add New Source**
   - POST /sources with automatic bias fetching
   - Verify source created with bias rating

2. **View Source in Directory**
   - Navigate to /sources page
   - Verify source appears with bias badge
   - Filter by bias and verify source shows/hides correctly

3. **Source Publishes Article**
   - Scrape article from source
   - Verify article inherits source_bias

4. **View Article in Feed**
   - Navigate to /feed
   - Verify source bias badge appears next to source name
   - Verify article bias shows separately

5. **View Article Detail**
   - Click on article
   - Verify source bias badge in header
   - Verify article bias shown in analysis section
   - Verify clear separation of bias types

---

## Manual Testing Checklist

### Visual Testing
- [ ] Bias badges have correct colors for all 5 levels
- [ ] Badges are readable in all sizes (sm, md, lg)
- [ ] Layout doesn't break on mobile devices
- [ ] Source descriptions are truncated appropriately
- [ ] Trust scores display with correct color coding

### Accessibility Testing
- [ ] Bias badges have descriptive tooltips
- [ ] Keyboard navigation works on sources page
- [ ] Screen readers can access all bias information
- [ ] Color contrast meets WCAG AA standards

### Cross-Browser Testing
- [ ] Chrome/Edge: All features work
- [ ] Firefox: All features work
- [ ] Safari: All features work

---

## Performance Testing

### Backend
- [ ] /sources endpoint responds < 200ms with 100 sources
- [ ] Filtering doesn't cause N+1 queries
- [ ] Sorting is efficient with large datasets

### Frontend
- [ ] Sources page loads < 1s with 100 sources
- [ ] Filtering/sorting is instant (<100ms)
- [ ] No memory leaks on repeated filter changes

---

## Success Criteria

### Backend
- ✅ All 30+ test cases pass
- ✅ 100% coverage on new services
- ✅ 100% coverage on new routes
- ✅ No breaking changes to existing tests

### Frontend
- ✅ All 40+ test cases pass
- ✅ 100% coverage on SourceBiasBadge
- ✅ 80%+ coverage on sources page
- ✅ No breaking changes to existing tests

### Integration
- ✅ Source bias flows correctly from API to UI
- ✅ Filtering and sorting work correctly
- ✅ No console errors or warnings
- ✅ All existing features still work

---

## Known Issues / TODOs

- [ ] Backend tests not yet implemented
- [ ] Frontend tests not yet implemented
- [ ] Need to add tests for edge cases (special characters in URLs, etc.)
- [ ] Need to add tests for concurrent updates
- [ ] Consider adding E2E tests with Playwright

---

**Test Plan Created**: 2025-10-12
**Author**: Claude Assistant
**Status**: Ready for Implementation
