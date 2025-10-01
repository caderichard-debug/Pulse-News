# API Keys Setup Guide

This document explains how to obtain and configure the required API keys for the Pulse News Aggregator.

## Required API Keys

The application requires two API keys to function:

1. **Anthropic Claude API** - For AI-powered article analysis and framework generation
2. **Resend API** - For sending email newsletters (optional for initial testing)

---

## 1. Anthropic Claude API Setup

Claude is used for batch article analysis (summarization, sentiment, bias detection) and framework generation.

### Getting Your API Key

1. **Create an Anthropic Account**
   - Go to: https://console.anthropic.com/
   - Click "Sign Up" and create an account
   - Verify your email address

2. **Add Payment Method**
   - Navigate to Settings → Billing
   - Add a credit card (required even for low usage)
   - Note: You only pay for what you use

3. **Generate API Key**
   - Go to Settings → API Keys
   - Click "Create Key"
   - Give it a name (e.g., "Pulse News Dev")
   - Copy the key immediately (you won't see it again)

### Pricing Information

- **Model Used**: Claude 3 Haiku (fastest, cheapest)
- **Input Cost**: $0.25 per million tokens (~750k words)
- **Output Cost**: $1.25 per million tokens
- **Estimated Monthly Cost**: $2-5 for 50 users

### Example Usage Calculation

For 50 users receiving daily newsletters:
- ~100 articles/day analyzed
- ~5 API calls/day (batches of 5 articles)
- ~150 API calls/month
- Estimated cost: **$3-5/month**

---

## 2. Resend API Setup

Resend is used for sending email newsletters. This is optional if you're just testing the scraping/analysis pipeline.

### Getting Your API Key

1. **Create a Resend Account**
   - Go to: https://resend.com/signup
   - Sign up with email or GitHub
   - Verify your email

2. **Free Tier Details**
   - 3,000 emails/month free
   - 100 emails/day limit
   - Perfect for initial 50-100 users

3. **Generate API Key**
   - Go to API Keys in the dashboard
   - Click "Create API Key"
   - Name it (e.g., "Pulse Newsletter")
   - Copy the key

4. **Domain Setup** (Optional for Production)
   - For testing, you can send from `onboarding@resend.dev`
   - For production, add and verify your custom domain
   - Follow Resend's DNS setup instructions

---

## 3. Configuring Your Environment

### Option A: Using .env File (Recommended)

1. **Create a .env file** in the `backend/` directory:

```bash
cd backend
touch .env
```

2. **Add your API keys** to the `.env` file:

```env
# Database (leave as default for local Docker setup)
DATABASE_URL=postgresql://postgres:password@db:5432/news_db

# Anthropic Claude API (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Resend Email API (Optional - for newsletter sending)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# AI Configuration (Optional - defaults provided)
AI_MODEL=claude-3-haiku-20240307
BATCH_SIZE=5

# Job Scheduling (Optional - defaults provided)
SCRAPE_INTERVAL_HOURS=3
PROCESS_INTERVAL_HOURS=4
NEWSLETTER_SEND_HOUR=7
```

3. **Verify .env is in .gitignore**:

```bash
# Check that .env won't be committed
grep -q ".env" .gitignore && echo "✓ .env is ignored" || echo "⚠ Add .env to .gitignore!"
```

### Option B: Using Docker Environment Variables

If you prefer, you can set environment variables directly in `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/news_db
      - ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
      - RESEND_API_KEY=re_your-key-here
```

**⚠️ Warning**: Never commit API keys directly in `docker-compose.yml` if you push to GitHub!

---

## 4. Verifying Your Setup

### Test API Keys

1. **Start your Docker containers**:

```bash
docker-compose up -d
```

2. **Check if Claude API is working**:

```bash
# Enter the backend container
docker exec -it pulse-backend-1 bash

# Run the AI analyzer test
cd /app
python -m app.services.ai_analyzer
```

Expected output:
```
Analyzing 5 articles...
  ✓ Analyzed: Article Title... (sentiment: 0.15, lean: CENTER)
Analyzed 5 articles
```

3. **Check admin stats endpoint**:

```bash
curl http://localhost:8000/admin/stats
```

Should return JSON with system statistics.

### Common Issues

#### "Claude API not configured"

**Problem**: The `ANTHROPIC_API_KEY` is not set or invalid.

**Solutions**:
- Check that `.env` file exists in `backend/` directory
- Verify the key starts with `sk-ant-api03-`
- Restart Docker containers: `docker-compose restart backend`
- Check logs: `docker logs pulse-backend-1`

#### "Rate limit exceeded"

**Problem**: You're making too many API requests.

**Solutions**:
- Claude Haiku has generous rate limits (50 requests/minute)
- Check if jobs are running too frequently
- Verify `max_instances=1` in scheduler to prevent duplicate jobs

#### "Invalid JSON response from Claude"

**Problem**: Claude occasionally returns non-JSON text.

**Solutions**:
- The code has retry logic built-in
- Check that prompts end with "Return ONLY the JSON array, no other text"
- Review logs for the actual response: `docker logs pulse-backend-1`

---

## 5. Testing Without API Keys

If you want to test the scraping/extraction pipeline without AI analysis:

1. **Comment out the analyze_job** in `backend/app/jobs/scheduler.py`:

```python
# scheduler.add_job(
#     analyze_job,
#     trigger=IntervalTrigger(hours=6),
#     id='analyze_articles',
#     max_instances=1
# )
```

2. **Use the admin endpoints** to manually trigger jobs:

```bash
# Scrape articles
curl -X POST http://localhost:8000/admin/jobs/scrape

# Extract content
curl -X POST http://localhost:8000/admin/jobs/extract

# Check stats
curl http://localhost:8000/admin/stats
```

This lets you verify the scraping and extraction pipeline works before adding API costs.

---

## 6. Cost Monitoring

### Track Your Usage

1. **Anthropic Console**:
   - Go to https://console.anthropic.com/settings/billing
   - View usage graphs and spending
   - Set up billing alerts

2. **Application Logs**:
   - The `ai_analyzer.py` service logs processing costs
   - Check Docker logs: `docker logs pulse-backend-1 | grep "processing_cost"`

3. **Database Tracking**:
   - `ArticleAnalysis.processing_cost` stores estimated cost per analysis
   - Query total costs:

```sql
SELECT SUM(processing_cost) as total_cost
FROM article_analyses;
```

### Setting Budget Alerts

In the Anthropic Console:
1. Go to Settings → Billing → Usage Limits
2. Set monthly limit (e.g., $10)
3. Add notification email
4. You'll get alerts at 50%, 75%, 90%, and 100% of limit

---

## 7. Security Best Practices

### Do NOT:
- ❌ Commit API keys to Git
- ❌ Share keys in screenshots or logs
- ❌ Use production keys in development
- ❌ Hard-code keys in source files

### DO:
- ✅ Use `.env` files for local development
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment variables in production
- ✅ Rotate keys if they're ever exposed
- ✅ Use separate keys for dev/staging/prod

### If You Accidentally Commit a Key:

1. **Immediately revoke it** in the provider's console
2. **Generate a new key**
3. **Remove from Git history**:

```bash
# Use git-filter-repo or BFG Repo-Cleaner
# Or simply delete the repo and start fresh if it's early in development
```

---

## 8. Quick Start Checklist

- [ ] Create Anthropic account and get API key
- [ ] (Optional) Create Resend account and get API key
- [ ] Create `backend/.env` file
- [ ] Add `ANTHROPIC_API_KEY` to `.env`
- [ ] Verify `.env` is in `.gitignore`
- [ ] Run `docker-compose up -d`
- [ ] Test with `curl http://localhost:8000/admin/stats`
- [ ] Trigger analysis job: `curl -X POST http://localhost:8000/admin/jobs/analyze`
- [ ] Check logs: `docker logs pulse-backend-1`
- [ ] Set up billing alerts in Anthropic Console

---

## Support

If you run into issues:

1. **Check the logs**: `docker logs pulse-backend-1 --tail 100`
2. **Verify environment**: `docker exec pulse-backend-1 env | grep API_KEY`
3. **Test Claude API directly**: Use their playground at https://console.anthropic.com/
4. **Review official docs**:
   - Anthropic: https://docs.anthropic.com/
   - Resend: https://resend.com/docs/

---

## Next Steps

Once your API keys are configured:

1. Run the full pipeline manually using admin endpoints
2. Monitor the automated jobs in the scheduler
3. Check system stats to see articles being processed
4. Move on to newsletter template development

See [NEXT_STEPS.md](NEXT_STEPS.md) for the full development roadmap.
