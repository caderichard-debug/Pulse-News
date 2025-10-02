# 🚀 Quick Email Test Guide

## ✅ Configuration Already Done!

Your email is already configured to use `onboarding@resend.dev` (Resend's test domain).

**No domain verification needed!**

---

## Step 1: Get Your Resend API Key

1. Go to [resend.com/api-keys](https://resend.com/api-keys)
2. Create a new API key (or use existing)
3. Copy the key (starts with `re_`)

---

## Step 2: Add API Key to .env

```bash
# Edit backend/.env
echo "RESEND_API_KEY=re_your_actual_key_here" >> backend/.env
```

Or manually edit `backend/.env` and add:
```
RESEND_API_KEY=re_your_actual_key_here
```

---

## Step 3: Restart Containers

**Important**: Must use `down` then `up` to reload .env changes!

```bash
docker-compose down
docker-compose up -d
```

Wait a few seconds for containers to start.

---

## Step 4: Send Test Email

### Option A: Interactive Script (Easiest!)

```bash
./scripts/send_test_email.sh
```

This will:
1. Ask for your email/password
2. Login automatically
3. Send a test email

### Option B: Using API Docs (Visual)

1. Open [http://localhost:8000/docs](http://localhost:8000/docs)
2. Click **"Authorize"** button (top right)
3. Login first:
   - Go to **POST /auth/register** or **POST /auth/login**
   - Get your `access_token`
4. Click **"Authorize"** again
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
5. Go to **POST /test/send-email**
6. Click "Try it out"
7. Fill in:
   ```json
   {
     "to_email": "your@email.com",
     "subject": "Test Email from Pulse",
     "message": "Hello! 🎉"
   }
   ```
8. Click "Execute"

### Option C: Manual curl

```bash
# 1. Register/Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Send test email
curl -X POST http://localhost:8000/test/send-email \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Test from Pulse",
    "message": "Testing! 🚀"
  }'
```

---

## ✅ Success Response

You should see:
```json
{
  "success": true,
  "message": "Test email sent successfully to test@example.com",
  "from": "Pulse News <onboarding@resend.dev>",
  "to": "test@example.com"
}
```

Check your inbox! 📧

---

## 🐛 Troubleshooting

### Error: "Resend API key not configured"

**Solution**: Add `RESEND_API_KEY` to `backend/.env` and restart:
```bash
echo "RESEND_API_KEY=re_your_key" >> backend/.env
docker-compose down && docker-compose up -d
```

### Error: "domain is not verified"

**Solution**: You're still using old config. Verify:
```bash
docker exec news_backend printenv | grep FROM_EMAIL
```

Should show: `FROM_EMAIL=onboarding@resend.dev`

If not, check `backend/.env` and restart:
```bash
docker-compose down && docker-compose up -d
```

### Error: 403 Forbidden

**Solution**: Token expired or invalid. Login again to get a fresh token.

---

## 📊 Check Email Config

```bash
# Quick check
curl http://localhost:8000/test/email-config \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Should show:
```json
{
  "resend_configured": true,
  "from_email": "onboarding@resend.dev",
  "from_name": "Pulse News",
  "environment": "development"
}
```

---

## 🎯 Summary

1. ✅ Email configured with `onboarding@resend.dev`
2. ✅ No domain verification needed
3. ✅ Just add your Resend API key
4. ✅ Restart containers: `docker-compose down && docker-compose up -d`
5. ✅ Send test email!

**That's it!** Your email system is ready to use. 🚀
