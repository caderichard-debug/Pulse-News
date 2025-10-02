# How to Send a Test Email

This guide walks you through testing the email functionality of your Pulse News Aggregator.

---

## Prerequisites

1. **Resend API Key** - Get one from [resend.com/api-keys](https://resend.com/api-keys)
2. **✅ No Domain Verification Needed!** - We're using Resend's test domain `onboarding@resend.dev`
3. **User Account** - You need to be registered and logged in

---

## Step 1: Configure Resend API Key

### Option A: Edit `.env` file directly

```bash
# Edit the .env file
nano backend/.env
```

Add or update:
```bash
RESEND_API_KEY=re_your_actual_key_here
FROM_EMAIL=onboarding@resend.dev  # ✅ Already configured! (Resend's test domain)
FROM_NAME=Pulse News
```

**Note**: `FROM_EMAIL` is already set to `onboarding@resend.dev` - no verification needed!

### Option B: Use environment variable

```bash
# In backend/.env
echo "RESEND_API_KEY=re_your_actual_key_here" >> backend/.env
```

### Restart Backend

After updating the `.env` file:
```bash
docker-compose restart backend
```

---

## Step 2: Create a User Account (if you haven't already)

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "securepassword123"
  }'
```

**Save the `access_token` from the response!**

---

## Step 3: Check Email Configuration

```bash
curl -X GET http://localhost:8000/test/email-config \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected response:**
```json
{
  "resend_configured": true,
  "from_email": "noreply@yourdomain.com",
  "from_name": "Pulse News",
  "environment": "development",
  "api_key_set": "Yes",
  "api_key_preview": "re_abc123..."
}
```

---

## Step 4: Send Test Email

### Simple Test (to your own email)

```bash
curl -X POST http://localhost:8000/test/send-email \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "to_email": "your-email@example.com",
    "subject": "Test Email from Pulse News",
    "message": "This is a test! If you receive this, email is working! 🎉"
  }'
```

### Custom Test

```bash
curl -X POST http://localhost:8000/test/send-email \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "to_email": "recipient@example.com",
    "subject": "Custom Subject Here",
    "message": "Your custom message content here"
  }'
```

---

## Step 5: Verify Success

### Check the API Response

**Success response:**
```json
{
  "success": true,
  "message": "Test email sent successfully to your-email@example.com",
  "resend_response": {
    "id": "abc123-def456-ghi789"
  },
  "from": "Pulse News <noreply@yourdomain.com>",
  "to": "your-email@example.com"
}
```

### Check Your Email Inbox

Look for an email with:
- **Subject**: Your custom subject (default: "Test Email from Pulse News")
- **From**: Your configured `FROM_NAME` and `FROM_EMAIL`
- **Content**: A nicely formatted HTML email with your message

---

## Full Example: End-to-End Test

```bash
# 1. Register a new user
RESPONSE=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}')

# 2. Extract access token
TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. Check email configuration
curl -X GET http://localhost:8000/test/email-config \
  -H "Authorization: Bearer $TOKEN"

# 4. Send test email
curl -X POST http://localhost:8000/test/send-email \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Pulse Test Email",
    "message": "Testing the email system! 📧"
  }'
```

---

## Troubleshooting

### Error: "Resend API key not configured"

**Cause**: `RESEND_API_KEY` not set in `.env` file

**Fix**:
1. Add `RESEND_API_KEY=re_your_key` to `backend/.env`
2. Restart: `docker-compose restart backend`

---

### Error: "The email address you're trying to send from is not verified"

**Cause**: Your `FROM_EMAIL` is not verified in Resend

**Fix**:
1. Go to [resend.com/domains](https://resend.com/domains)
2. Verify your domain OR use a Resend test email
3. Update `FROM_EMAIL` in `.env`:
   ```bash
   FROM_EMAIL=onboarding@resend.dev  # For testing only
   ```

---

### Error: 403 Forbidden

**Cause**: Invalid or missing authentication token

**Fix**:
1. Make sure you're logged in
2. Check that your `Authorization: Bearer TOKEN` header is correct
3. Token may have expired - login again to get a fresh token

---

### Error: 500 Internal Server Error

**Cause**: Invalid Resend API key or network issue

**Fix**:
1. Check your API key is correct
2. Check Docker logs: `docker logs news_backend`
3. Verify network connectivity

---

## Using the API Documentation

Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) and:

1. Click **"Authorize"** button (🔓)
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click **"Authorize"**
4. Go to **"testing"** section
5. Try the endpoints with the interactive UI

---

## Testing Newsletter Functionality

Once basic email works, test the full newsletter:

```bash
# Generate and preview newsletter
curl -X GET http://localhost:8000/preferences/newsletter-preview \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Resend Dashboard

Monitor sent emails at [resend.com/emails](https://resend.com/emails):
- View delivery status
- Check bounce/spam reports
- See email content
- Monitor rate limits

---

## Environment Variables Reference

```bash
# Required for email
RESEND_API_KEY=re_your_key_here          # Get from resend.com
FROM_EMAIL=noreply@yourdomain.com        # Must be verified
FROM_NAME=Pulse News                      # Display name

# Optional email settings
NEWSLETTER_SEND_HOUR=7                    # Hour to send (0-23)
MAX_ARTICLES_PER_NEWSLETTER=5             # Articles per email
```

---

## Next Steps

1. ✅ Verify test email works
2. ✅ Set up preferences for your account
3. ✅ Test newsletter preview
4. ✅ Configure newsletter schedule
5. ✅ Monitor delivery in Resend dashboard

---

## Quick Reference

| Action | Endpoint | Method |
|--------|----------|--------|
| Check config | `/test/email-config` | GET |
| Send test email | `/test/send-email` | POST |
| Preview newsletter | `/preferences/newsletter-preview` | GET |
| API docs | `/docs` | GET |

**All endpoints require authentication except `/docs`**

---

## Need Help?

- **Resend Documentation**: [resend.com/docs](https://resend.com/docs)
- **API Documentation**: [localhost:8000/docs](http://localhost:8000/docs)
- **Backend Logs**: `docker logs news_backend -f`
