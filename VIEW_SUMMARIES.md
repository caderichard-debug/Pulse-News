# How to View Article Summaries & Analysis

## Current Status

You have **39 extracted articles** waiting to be analyzed!

---

## Step 1: Set Up OpenAI API Key

If you haven't already:

```bash
# Add your OpenAI API key to backend/.env
echo "OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE" >> backend/.env

# Restart backend
docker-compose restart backend
```

---

## Step 2: Run AI Analysis

```bash
# Analyze 5-10 articles (takes ~30 seconds, costs ~$0.01)
curl -X POST http://localhost:8000/admin/jobs/analyze

# You'll see output like:
# {"success": true, "articles_analyzed": 10}
```

---

## Step 3: View Summaries

### Option A: View All Analyzed Articles
```bash
curl -s http://localhost:8000/articles/analyzed | python3 -m json.tool
```

### Option B: Pretty Print (Easier to Read)
```bash
curl -s http://localhost:8000/articles/analyzed | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'\n✨ Found {data[\"total\"]} analyzed articles\n')
print('=' * 80)
for i, article in enumerate(data['articles'], 1):
    print(f'\n📰 Article {i}: {article[\"title\"]}')
    print(f'   Source: {article[\"source\"][\"name\"]}')
    print(f'   Link: {article[\"url\"]}')
    print()
    print(f'   📝 SUMMARY:')
    print(f'   {article[\"analysis\"][\"summary\"]}')
    print()
    print(f'   📊 ANALYSIS:')
    print(f'      Sentiment: {article[\"analysis\"][\"sentiment_score\"]}/10')
    print(f'      Political Lean: {article[\"analysis\"][\"political_lean\"]}')
    print(f'      Bias: {article[\"analysis\"][\"bias_indicators\"]}')
    if article['analysis']['key_stats']:
        print(f'      Key Stats: {article[\"analysis\"][\"key_stats\"]}')
    print('=' * 80)
"
```

### Option C: View in Browser
1. Open: http://localhost:8000/docs
2. Find `/articles/analyzed` endpoint
3. Click "Try it out" → "Execute"
4. See formatted JSON with all summaries

### Option D: View Specific Article
```bash
# Replace {id} with article ID (e.g., 1, 2, 3...)
curl -s http://localhost:8000/articles/1 | python3 -m json.tool
```

---

## Step 4: Analyze More Articles

```bash
# Run multiple times to analyze more
curl -X POST http://localhost:8000/admin/jobs/analyze
curl -X POST http://localhost:8000/admin/jobs/analyze
curl -X POST http://localhost:8000/admin/jobs/analyze

# Each run analyzes 5-10 articles
# Check how many are analyzed:
curl -s http://localhost:8000/articles/analyzed | python3 -c "import json, sys; print(f'Analyzed: {json.load(sys.stdin)[\"total\"]}')"
```

---

## Quick Commands Reference

```bash
# Check system status
curl -s http://localhost:8000/admin/stats | python3 -m json.tool

# Trigger AI analysis
curl -X POST http://localhost:8000/admin/jobs/analyze

# View analyzed articles (short)
curl -s http://localhost:8000/articles/analyzed?limit=5

# View all analyzed articles (pretty)
curl -s http://localhost:8000/articles/analyzed | python3 -m json.tool

# Count analyzed articles
curl -s http://localhost:8000/articles/analyzed | python3 -c "import json, sys; print(json.load(sys.stdin)['total'])"
```

---

## Understanding the Analysis

Each article gets:

1. **Summary** (100 words) - Concise overview of main points
2. **Sentiment Score** (-10 to +10)
   - Negative: -10 to -1 (bad news)
   - Neutral: 0
   - Positive: +1 to +10 (good news)
3. **Political Lean** (LEFT / CENTER / RIGHT)
4. **Bias Indicators** - Description of detected bias or "neutral"
5. **Key Statistics** - Important numbers mentioned in article

---

## Troubleshooting

### "No analyzed articles found"
→ Run: `curl -X POST http://localhost:8000/admin/jobs/analyze`

### "OpenAI API not configured"
→ Add OPENAI_API_KEY to `backend/.env`

### "Rate limit exceeded"
→ Wait a minute, OpenAI has rate limits

### Check backend logs:
```bash
docker logs news_backend --follow
```

---

## Cost Estimate

- Each analysis batch (5-10 articles): ~$0.01
- 100 articles analyzed: ~$0.10-0.20
- Very affordable with GPT-4o-mini!

---

## Next Steps

After you have analyzed articles:
1. View them in the frontend (when built)
2. Map articles to ethical frameworks
3. Generate test newsletter
4. Set up automated daily analysis

Enjoy your AI-powered news summaries! 🎉
