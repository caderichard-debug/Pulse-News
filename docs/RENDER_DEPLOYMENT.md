# Render Deployment Guide

This guide walks you through deploying Pulse to Render using the included Blueprint (`render.yaml`).

## Overview

Pulse uses a Render Blueprint to manage the entire infrastructure:
- **PostgreSQL Database** (Free tier)
- **Backend API** (FastAPI with Docker) - Starter tier
- **Frontend** (Next.js) - Starter tier

The Blueprint automatically:
- Creates and configures all services
- Links the database to the backend
- Sets up environment variables
- Configures health checks
- Links frontend to backend API

---

## Prerequisites

1. **GitHub Repository**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at https://render.com
3. **API Keys**: Have these ready:
   - OpenAI API key (for AI features)
   - Resend API key (for newsletters)
   - Google Fact Check API key (optional)
   - Google Search Engine ID (optional)

---

## Step 1: Prepare Your Repository

1. Ensure your repository has the `render.yaml` file in the root
2. Commit and push all changes to your main branch:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

---

## Step 2: Deploy from Blueprint

### Option A: Deploy via Render Dashboard

1. Go to https://dashboard.render.com
2. Click **"New" → "Blueprint"**
3. Connect your GitHub repository
4. Select the repository containing Pulse
5. Render will automatically detect `render.yaml`
6. Click **"Apply"**

### Option B: Deploy via Direct Link

Use this format (replace with your GitHub URL):
```
https://dashboard.render.com/blueprints?repo=https://github.com/YOUR_USERNAME/Pulse-News
```

---

## Step 3: Configure Secret Environment Variables

After deployment starts, you need to add the secret environment variables manually:

### For `pulse-backend` service:

1. Go to your Render Dashboard
2. Click on the **pulse-backend** service
3. Go to **Environment** tab
4. Add the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key (generate a long random string) | `your-256-bit-secret-key-here` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |
| `RESEND_API_KEY` | Resend email API key | `re_...` |
| `GOOGLE_FACT_CHECK_API_KEY` | (Optional) Google Fact Check API | `AIza...` |
| `GOOGLE_SEARCH_ENGINE_ID` | (Optional) Google Custom Search ID | `012345...` |

5. Click **"Save Changes"**

**Note**: The Blueprint marks these as `sync: false` to prevent them from being stored in version control.

---

## Step 4: Run Database Migrations

Once the backend service is deployed and healthy:

1. Go to the **pulse-backend** service in Render Dashboard
2. Click **"Shell"** tab
3. Run the migration command:
   ```bash
   alembic upgrade head
   ```

This will create all the database tables and initial data.

---

## Step 5: Verify Deployment

### Check Service Health

1. **Backend**: Visit `https://pulse-backend.onrender.com/health`
   - Should return: `{"status": "healthy"}`

2. **Backend API Docs**: Visit `https://pulse-backend.onrender.com/docs`
   - Should show FastAPI Swagger UI

3. **Frontend**: Visit `https://pulse-frontend.onrender.com`
   - Should show the Pulse landing page

### Test Backend Connection

From the frontend, try to:
1. Register a new account
2. Log in
3. View the dashboard
4. Browse articles

---

## Step 6: (Optional) Trigger Initial Data Load

To populate the database with articles:

1. Get an authentication token:
   ```bash
   curl -X POST https://pulse-backend.onrender.com/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password"}'
   ```

2. Trigger article scraping (requires admin user):
   ```bash
   curl -X POST https://pulse-backend.onrender.com/admin/jobs/scrape \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. Trigger analysis:
   ```bash
   curl -X POST https://pulse-backend.onrender.com/admin/jobs/analyze \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

---

## Architecture Overview

```
┌─────────────────┐
│  pulse-frontend │  (Next.js)
│  onrender.com   │
└────────┬────────┘
         │ API calls via NEXT_PUBLIC_API_URL
         ▼
┌─────────────────┐
│  pulse-backend  │  (FastAPI)
│  onrender.com   │
└────────┬────────┘
         │ DATABASE_URL
         ▼
┌─────────────────┐
│    pulse-db     │  (PostgreSQL)
│   (internal)    │
└─────────────────┘
```

---

## Environment Variables Reference

### Backend Environment Variables

Auto-configured by Blueprint:
- `DATABASE_URL` - Postgres connection string (from pulse-db)
- `ENVIRONMENT` - Set to "production"
- `DEBUG` - Set to "false"
- `AI_MODEL` - Set to "gpt-4o-mini"
- `FROM_EMAIL` - Set to "onboarding@resend.dev"
- `FROM_NAME` - Set to "Pulse News"
- All other non-secret configuration values

Must be set manually (secrets):
- `SECRET_KEY` - JWT signing key
- `OPENAI_API_KEY` - OpenAI API access
- `RESEND_API_KEY` - Email sending
- `GOOGLE_FACT_CHECK_API_KEY` - (Optional) Fact checking
- `GOOGLE_SEARCH_ENGINE_ID` - (Optional) Web search

### Frontend Environment Variables

Auto-configured by Blueprint:
- `NODE_ENV` - Set to "production"
- `NEXT_PUBLIC_API_URL` - Auto-linked to pulse-backend URL

---

## Updating Your Deployment

### Automatic Deployments

By default, Render automatically deploys when you push to your `main` branch:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Render will:
1. Pull the latest code
2. Rebuild the services
3. Run health checks
4. Deploy if successful

### Manual Deployments

From the Render Dashboard:
1. Go to the service you want to redeploy
2. Click **"Manual Deploy" → "Deploy latest commit"**

---

## Monitoring & Logs

### View Logs

1. Go to your service in Render Dashboard
2. Click the **"Logs"** tab
3. View real-time logs

### Health Checks

- Backend health check: `/health` endpoint
- Render automatically monitors this endpoint
- If health check fails, Render will not route traffic to the instance

### Database Backups

Free tier databases do not include automatic backups. For production:
1. Upgrade to a paid database plan
2. Render will automatically create daily backups
3. Configure backup retention in database settings

---

## Troubleshooting

### Backend Won't Start

**Issue**: Backend service shows "Unhealthy" status

**Solution**:
1. Check logs for errors: `Logs` tab in Render Dashboard
2. Verify all secret environment variables are set
3. Check database connection:
   - Ensure `DATABASE_URL` is correctly linked
   - Verify database is healthy

### Frontend Can't Connect to Backend

**Issue**: Frontend shows API errors

**Solution**:
1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check CORS settings in backend:
   - Ensure frontend URL is allowed
   - May need to add frontend URL to `FRONTEND_URL` env var
3. Check backend health: Visit `/health` endpoint

### Database Migration Errors

**Issue**: Alembic migration fails

**Solution**:
1. Connect to the backend shell (Render Dashboard → Shell)
2. Check migration status:
   ```bash
   alembic current
   ```
3. View migration history:
   ```bash
   alembic history
   ```
4. If stuck, check which migration failed:
   ```bash
   alembic upgrade head --sql
   ```

### Scheduled Jobs Not Running

**Issue**: Articles not being scraped automatically

**Solution**:
1. Check APScheduler logs in backend logs
2. Verify jobs are registered: Check `/admin/scheduler/status`
3. Manually trigger jobs to test:
   ```bash
   curl -X POST https://pulse-backend.onrender.com/admin/jobs/scrape
   ```

---

## Scaling & Performance

### Free Tier Limitations

- **Backend/Frontend**: Services spin down after 15 minutes of inactivity
  - First request after spin-down will take ~30-60 seconds
  - Consider upgrading to paid plans to prevent spin-down

- **Database**: Free tier includes:
  - 256MB storage
  - Expires after 90 days (must upgrade or migrate)

### Upgrading Plans

To upgrade service plans:
1. Go to service in Render Dashboard
2. Click **"Settings"** tab
3. Change **"Instance Type"**
4. Save changes

Recommended for production:
- **Backend**: Starter ($7/month) or Standard ($25/month)
- **Frontend**: Starter ($7/month)
- **Database**: Starter ($7/month) with 1GB storage and backups

---

## Cost Estimate

### Free Tier (Development/Testing)
- Database: Free (256MB, 90 days)
- Backend: Free (spins down)
- Frontend: Free (spins down)
- **Total**: $0/month

### Starter Tier (Production)
- Database: Starter $7/month
- Backend: Starter $7/month
- Frontend: Starter $7/month
- **Total**: $21/month

---

## Security Best Practices

1. **Use Strong Secret Keys**
   - Generate `SECRET_KEY` with: `openssl rand -hex 32`
   - Never commit secrets to git

2. **Restrict CORS**
   - Update `FRONTEND_URL` env var with actual frontend domain
   - Remove wildcard `*` CORS in production

3. **Use Environment Variables**
   - All secrets should be in Render environment variables
   - Never hardcode API keys

4. **Enable HTTPS**
   - Render automatically provides HTTPS
   - Ensure all API calls use HTTPS

5. **Database Access**
   - Use Render's internal connection for backend
   - External connections: Use SSL/TLS
   - Restrict IP access if possible

---

## Support & Resources

- **Render Documentation**: https://render.com/docs
- **Render Status**: https://status.render.com
- **Pulse Documentation**: See [docs/](../docs/) folder
- **API Reference**: [API.md](./API.md)
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## Rollback Procedure

If a deployment fails:

1. **Via Dashboard**:
   - Go to service → Deploys tab
   - Find the last successful deploy
   - Click **"Rollback to this deploy"**

2. **Via Git**:
   ```bash
   git revert HEAD
   git push origin main
   ```

---

**Last Updated**: 2025-10-09
**Blueprint Version**: 1.0
**Maintained by**: Pulse Development Team
