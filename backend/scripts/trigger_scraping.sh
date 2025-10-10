#!/bin/bash
# Script to trigger the article scraping pipeline on Render

# Set the backend URL (update this to your Render backend URL)
BACKEND_URL="${BACKEND_URL:-https://pulse-backend-4h7y.onrender.com}"

echo "🚀 Triggering article scraping pipeline on $BACKEND_URL"
echo ""

# Step 1: Scrape RSS feeds
echo "1️⃣  Triggering RSS scraping..."
curl -X POST "$BACKEND_URL/admin/jobs/scrape" -H "Content-Type: application/json"
echo ""
echo "   ✅ Scraping job triggered. Waiting 30 seconds for articles to be scraped..."
sleep 30

# Step 2: Extract article content
echo ""
echo "2️⃣  Triggering article extraction..."
curl -X POST "$BACKEND_URL/admin/jobs/extract" -H "Content-Type: application/json"
echo ""
echo "   ✅ Extraction job triggered. Waiting 60 seconds for content extraction..."
sleep 60

# Step 3: AI analysis
echo ""
echo "3️⃣  Triggering AI analysis..."
curl -X POST "$BACKEND_URL/admin/jobs/analyze" -H "Content-Type: application/json"
echo ""
echo "   ✅ Analysis job triggered. Waiting 90 seconds for AI processing..."
sleep 90

# Step 4: Framework mapping
echo ""
echo "4️⃣  Triggering framework mapping..."
curl -X POST "$BACKEND_URL/admin/jobs/frameworks" -H "Content-Type: application/json"
echo ""
echo "   ✅ Framework job triggered."

# Check stats
echo ""
echo "📊 Checking system stats..."
curl -s "$BACKEND_URL/admin/stats" | python3 -m json.tool
echo ""

echo ""
echo "✅ Pipeline complete! Check your feed at:"
echo "   https://pulse-frontend-pfrt.onrender.com/feed"
