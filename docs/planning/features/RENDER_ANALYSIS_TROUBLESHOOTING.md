# Render Analysis Troubleshooting Guide

## Issue: Articles Show "Analysis pending..." on Render Deployment

When articles display "Analysis pending..." it means they exist in the database but don't have associated `ArticleAnalysis` records. This guide will help you diagnose and fix the issue.

---

## 1. Check System Stats

First, check your system statistics to understand the current state:

```bash
curl https://your-render-backend.onrender.com/admin/stats
```

Look for:
- `articles.total`: Total number of articles
- `articles.completed`: Articles with status COMPLETED
- `articles.pending`: Articles awaiting processing
- `articles.failed`: Articles that failed processing

**What to look for:**
- If you have articles but all are `pending`, the extraction job isn't running
- If you have `completed` articles but they show "Analysis pending...", the AI analysis job isn't running

---

## 2. Check Scheduler Status

Check if the background scheduler is running:

```bash
curl https://your-render-backend.onrender.com/admin/scheduler/status
```

**Expected output:**
```json
{
  "status": "running",
  "jobs": [
    {
      "id": "analyze_articles",
      "name": "AI Article Analysis",
      "next_run": "2025-10-10 15:30:00",
      "trigger": "interval[0:06:00:00]"
    },
    ...
  ]
}
```

**What to check:**
- Status should be `"running"`
- Look for `analyze_articles` job
- Check the `next_run` time

---

## 3. Check Recent Articles

Get details about recent articles:

```bash
curl https://your-render-backend.onrender.com/admin/articles/recent?limit=5
```

**Look for:**
- `status`: Should be `COMPLETED` (not `PENDING`)
- `word_count`: Should have a value (indicates extraction worked)
- `extraction_method`: Should show `trafilatura` or `readability`

---

## 4. Common Issues & Solutions

### Issue A: Articles are PENDING (not extracted)

**Symptom:** Articles have `status: PENDING`

**Cause:** Article extraction job hasn't run

**Solution:** Manually trigger extraction:
```bash
curl -X POST https://your-render-backend.onrender.com/admin/jobs/extract
```

Wait 1-2 minutes, then check stats again.

---

### Issue B: Articles are COMPLETED but no Analysis

**Symptom:** Articles have `status: COMPLETED` and word_count, but show "Analysis pending..." in UI

**Cause:** AI analysis job hasn't run

**Solution:** Manually trigger analysis:
```bash
curl -X POST https://your-render-backend.onrender.com/admin/jobs/analyze
```

**Important:** Check that your OpenAI API key is set correctly in Render environment variables:
- Go to Render Dashboard → Your Backend Service → Environment
- Verify `OPENAI_API_KEY` is set
- Verify `AI_MODEL` is set to `gpt-4o-mini` (or your preferred model)

---

### Issue C: Scheduler Not Running

**Symptom:** `/admin/scheduler/status` returns `"status": "stopped"`

**Cause:** Scheduler failed to start on deployment

**Check Render Logs:**
1. Go to Render Dashboard → Your Backend Service → Logs
2. Search for:
   - `"APScheduler started successfully!"` ✅ Good
   - `"Scheduler is already running"` ⚠️ Warning but OK
   - Any errors mentioning scheduler or jobs ❌ Problem

**Solution:** Restart your backend service on Render

---

### Issue D: OpenAI API Key Issues

**Symptom:** Analysis jobs run but articles still not analyzed

**Check logs for:**
```
Error: OpenAI API key not found
Error: Incorrect API key provided
Error: You exceeded your current quota
```

**Solutions:**
1. **Missing key:** Add `OPENAI_API_KEY` to Render environment variables
2. **Wrong key:** Update the key in Render environment
3. **Quota exceeded:** Check your OpenAI account billing
4. **Rate limiting:** Wait and the job will retry on next schedule

---

## 5. Manual Analysis Pipeline

To manually run the complete pipeline in order:

### Step 1: Scrape Articles (if needed)
```bash
curl -X POST https://your-render-backend.onrender.com/admin/jobs/scrape
```
Wait 30 seconds.

### Step 2: Extract Content
```bash
curl -X POST https://your-render-backend.onrender.com/admin/jobs/extract
```
Wait 1-2 minutes (processes up to 50 articles).

### Step 3: Analyze with AI
```bash
curl -X POST https://your-render-backend.onrender.com/admin/jobs/analyze
```
Wait 1-2 minutes (processes up to 10 articles per run).

### Step 4: Generate Frameworks (optional)
```bash
curl -X POST https://your-render-backend.onrender.com/admin/jobs/frameworks
```

### Step 5: Verify Statistics (optional)
```bash
curl -X POST https://your-render-backend.onrender.com/admin/jobs/verify-statistics
```

### Step 6: Check Results
```bash
# Get stats
curl https://your-render-backend.onrender.com/admin/stats

# Check feed
curl https://your-render-backend.onrender.com/feed/articles?only_analyzed=true
```

---

## 6. Understanding the Analysis Job

The `analyze_job` function:
- Runs every **6 hours** automatically
- Processes **10 articles per run** (2 batches of 5)
- Only processes articles with `status: COMPLETED` that don't have analysis yet
- Requires valid OpenAI API key

**To process more articles faster:**
Run the analyze job multiple times:
```bash
for i in {1..5}; do
  curl -X POST https://your-render-backend.onrender.com/admin/jobs/analyze
  echo "Batch $i triggered, waiting 2 minutes..."
  sleep 120
done
```

This will process up to 50 articles (5 batches × 10 articles).

---

## 7. Monitoring Analysis Progress

Create a simple monitoring script:

```bash
#!/bin/bash
# monitor_analysis.sh

BACKEND_URL="https://your-render-backend.onrender.com"

while true; do
  STATS=$(curl -s $BACKEND_URL/admin/stats)
  TOTAL=$(echo $STATS | jq -r '.articles.total')
  COMPLETED=$(echo $STATS | jq -r '.articles.completed')
  PENDING=$(echo $STATS | jq -r '.articles.pending')

  echo "$(date): Total=$TOTAL, Completed=$COMPLETED, Pending=$PENDING"

  # Trigger analysis if there are completed articles
  if [ "$COMPLETED" -gt 0 ]; then
    curl -s -X POST $BACKEND_URL/admin/jobs/analyze
    echo "  → Analysis job triggered"
  fi

  sleep 300  # Check every 5 minutes
done
```

---

## 8. Quick Diagnosis Commands

Run these commands in sequence to quickly diagnose:

```bash
# Replace with your actual Render backend URL
BACKEND="https://your-render-backend.onrender.com"

echo "=== System Stats ==="
curl -s $BACKEND/admin/stats | jq

echo -e "\n=== Scheduler Status ==="
curl -s $BACKEND/admin/scheduler/status | jq

echo -e "\n=== Recent Articles ==="
curl -s $BACKEND/admin/articles/recent?limit=3 | jq

echo -e "\n=== Triggering Analysis ==="
curl -s -X POST $BACKEND/admin/jobs/analyze | jq

echo -e "\n=== Wait 60 seconds for analysis... ==="
sleep 60

echo -e "\n=== Check Feed (analyzed only) ==="
curl -s "$BACKEND/feed/articles?only_analyzed=true&page_size=5" | jq '.total_count'
```

---

## 9. Checking Article Analysis Status

To see which articles have analysis:

```sql
-- If you have direct DB access via Render dashboard
SELECT
    a.id,
    a.title,
    a.processing_status,
    a.word_count,
    CASE WHEN aa.id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_analysis
FROM articles a
LEFT JOIN article_analysis aa ON aa.article_id = a.id
ORDER BY a.scraped_at DESC
LIMIT 10;
```

Or via API:
```bash
# Get articles without analysis
curl "$BACKEND/feed/articles?page_size=100" | jq '.articles[] | select(.summary == null) | {id, title}'

# Get articles with analysis
curl "$BACKEND/feed/articles?only_analyzed=true&page_size=5" | jq '.articles[] | {id, title, summary}'
```

---

## 10. Expected Timeline

After triggering jobs, here's what to expect:

| Job | Duration | Output |
|-----|----------|--------|
| Scrape | 10-30s | New articles in DB with status PENDING |
| Extract | 1-2 min | Articles updated to COMPLETED with content |
| Analyze | 1-2 min | ArticleAnalysis records created (10 articles) |
| Frameworks | 30s-1min | Framework links created |

**Full pipeline for 50 articles:** ~15-20 minutes (5 analysis runs)

---

## Need More Help?

1. **Check Render Logs:** Most errors will appear in the logs
2. **Check OpenAI Dashboard:** Verify API usage and quota
3. **Check Environment Variables:** Ensure all required vars are set
4. **Restart Service:** Sometimes a fresh restart helps

**Key Environment Variables on Render:**
- `DATABASE_URL` ✅
- `OPENAI_API_KEY` ✅
- `AI_MODEL` (default: gpt-4o-mini) ✅
- `RESEND_API_KEY` (for newsletters)
- `SECRET_KEY` (for JWT)
