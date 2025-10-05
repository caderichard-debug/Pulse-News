#!/bin/bash
# Populate article features (analysis, frameworks, context, clustering)
# Run this script to process articles and make them visible in the feed

echo "🚀 Starting article processing pipeline..."
echo ""

# Trigger analysis jobs (processes 10 articles per run)
echo "📊 Step 1/4: Running AI analysis (3 batches)..."
for i in {1..3}; do
  curl -s -X POST http://localhost:8000/admin/jobs/analyze > /dev/null
  echo "  ✓ Analysis batch $i triggered"
  sleep 3
done

echo ""
echo "⚖️ Step 2/4: Generating ethical frameworks (3 batches)..."
for i in {1..3}; do
  curl -s -X POST http://localhost:8000/admin/jobs/frameworks > /dev/null
  echo "  ✓ Frameworks batch $i triggered"
  sleep 2
done

echo ""
echo "📚 Step 3/4: Generating article context (3 batches)..."
for i in {1..3}; do
  curl -s -X POST http://localhost:8000/admin/jobs/generate-context > /dev/null
  echo "  ✓ Context batch $i triggered"
  sleep 2
done

echo ""
echo "🔗 Step 4/4: Clustering similar articles..."
curl -s -X POST http://localhost:8000/admin/jobs/cluster-articles > /dev/null
echo "  ✓ Clustering triggered"

echo ""
echo "⏳ Waiting 20 seconds for jobs to complete..."
sleep 20

echo ""
echo "📈 Current stats:"
docker exec news_backend python -c "
from app.database import get_session
from app.models import Article, ArticleAnalysis, ArticleFrameworkLink, ArticleContext
from sqlmodel import select, func

session = next(get_session())

total_articles = session.exec(select(func.count(Article.id))).first()
with_analysis = session.exec(select(func.count()).select_from(
    select(Article).join(ArticleAnalysis).subquery()
)).first()
with_frameworks = session.exec(select(func.count()).select_from(
    select(Article).join(ArticleFrameworkLink).subquery()
)).first()
with_context = session.exec(select(func.count(ArticleContext.id))).first()

print(f'  Total articles: {total_articles}')
print(f'  With analysis: {with_analysis}')
print(f'  With frameworks: {with_frameworks}')
print(f'  With context: {with_context}')
print(f'  ')
print(f'  Feed will show: {with_analysis} articles')
" 2>&1 | grep -E "(Total|With|Feed)"

echo ""
echo "✅ Done! Refresh your browser to see the new articles."
echo "💡 Run this script again to process more articles."
