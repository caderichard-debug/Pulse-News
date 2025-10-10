# Pull Request Previews on Render

This guide explains how PR previews work for the Pulse project on Render.

## What are PR Previews?

Pull Request Previews automatically create temporary deployment environments for each pull request. This allows you to:

- **Test changes** before merging to main
- **Share preview links** with team members or reviewers
- **Verify features** work in a production-like environment
- **Catch deployment issues** early

## Configuration

PR previews are enabled in [render.yaml](../render.yaml) with these settings:

```yaml
services:
  - type: web
    name: pulse-backend
    previewsEnabled: true
    previewsExpireAfterDays: 3
    # ... rest of config

  - type: web
    name: pulse-frontend
    previewsEnabled: true
    previewsExpireAfterDays: 3
    # ... rest of config
```

## How It Works

### Automatic Deployment

1. **Create a Pull Request**: When you create a PR against the `main` branch, Render automatically:
   - Detects the new PR via GitHub webhook
   - Creates preview instances for both backend and frontend
   - Deploys the code from your PR branch
   - Provides unique URLs for each preview

2. **Update the PR**: Each time you push new commits to the PR:
   - Render automatically rebuilds the preview
   - Preview URLs remain the same
   - You can see the latest changes immediately

3. **Close/Merge the PR**: When the PR is closed or merged:
   - Preview environments are automatically deleted after 3 days
   - No manual cleanup needed

### Preview URLs

Render generates unique URLs for each preview:

- **Backend**: `https://pulse-backend-pr-{PR_NUMBER}.onrender.com`
- **Frontend**: `https://pulse-frontend-pr-{PR_NUMBER}.onrender.com`

Example for PR #42:
- Backend: `https://pulse-backend-pr-42.onrender.com`
- Frontend: `https://pulse-frontend-pr-42.onrender.com`

## Environment Variables

### Preview-Specific Variables

The `IS_PULL_REQUEST` environment variable is automatically set to `true` for preview environments:

```yaml
- key: IS_PULL_REQUEST
  isPreview: true
```

You can use this in your code to adjust behavior for previews:

```python
import os

if os.getenv("IS_PULL_REQUEST") == "true":
    # Preview-specific configuration
    print("Running in PR preview mode")
```

### Shared Database

⚠️ **Important**: Preview environments share the **same production database** (`pulse-db`). This means:

- Data changes in previews affect production data
- Consider adding preview-specific database logic if needed
- Be cautious when testing data modifications

**Recommendation**: For safer testing, you can:
1. Create a separate preview database in Render
2. Update the `DATABASE_URL` to use a preview-specific database
3. Seed the preview database with test data

### Secret Environment Variables

Preview environments inherit secret environment variables from the production service:

- `SECRET_KEY` (JWT secret)
- `OPENAI_API_KEY`
- `RESEND_API_KEY`
- Other secrets from Render's Secret File

These are automatically available in preview environments - no additional configuration needed.

## Accessing Preview Environments

### Via GitHub

1. Go to your Pull Request on GitHub
2. Scroll to the bottom of the PR
3. Look for the **"View deployment"** button from Render
4. Click to open the preview environment

### Via Render Dashboard

1. Go to https://dashboard.render.com
2. Navigate to your service (pulse-backend or pulse-frontend)
3. Click the **"Preview Environments"** tab
4. See all active previews and their URLs

## Testing a Preview

### Frontend Testing

1. Open the preview frontend URL
2. Test the feature you're working on
3. Verify UI changes, navigation, etc.

### Backend Testing

1. Test API endpoints using the preview backend URL:
   ```bash
   # Example: Login to preview backend
   curl -X POST https://pulse-backend-pr-42.onrender.com/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@pulse.com","password":"testpassword123"}'
   ```

2. View API docs:
   ```
   https://pulse-backend-pr-42.onrender.com/docs
   ```

### Health Check

Verify the preview is healthy:
```bash
curl https://pulse-backend-pr-42.onrender.com/health
# Expected: {"status": "healthy"}
```

## Preview Limitations

### Free Tier Constraints

- **Spin-down**: Preview environments on the free tier will spin down after 15 minutes of inactivity
- **First request**: May take 30-60 seconds to wake up
- **Build time**: Initial deploy can take 5-10 minutes

### Resource Limits

- **Database**: Shared with production (or separate free tier database)
- **CPU/Memory**: Same as the service plan (free/starter)
- **Expiration**: Previews are deleted 3 days after PR is closed/merged

## Customizing Preview Behavior

### Adjust Expiration Time

Change how long previews remain after PR closure:

```yaml
previewsEnabled: true
previewsExpireAfterDays: 7  # Keep for 7 days instead of 3
```

### Disable Previews for a Service

To disable previews for a specific service:

```yaml
previewsEnabled: false
```

### Preview-Specific Configuration

Add environment variables only for previews:

```yaml
envVars:
  - key: ENABLE_DEBUG_MODE
    isPreview: true
    value: "true"
```

## Best Practices

### 1. Test Before Merging

Always check the preview environment before merging:
- ✅ Run through your feature manually
- ✅ Verify no errors in logs
- ✅ Test edge cases
- ✅ Check responsive design (for frontend)

### 2. Share Preview Links

Include the preview URL in your PR description:
```markdown
## Testing

Preview environment: https://pulse-frontend-pr-42.onrender.com

### Test Steps
1. Navigate to /dashboard
2. Click on article
3. Verify analytics display correctly
```

### 3. Monitor Build Logs

If a preview fails to deploy:
1. Check the build logs in Render dashboard
2. Fix any deployment errors
3. Push a new commit to rebuild

### 4. Clean Up Old PRs

Render automatically cleans up previews, but you can:
- Close stale PRs to trigger cleanup
- Manually delete previews from Render dashboard if needed

## Troubleshooting

### Preview Not Created

**Issue**: PR was opened but no preview environment appeared

**Solutions**:
1. Check if `previewsEnabled: true` is in render.yaml
2. Verify GitHub webhook is connected in Render dashboard
3. Check if PR is against the correct branch (`main`)

### Preview Shows Old Code

**Issue**: Preview still shows old code after pushing new commits

**Solutions**:
1. Wait 2-3 minutes for rebuild to complete
2. Check deploy logs in Render dashboard
3. Manually trigger redeploy if needed

### Frontend Can't Connect to Backend

**Issue**: Frontend preview shows API errors

**Solutions**:
1. Verify both backend and frontend previews are deployed
2. Check if backend preview is healthy: `/health` endpoint
3. Ensure CORS settings allow preview frontend URL
4. Check if `NEXT_PUBLIC_API_URL` is correct in frontend preview

### Database Connection Errors

**Issue**: Backend preview can't connect to database

**Solutions**:
1. Verify `DATABASE_URL` is configured correctly
2. Check database is healthy in Render dashboard
3. Ensure database accepts connections from preview environments

## Cost Considerations

### Free Tier

- **Preview environments**: Free (up to 90 hours/month total across all services)
- **Shared limits**: Previews count toward your total service hours
- **Spin-down**: Inactive previews spin down to save resources

### Paid Plans

If you upgrade to paid plans:
- **No spin-down**: Previews stay active
- **Faster builds**: Better build performance
- **More previews**: Can run more concurrent previews

## Example Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/new-dashboard-widget
# Make your changes
git add .
git commit -m "Add new dashboard widget"
git push origin feature/new-dashboard-widget
```

### 2. Open Pull Request

Create PR on GitHub targeting `main` branch.

### 3. Wait for Preview

Render automatically:
- Detects the PR
- Creates preview environments
- Posts deployment status to GitHub

### 4. Test the Preview

Visit the preview URL and verify your changes work.

### 5. Iterate

Make changes, push commits, and Render will automatically rebuild the preview.

### 6. Merge

Once approved and tested, merge the PR. Render will:
- Deploy to production
- Delete preview environments after 3 days

## Additional Resources

- **Render Docs**: https://render.com/docs/preview-environments
- **GitHub Integration**: https://render.com/docs/github
- **Blueprint Spec**: https://render.com/docs/blueprint-spec

---

**Last Updated**: 2025-10-10
**Status**: PR Previews Enabled ✅
