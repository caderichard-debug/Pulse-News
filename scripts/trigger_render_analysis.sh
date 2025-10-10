#!/bin/bash
# Script to trigger analysis on Render deployment and monitor progress

BACKEND_URL="https://pulse-backend-4h7y.onrender.com"

echo "========================================="
echo "Pulse Render Analysis Trigger Script"
echo "========================================="
echo ""

# 1. Check system stats
echo "1. Checking system stats..."
STATS=$(curl -s "$BACKEND_URL/admin/stats")
TOTAL=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['articles']['total'])" 2>/dev/null || echo "Error")
COMPLETED=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['articles']['completed'])" 2>/dev/null || echo "Error")

echo "   Total articles: $TOTAL"
echo "   Completed articles: $COMPLETED"
echo ""

# 2. Check scheduler status
echo "2. Checking scheduler status..."
SCHEDULER=$(curl -s "$BACKEND_URL/admin/scheduler/status")
STATUS=$(echo "$SCHEDULER" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "Error")
echo "   Scheduler status: $STATUS"
echo ""

# 3. Check for analyzed articles
echo "3. Checking for analyzed articles..."
FEED=$(curl -s "$BACKEND_URL/feed/articles?page_size=3")
echo "$FEED" | python3 << 'EOF'
import sys, json
try:
    data = json.load(sys.stdin)
    total = data.get('total_count', 0)
    print(f"   Total in feed: {total}")

    articles = data.get('articles', [])
    if articles:
        print("\n   Sample articles:")
        for i, article in enumerate(articles[:3], 1):
            title = article.get('title', 'Unknown')[:50]
            has_summary = 'YES ✓' if article.get('summary') else 'NO ✗'
            has_sentiment = 'YES ✓' if article.get('sentiment_score') is not None else 'NO ✗'
            print(f"   {i}. {title}...")
            print(f"      Analysis: Summary={has_summary}, Sentiment={has_sentiment}")
    else:
        print("   No articles found")
except Exception as e:
    print(f"   Error parsing feed: {e}")
EOF
echo ""

# 4. Trigger analysis jobs
echo "4. Triggering analysis jobs..."
echo "   This will process up to 50 articles (5 batches × 10 articles)"
echo ""

for i in {1..5}; do
    echo "   Triggering batch $i..."
    RESULT=$(curl -s -X POST "$BACKEND_URL/admin/jobs/analyze")
    MESSAGE=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'Failed'))" 2>/dev/null || echo "Error")
    echo "   → $MESSAGE"

    if [ $i -lt 5 ]; then
        echo "   Waiting 10 seconds before next batch..."
        sleep 10
    fi
done

echo ""
echo "5. Waiting 2 minutes for analysis to complete..."
echo "   (Analysis processes articles in background)"
echo ""

for i in {1..24}; do
    echo -n "."
    sleep 5
done
echo ""
echo ""

# 6. Check results
echo "6. Checking results after analysis..."
FEED_AFTER=$(curl -s "$BACKEND_URL/feed/articles?page_size=5")
echo "$FEED_AFTER" | python3 << 'EOF'
import sys, json
try:
    data = json.load(sys.stdin)
    articles = data.get('articles', [])

    analyzed_count = sum(1 for a in articles if a.get('summary'))
    total_shown = len(articles)

    print(f"   Analyzed: {analyzed_count}/{total_shown} of shown articles")
    print("")

    if articles:
        print("   Article details:")
        for i, article in enumerate(articles[:5], 1):
            title = article.get('title', 'Unknown')[:50]
            summary = article.get('summary', '')
            sentiment = article.get('sentiment_score')
            lean = article.get('political_lean', 'None')

            print(f"\n   {i}. {title}...")
            if summary:
                print(f"      ✓ Summary: {summary[:60]}...")
                print(f"      ✓ Sentiment: {sentiment}, Lean: {lean}")
            else:
                print(f"      ✗ No analysis yet")
    else:
        print("   No articles found")

except Exception as e:
    print(f"   Error: {e}")
EOF

echo ""
echo "========================================="
echo "Script complete!"
echo ""
echo "If articles still show no analysis:"
echo "1. Check Render logs for errors"
echo "2. Verify OPENAI_API_KEY is set in Render environment"
echo "3. Check OpenAI account has quota remaining"
echo "4. Run this script again to process more articles"
echo "========================================="
