# Statistics Verification Logging Guide

This guide explains how to interpret the enhanced logging in the statistics verification pipeline to debug why statistics aren't being extracted or why sources aren't being found.

## Overview

The statistics verification pipeline has three main stages, each with detailed logging:

1. **[EXTRACT]** - Extracting statistics from articles using AI
2. **[VERIFY]** - Verifying statistics through the 3-stage pipeline
3. **[TRACE]** - Tracing statistics to their original sources

## Log Prefixes

- `[EXTRACT]` - Statistics extraction from articles
- `[VERIFY]` - Overall verification process
- `[TRACE]` - Source tracing (within VERIFY Stage 1)
- `[TRACE-WEB]` - Web search details (within TRACE Method 2)

## Viewing Logs

### Real-time logs
```bash
docker logs news_backend -f
```

### Filter for statistics verification
```bash
docker logs news_backend 2>&1 | grep -E "\[EXTRACT\]|\[VERIFY\]|\[TRACE\]"
```

### Show only successful extractions
```bash
docker logs news_backend 2>&1 | grep "\[EXTRACT\] ✅"
```

### Show only failed source traces
```bash
docker logs news_backend 2>&1 | grep "\[TRACE\] ❌"
```

---

## Understanding Extraction Logs

### Successful Extraction
```
INFO:[EXTRACT] Starting extraction for article 31: 'The EU's new border system explained'
INFO:[EXTRACT] ✅ Extracted 3 statistics from article 31
```

**What this means:**
- AI found 3 verifiable statistics in the article
- Each will now go through the verification pipeline

### No Statistics Found
```
INFO:[EXTRACT] Starting extraction for article 98: 'Today's Atlantic Trivia'
INFO:[EXTRACT] Article 98 - No statistics found by AI
```

**Why this happens:**
- Article contains no quantifiable claims
- Article is too short or lacks concrete data
- AI determined claims aren't verifiable

**What to check:**
- Review the article summary (used for extraction)
- Check if the article actually contains statistics
- Verify OpenAI API is working

### Failed Extraction
```
ERROR:[EXTRACT] ❌ Article 42 - Failed to parse AI response as JSON: ...
```

**Why this happens:**
- AI returned invalid JSON
- Network error calling OpenAI API
- API rate limit hit

**What to do:**
- Check OpenAI API key is valid
- Verify API rate limits
- Check network connectivity

---

## Understanding Verification Logs

### Full Verification Flow
```
INFO:[VERIFY] Starting V2 verification for: '29 European countries covered'
INFO:[VERIFY] Stage 1: Tracing source for '29 European countries covered'
INFO:[VERIFY] ✅ Stage 1: Found source - 'European Commission' via article_content
INFO:[VERIFY] Stage 2: Rating credibility for 'European Commission'
INFO:[VERIFY] ✅ Stage 2: Credibility score: 0.85
INFO:[VERIFY] Stage 3: Fact-checking '29 European countries covered'
INFO:[VERIFY] ✅ COMPLETE: Status: verified, Confidence: 0.72, Method: ai_analysis
```

**What this means:**
- Source was found in the article text
- Source is credible (0.85/1.0)
- Statistic was marked as VERIFIED

### No Source Found
```
INFO:[VERIFY] Starting V2 verification for: '325m views'
WARNING:[VERIFY] ⚠️ Stage 1: No source found for '325m views'
WARNING:[VERIFY] ⚠️ Stage 2: Skipping credibility rating (missing URL or name)
INFO:[VERIFY] Setting note: No source found
INFO:[VERIFY] ✅ COMPLETE: Status: unverified, Confidence: 0.00
```

**Why this happens:**
- No source mentioned in article text
- Web search found no relevant results
- No similar statistics in database

**What to check:**
- Look at TRACE logs for details
- Check if Google Search API is configured
- Review the article content quality

---

## Understanding Source Tracing Logs

### Method 1: Article Content (Success)
```
INFO:[TRACE] Starting source trace for: 'Rotten Tomatoes score'
INFO:[TRACE] Method 1: Searching within article content...
INFO:[TRACE] Method 1: Found candidate source 'Rotten Tomatoes' (confidence: 0.85)
INFO:[TRACE] ✅ Method 1: Validated source 'Rotten Tomatoes' in article
```

**What this means:**
- AI found the source mentioned in the article
- Source name appears near the statistic (validation passed)

### Method 1: Article Content (Failed Validation)
```
INFO:[TRACE] Method 1: Found candidate source 'Johns Hopkins' (confidence: 0.75)
WARNING:[TRACE] ⚠️ Method 1: Source 'Johns Hopkins' failed relevance check, trying web search
```

**Why this happens:**
- AI extracted a source name, but it appears far from the statistic
- Likely a false positive (unrelated source mentioned elsewhere)

### Method 2: Web Search (Success)
```
INFO:[TRACE] Method 1: No source found in article
INFO:[TRACE] Method 2: Searching web (Google Custom Search)...
INFO:[TRACE-WEB] Extracted keywords: 'Nosferatu Rotten Tomatoes'
INFO:[TRACE-WEB] Detected entertainment stat, adding movie-specific queries
INFO:[TRACE-WEB] Trying 7 search queries
INFO:[TRACE-WEB] Query 1/7: '"Nosferatu Rotten Tomatoes score"'
INFO:[TRACE-WEB] Got 10 results for query 1
INFO:[TRACE-WEB] Result 3 score: 0.85 - Nosferatu Reviews [rottentomatoes.com]
INFO:[TRACE-WEB] New best result: score=0.85, domain=rottentomatoes.com
INFO:[TRACE] ✅ Method 2: Found source via web search: 'Rotten Tomatoes' (score: 0.85)
```

**What this means:**
- Article didn't mention the source
- Web search found a highly relevant result
- URL points to specific page (not homepage)

### Method 2: Web Search (No Results)
```
INFO:[TRACE] Method 2: Searching web (Google Custom Search)...
INFO:[TRACE-WEB] Trying 5 search queries
WARNING:[TRACE-WEB] No relevant search results found (best score: 0.32, threshold: 0.4)
INFO:[TRACE] Method 2: No relevant web results found
```

**Why this happens:**
- No web pages found with the statistic
- Results were too generic (homepages, unrelated content)
- Best score below 0.4 threshold

**What to check:**
- Try the search query manually on Google
- Check if the statistic is too vague
- Verify Google Custom Search API is configured

### Method 2: Skipped (No API)
```
INFO:[TRACE] Method 1: No source found in article
DEBUG:[TRACE] Method 2: Skipping (Google API not configured)
```

**What this means:**
- `GOOGLE_FACT_CHECK_API_KEY` or `GOOGLE_SEARCH_ENGINE_ID` not set
- Web search is disabled

**What to do:**
- Add Google API credentials to `.env`
- See [SETUP.md](SETUP.md) for Google Custom Search setup

### Method 3: Database Search
```
INFO:[TRACE] Method 3: Searching database for similar statistics...
INFO:[TRACE] ✅ Method 3: Found source in database: 'CDC'
```

**What this means:**
- Found another article with the same statistic
- Reusing previously verified source

---

## Debugging Common Issues

### Issue: No Statistics Extracted from Articles

**Symptoms:**
```
INFO:[EXTRACT] Article 42 - No statistics found by AI
INFO:[EXTRACT] Article 43 - No statistics found by AI
```

**Possible Causes:**
1. Articles genuinely don't contain statistics
2. Article summaries are too short/vague
3. OpenAI API issues

**Debug Steps:**
1. Check article summaries:
   ```bash
   docker logs news_backend 2>&1 | grep "Summary length"
   ```
2. Verify articles in database actually have data
3. Check OpenAI API usage/errors

---

### Issue: Sources Not Found for Statistics

**Symptoms:**
```
WARNING:[VERIFY] ⚠️ Stage 1: No source found for 'statistic'
INFO:[VERIFY] Setting note: No source found
```

**Possible Causes:**
1. Article doesn't mention the source
2. Web search API not configured
3. Statistic is too vague for web search

**Debug Steps:**
1. Check if web search is enabled:
   ```bash
   docker logs news_backend 2>&1 | grep "Method 2: Skipping"
   ```
2. Look at web search results:
   ```bash
   docker logs news_backend 2>&1 | grep "\[TRACE-WEB\]"
   ```
3. Review the article content to see if source is mentioned

---

### Issue: Web Search Finds Wrong URLs

**Symptoms:**
```
INFO:[TRACE-WEB] Result 1 score: 0.45 - [rottentomatoes.com]
WARNING:[TRACE-WEB] Skipping result 1: homepage URL
```

**Possible Causes:**
1. Search results are too generic
2. Homepage filtering is too aggressive
3. Scoring algorithm needs tuning

**Debug Steps:**
1. Check what URLs were found:
   ```bash
   docker logs news_backend 2>&1 | grep "Result.*score"
   ```
2. See which URLs were skipped:
   ```bash
   docker logs news_backend 2>&1 | grep "Skipping result"
   ```
3. Review search queries being used:
   ```bash
   docker logs news_backend 2>&1 | grep "Query.*:"
   ```

---

## Log Levels

The logging uses different levels:

- **INFO** - Normal operation, successful steps
- **DEBUG** - Detailed information (queries, scores, intermediate results)
- **WARNING** - Non-critical issues (no results, skipped steps)
- **ERROR** - Critical failures (API errors, exceptions)

### Enabling DEBUG Logs

To see more detailed logs (including search queries and scores), set log level in `backend/app/config.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

Or via environment variable:
```bash
LOG_LEVEL=DEBUG docker-compose up
```

---

## Example Full Flow

Here's an example of a successful verification with all stages:

```
INFO:[EXTRACT] Starting extraction for article 23: 'Movie breaks box office records'
INFO:[EXTRACT] ✅ Extracted 2 statistics from article 23

INFO:[VERIFY] Starting V2 verification for: 'Nosferatu earned 97% on Rotten Tomatoes'
INFO:[VERIFY] Stage 1: Tracing source for 'Nosferatu earned 97% on Rotten Tomatoes'
INFO:[TRACE] Starting source trace for: 'Nosferatu earned 97% on Rotten Tomatoes'
INFO:[TRACE] Method 1: Searching within article content...
INFO:[TRACE] Method 1: No source found in article
INFO:[TRACE] Method 2: Searching web (Google Custom Search)...
INFO:[TRACE-WEB] Extracted keywords: 'Nosferatu Rotten Tomatoes'
INFO:[TRACE-WEB] Detected entertainment stat, adding movie-specific queries
INFO:[TRACE-WEB] Trying 7 search queries
INFO:[TRACE-WEB] Query 1/7: '"Nosferatu earned 97% on Rotten Tomatoes"'
INFO:[TRACE-WEB] Got 8 results for query 1
INFO:[TRACE-WEB] Result 1 score: 0.92 - Nosferatu (2024) Reviews [rottentomatoes.com/m/nosferatu_2024]
INFO:[TRACE-WEB] New best result: score=0.92, domain=rottentomatoes.com
INFO:[TRACE] ✅ Method 2: Found source via web search: 'Rotten Tomatoes' (score: 0.92)
INFO:[VERIFY] ✅ Stage 1: Found source - 'Rotten Tomatoes' via web_search
INFO:[VERIFY] Source URL: https://www.rottentomatoes.com/m/nosferatu_2024
INFO:[VERIFY] Stage 2: Rating credibility for 'Rotten Tomatoes'
INFO:[VERIFY] ✅ Stage 2: Credibility score: 0.75
INFO:[VERIFY] Stage 3: Fact-checking 'Nosferatu earned 97% on Rotten Tomatoes'
INFO:[VERIFY] ✅ COMPLETE: Status: verified, Confidence: 0.68, Method: ai_analysis
```

**What happened:**
1. AI extracted the statistic from the article
2. Source not found in article text (Method 1 failed)
3. Web search found the exact Rotten Tomatoes page (Method 2 succeeded)
4. Source was rated as credible (0.75/1.0)
5. Final status: VERIFIED with 68% confidence

---

## Tips for Debugging

1. **Always start with EXTRACT logs** - If statistics aren't being extracted, verification won't run
2. **Check for "✅" success markers** - These show which stages succeeded
3. **Look for "⚠️" and "❌" markers** - These indicate problems
4. **Follow the flow**: EXTRACT → VERIFY → TRACE → Methods 1/2/3
5. **Use grep to filter** - Don't try to read all logs at once
6. **Compare successful vs failed** - Look at what's different between stats that get verified vs those that don't

---

## Related Documentation

- [API.md](API.md) - API endpoints for triggering verification
- [STATISTICS_VERIFICATION_V2_PLAN.md](STATISTICS_VERIFICATION_V2_PLAN.md) - V2 pipeline design
- [SETUP.md](SETUP.md) - Configuration including Google API setup
