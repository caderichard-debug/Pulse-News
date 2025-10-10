#!/bin/bash
# Script to run analysis on all articles by triggering the job multiple times

BACKEND_URL="${BACKEND_URL:-https://pulse-backend-4h7y.onrender.com}"

echo "🤖 Running full AI analysis on all articles..."
echo ""

# Run analyze job 10 times (10 articles per run = 100 articles)
for i in {1..10}; do
  echo "📊 Batch $i/10..."
  curl -s -X POST "$BACKEND_URL/admin/jobs/analyze" | python3 -m json.tool

  # Wait between batches to avoid rate limiting
  if [ $i -lt 10 ]; then
    echo "   Waiting 5 seconds before next batch..."
    sleep 5
  fi
done

echo ""
echo "✅ Analysis complete! Checking results..."
sleep 5

# Check how many articles now have analysis
curl -s "$BACKEND_URL/feed/articles?page=1&page_size=3" | python3 -m json.tool

echo ""
echo "📊 Check feed at: https://pulse-frontend-pfrt.onrender.com/feed"
