# Admin User Setup Guide

This guide explains how to grant admin privileges to users in different environments.

---

## Development (Local)

### Option 1: Using the Admin Setup Script

```bash
# From the project root
docker-compose exec backend python scripts/make_admin.py your-email@example.com
```

### Option 2: Direct Database Update

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d news_db

# Run SQL
UPDATE users SET is_admin = true WHERE email = 'your-email@example.com';
```

---

## Production

### Option 1: Using the Admin Setup Script (Recommended)

If you have SSH/exec access to your production container:

```bash
# SSH into your production server or use your platform's exec command
# For Railway, use the service shell in the dashboard

python scripts/make_admin.py your-email@example.com
```

### Option 2: Direct Database Update

**For Supabase Postgres:**

1. Go to your Supabase project dashboard
2. Open **Project Settings -> Database**
3. Copy the connection string for the role you use to run admin SQL
4. Use a SQL client to connect:

```bash
# Using psql locally
psql "postgresql://user:password@host:5432/database_name"

# Or use a GUI tool like:
# - TablePlus (Mac/Windows/Linux)
# - pgAdmin (Cross-platform)
# - DBeaver (Cross-platform)
```

5. Run the SQL command:

```sql
-- Find your user
SELECT id, email, name, is_admin FROM users WHERE email = 'your-email@example.com';

-- Grant admin privileges
UPDATE users SET is_admin = true WHERE email = 'your-email@example.com';

-- Verify
SELECT id, email, name, is_admin FROM users WHERE email = 'your-email@example.com';
```

### Option 3: Environment Variable Method (For First Admin)

You can create an environment variable in production that automatically grants admin on first login:

1. Add to your production environment variables:
   ```
   ADMIN_EMAILS=admin1@example.com,admin2@example.com
   ```

2. Update [backend/app/config.py](../backend/app/config.py) to include:
   ```python
   admin_emails: str = ""  # Comma-separated admin emails
   ```

3. Update the registration/login logic to check this list and auto-grant admin privileges

---

## Verifying Admin Access

After granting admin privileges, verify by:

1. **Login to your application**
2. **Navigate to** `/admin` in your browser
3. **You should see the admin dashboard** (if denied, admin privileges weren't applied)

Alternatively, check via API:

```bash
# Get auth token
TOKEN=$(curl -s -X POST https://your-domain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}' \
  | jq -r '.access_token')

# Check user info
curl -s -H "Authorization: Bearer $TOKEN" https://your-domain.com/auth/me | jq
```

You should see `"is_admin": true` in the response.

---

## Security Best Practices

1. **Limit admin users** - Only grant admin to trusted individuals
2. **Use strong passwords** - Admin accounts are high-value targets
3. **Enable 2FA** (when implemented) - Extra security for admin accounts
4. **Audit admin actions** - Review the `admin_audit_logs` table regularly
5. **Remove admin privileges** when no longer needed:
   ```sql
   UPDATE users SET is_admin = false WHERE email = 'former-admin@example.com';
   ```

---

## Troubleshooting

### "Admin access denied" after granting privileges

1. **Clear browser cache** and cookies
2. **Log out and log back in** - Token needs to be refreshed
3. **Verify database update** was committed:
   ```sql
   SELECT email, is_admin FROM users WHERE email = 'your-email@example.com';
   ```

### Script not found in production

Ensure the `scripts/` directory is included in your deployment:
- Check your `.dockerignore` doesn't exclude `scripts/`
- Verify scripts are copied in your Dockerfile

---

## Admin Panel Features

Once you have admin access, you can:

- 📊 **Dashboard** - View system stats and monitoring
- 👥 **User Management** - View, edit, and manage users
- 📰 **Source Management** - Add/edit/remove news sources
- 📄 **Article Management** - View and manage articles
- ⚙️ **Job Management** - Trigger and monitor background jobs
- 📋 **Audit Log** - Review all admin actions

Access the admin panel at: `https://your-domain.com/admin`

---

**Last Updated**: 2025-10-17
