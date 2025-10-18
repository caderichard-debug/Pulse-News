# How to Test the Welcome Email

This guide shows you how to send a test welcome email using the new `/test/send-welcome` endpoint.

## Quick Test (via curl)

### Step 1: Get an Authentication Token

```bash
# Login to get a token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

### Step 2: Send Test Welcome Email

```bash
# Send welcome email to your own email address
curl -X POST http://localhost:8000/test/send-welcome \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your-email@example.com",
    "user_name": "John Doe"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Test welcome email sent successfully to your-email@example.com",
  "user_name": "John Doe",
  "sent_by": "test@example.com"
}
```

## Testing Different Scenarios

### Test with Different Names

```bash
# Test with a custom name
curl -X POST http://localhost:8000/test/send-welcome \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your-email@example.com",
    "user_name": "Jane Smith"
  }'
```

### Test with Email as Name (Fallback)

```bash
# Test using email as the name
curl -X POST http://localhost:8000/test/send-welcome \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your-email@example.com",
    "user_name": "your-email@example.com"
  }'
```

## Using the Interactive API Docs

1. **Navigate to Swagger UI**: http://localhost:8000/docs

2. **Authenticate**:
   - Click the **"Authorize"** button (🔒 icon in top right)
   - Use the `/auth/login` endpoint to get a token
   - Enter the token in the format: `Bearer YOUR_TOKEN_HERE`
   - Click **"Authorize"**

3. **Send Test Email**:
   - Find the **`POST /test/send-welcome`** endpoint under the "testing" section
   - Click **"Try it out"**
   - Fill in the request body:
     ```json
     {
       "to_email": "your-email@example.com",
       "user_name": "Test User"
     }
     ```
   - Click **"Execute"**

4. **Check Your Inbox**:
   - Look for an email with subject: **"Welcome to Pulse - Your AI-Powered News Companion"**
   - It should arrive within a few seconds (depending on your email provider)

## What to Look For

The welcome email should include:

✅ **Personalized Greeting**: "Hi {user_name},"

✅ **Key Features Section**: Overview of 4 main features:
- Sentiment & Bias Analysis
- Statistics Verification
- Ethical Framework Mapping
- Personalized Daily Digest

✅ **Quick Start Guide**: Actionable steps with links to:
- Preferences page
- Dashboard
- How It Works page

✅ **CTA Button**: "Go to Your Dashboard"

✅ **Pro Tip**: Highlight of clustered articles feature

✅ **Professional Design**: Responsive layout with gradient header

## Troubleshooting

### "Resend API key not configured"
- Make sure `RESEND_API_KEY` is set in your `backend/.env` file
- Restart the backend container: `docker-compose restart backend`

### "Failed to send welcome email"
- Check the backend logs: `docker logs news_backend --tail 50`
- Verify your Resend API key is valid
- Check your Resend dashboard for any sending limits or errors

### Email Not Received
- Check your spam/junk folder
- Verify the email address is correct
- Check Resend dashboard for delivery status: https://resend.com/emails
- Some email providers may take 1-2 minutes to deliver

### "Invalid or expired token"
- Get a fresh token using the login endpoint
- Make sure you're using `Bearer` prefix before the token

## Testing Email Configuration

Before sending test emails, verify your email configuration:

```bash
# Check email config
curl -X GET http://localhost:8000/test/email-config \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "resend_configured": true,
  "from_email": "onboarding@resend.dev",
  "from_name": "Pulse News",
  "environment": "development",
  "api_key_set": "Yes",
  "api_key_preview": "re_xxxxxx..."
}
```

## All Available Test Endpoints

| Endpoint | Purpose | Docs |
|----------|---------|------|
| `POST /test/send-email` | Send basic test email | [HOW_TO_SEND_TEST_EMAIL.md](HOW_TO_SEND_TEST_EMAIL.md) |
| `POST /test/send-newsletter` | Send test newsletter | [QUICK_EMAIL_TEST.md](QUICK_EMAIL_TEST.md) |
| `POST /test/send-welcome` | Send test welcome email | This guide |
| `GET /test/email-config` | Check email configuration | - |

## Example: Complete Testing Flow

```bash
#!/bin/bash

# 1. Login and get token
echo "Getting authentication token..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token. Check your credentials."
  exit 1
fi

echo "✅ Token obtained"

# 2. Check email configuration
echo -e "\nChecking email configuration..."
curl -s -X GET http://localhost:8000/test/email-config \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Send test welcome email
echo -e "\nSending test welcome email..."
RESPONSE=$(curl -s -X POST http://localhost:8000/test/send-welcome \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your-email@example.com",
    "user_name": "Test User"
  }')

echo "$RESPONSE" | jq

if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  echo -e "\n✅ Welcome email sent successfully! Check your inbox."
else
  echo -e "\n❌ Failed to send welcome email."
fi
```

Save this as `test_welcome_email.sh`, make it executable (`chmod +x test_welcome_email.sh`), and run it!

## Need Help?

- Check the backend logs: `docker logs news_backend -f`
- Review the email service code: [email_service.py](../backend/app/services/email_service.py)
- View the template: [welcome.html](../backend/app/templates/welcome.html)
- Run the tests: `docker-compose exec backend pytest tests/test_welcome_email.py -v`
