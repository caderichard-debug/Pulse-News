# Article Topic Backfill Script

## Purpose

This script re-analyzes existing articles to populate topic classifications that were added after articles were initially analyzed.

## When to Use

- **After deploying topic classification feature** - Run once to backfill all existing articles
- **After data corruption** - If topic data is lost or corrupted
- **Testing** - Use with `--max-articles` to test on a subset

## Usage

### Basic Usage (Process All Articles)

```bash
# Inside the backend container
docker-compose exec backend python scripts/backfill_article_topics.py

# Or from host with docker exec
docker exec -it news_backend python scripts/backfill_article_topics.py
```

### With Options

```bash
# Dry run to see what would happen (no changes)
docker-compose exec backend python scripts/backfill_article_topics.py --dry-run

# Process only 100 articles (for testing)
docker-compose exec backend python scripts/backfill_article_topics.py --max-articles 100

# Use larger batch size (default is 50)
docker-compose exec backend python scripts/backfill_article_topics.py --batch-size 100

# Combine options
docker-compose exec backend python scripts/backfill_article_topics.py --batch-size 25 --max-articles 50 --dry-run
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--batch-size` | 50 | Number of articles to process per batch |
| `--max-articles` | 0 (all) | Maximum total articles to process (0 = all) |
| `--dry-run` | False | Show what would be done without making changes |

## How It Works

1. **Identifies articles without topics** - Queries for analyzed articles where `topic_category IS NULL`
2. **Deletes analyses in batches** - Removes `ArticleAnalysis` records to trigger re-analysis
3. **Re-analyzes articles** - Calls the AI analyzer which now includes topic classification
4. **Populates both fields**:
   - `Article.topic_category` (string, for quick filtering)
   - `ArticleTopicLink` (many-to-many relationship)

## Performance Notes

- **API Rate Limits**: The script processes 5 articles per OpenAI API call (optimal batch size)
- **Pauses**: 1 second between sub-batches, 2 seconds between main batches
- **Time Estimate**: ~1-2 seconds per article (including API calls)
- **Cost**: ~$0.002 per article (using gpt-4o-mini)

### Example Runtime

- **100 articles**: ~3-5 minutes, ~$0.20
- **500 articles**: ~15-25 minutes, ~$1.00
- **Full backfill (600+ articles)**: ~20-30 minutes, ~$1.20-$1.30

## Production Deployment

### Option 1: Run Manually After Deploy (Recommended)

1. Deploy code changes
2. SSH into production server
3. Run backfill script:

```bash
docker-compose exec backend python scripts/backfill_article_topics.py --batch-size 50
```

### Option 2: Automated Post-Deploy Script

Add to your deployment pipeline after container starts:

```bash
# In your deploy script
docker-compose up -d --build
sleep 10  # Wait for services to start

# Run backfill
docker-compose exec -T backend python scripts/backfill_article_topics.py --max-articles 0 << EOF
EOF  # Auto-confirm by piping empty input
```

### Option 3: Gradual Backfill

Process in smaller batches over time to avoid API costs/rate limits:

```bash
# Day 1: First 200 articles
docker-compose exec backend python scripts/backfill_article_topics.py --max-articles 200

# Day 2: Next 200 articles
docker-compose exec backend python scripts/backfill_article_topics.py --max-articles 200

# Continue until all processed
```

## Safety Features

- **Confirmation prompt** - Asks for ENTER before proceeding (skip with input piping)
- **Dry run mode** - Test without making changes
- **Progress logging** - Shows detailed progress at each step
- **Batch processing** - Processes in chunks to avoid overwhelming the system
- **Error handling** - Continues processing even if individual batches fail

## Monitoring Progress

The script outputs:
- Total articles found without topics
- Batch progress (X/Y batches complete)
- Articles analyzed vs. processed per batch
- Final summary with success/failure counts

## Troubleshooting

### "No articles to process"
All articles already have topics assigned. Run with `--dry-run` to verify.

### OpenAI API Errors
- Check `OPENAI_API_KEY` in `.env`
- Verify API quota/rate limits
- Reduce `--batch-size` if hitting rate limits

### Database Errors
- Ensure database connection is stable
- Check migrations are up to date: `alembic current`

### Partial Completion
If the script is interrupted, simply re-run it. It will only process articles that still lack topics.

## Verification

After running, verify topics were populated:

```bash
# Check how many articles have topics
docker-compose exec backend python -c "
from app.database import get_session
from app.models import Article
from sqlmodel import select, func

with next(get_session()) as session:
    with_topics = session.exec(select(func.count(Article.id)).where(Article.topic_category.isnot(None))).one()
    without_topics = session.exec(select(func.count(Article.id)).where(Article.topic_category.is_(None))).one()
    print(f'Articles with topics: {with_topics}')
    print(f'Articles without topics: {without_topics}')
"

# Check topic distribution via API
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/feed/topics
```

## Related Files

- **Script**: `/backend/scripts/backfill_article_topics.py`
- **AI Analyzer**: `/backend/app/services/ai_analyzer.py`
- **OpenAI Client**: `/backend/app/utils/openai_client.py`
- **Models**: `/backend/app/models.py`
