#!/bin/bash
# Quick script to send a test email from Pulse News Aggregator

set -e

echo "🎯 Pulse News - Test Email Sender"
echo "=================================="
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "❌ Error: Backend is not running!"
    echo "Start it with: docker-compose up -d"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Get user credentials
read -p "📧 Your email address: " USER_EMAIL
read -s -p "🔒 Your password: " USER_PASSWORD
echo ""
echo ""

# Login and get token
echo "🔐 Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}")

# Check if login was successful
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

    if [ -z "$TOKEN" ]; then
        echo "❌ Failed to extract token"
        echo "Response: $LOGIN_RESPONSE"
        exit 1
    fi

    echo "✅ Login successful!"
    echo ""
else
    echo "❌ Login failed!"
    echo "Response: $LOGIN_RESPONSE"
    echo ""
    echo "💡 Need an account? Register first:"
    echo "   curl -X POST http://localhost:8000/auth/register \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"email\":\"$USER_EMAIL\",\"password\":\"yourpassword\"}'"
    exit 1
fi

# Check email configuration
echo "🔍 Checking email configuration..."
CONFIG_RESPONSE=$(curl -s -X GET http://localhost:8000/test/email-config \
  -H "Authorization: Bearer $TOKEN")

echo "$CONFIG_RESPONSE" | python3 -c "
import sys, json
config = json.load(sys.stdin)
print(f\"  From: {config['from_name']} <{config['from_email']}>\" if config.get('from_email') else '  From: Not configured')
print(f\"  Resend API: {'✅ Configured' if config.get('resend_configured') else '❌ Not configured'}\" )
if not config.get('resend_configured'):
    print('')
    print('⚠️  Warning: Resend API key not configured!')
    print('   Set RESEND_API_KEY in api/.env')
    sys.exit(1)
" || exit 1

echo ""

# Get recipient email (default to sender)
read -p "📬 Send test email to [$USER_EMAIL]: " TO_EMAIL
TO_EMAIL=${TO_EMAIL:-$USER_EMAIL}

# Get custom message
read -p "💬 Custom message [Testing email system! 🎉]: " CUSTOM_MESSAGE
CUSTOM_MESSAGE=${CUSTOM_MESSAGE:-"Testing email system! 🎉"}

echo ""
echo "📤 Sending test email..."

# Send test email
SEND_RESPONSE=$(curl -s -X POST http://localhost:8000/test/send-email \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"to_email\":\"$TO_EMAIL\",
    \"subject\":\"Test Email from Pulse News\",
    \"message\":\"$CUSTOM_MESSAGE\"
  }")

# Check if successful
if echo "$SEND_RESPONSE" | grep -q '"success":true'; then
    echo ""
    echo "✅ Success! Email sent to $TO_EMAIL"
    echo ""
    echo "📧 Check your inbox for:"
    echo "   Subject: Test Email from Pulse News"
    echo "   From: $(echo $CONFIG_RESPONSE | python3 -c "import sys, json; c=json.load(sys.stdin); print(f\"{c['from_name']} <{c['from_email']}>\")" 2>/dev/null)"
    echo ""
    echo "💡 View delivery status at: https://resend.com/emails"
else
    echo ""
    echo "❌ Failed to send email"
    echo "Response: $SEND_RESPONSE"
    echo ""
    echo "Common issues:"
    echo "  1. FROM_EMAIL not verified in Resend"
    echo "  2. Invalid RESEND_API_KEY"
    echo "  3. Network connectivity issues"
    echo ""
    echo "Check backend logs: docker logs news_backend"
    exit 1
fi
