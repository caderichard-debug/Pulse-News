# Backend Scripts

This directory contains utility scripts for maintenance and operations.

## Available Scripts

### backfill_article_topics.py

Re-analyzes existing articles to populate topic classifications.

**Quick Start:**
```bash
# See what would be done (dry run)
docker-compose exec backend python scripts/backfill_article_topics.py --dry-run

# Process all articles
docker-compose exec backend python scripts/backfill_article_topics.py

# Process first 100 articles only
docker-compose exec backend python scripts/backfill_article_topics.py --max-articles 100
```

**Full Documentation:** See [README_BACKFILL.md](README_BACKFILL.md)

## Adding New Scripts

When creating new scripts:

1. Add shebang: `#!/usr/bin/env python3`
2. Include docstring with usage examples
3. Make executable: `chmod +x script_name.py`
4. Add to this README with description
5. Include error handling and logging
6. Test in container environment
