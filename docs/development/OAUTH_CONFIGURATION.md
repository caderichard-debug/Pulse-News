# OAuth Configuration Guide

## Overview
Pulse supports Google OAuth for user authentication. This guide explains how to configure OAuth for both development and production environments.

## Environment Variables

### Required Environment Variables
```bash
# OAuth Configuration (Google Sign-In)
GOOGLE_AUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_AUTH_CLIENT_SECRET=your-google-client-secret

# Application URLs
AUTH_URL=https://auth.pulsenews.app  # Production OAuth domain
BACKEND_URL=http://localhost:8000     # Development backend
ENVIRONMENT=development              # or "production"
```

## OAuth Flow Configuration

### Development Environment
- Callback URI: `http://localhost:8000/auth/oauth/google/callback`
- Frontend Redirect: `http://localhost:3000/login/callback`

### Production Environment
- Callback URI: `https://auth.pulsenews.app/auth/oauth/google/callback`
- Frontend Redirect: `https://pulsenews.app/login/callback`

## Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID credentials
3. Add authorized redirect URIs:
   - Development: `http://localhost:8000/auth/oauth/google/callback`
   - Production: `https://auth.pulsenews.app/auth/oauth/google/callback`

## Configuration Logic

The OAuth configuration automatically uses the correct callback URI based on the `ENVIRONMENT` setting:

```python
base_url = settings.auth_url if settings.environment == "production" else settings.backend_url
redirect_uri = f"{base_url}/auth/oauth/google/callback"
```

## Error Handling

The OAuth flow includes comprehensive error handling:
- `access_denied`: User cancelled OAuth → redirects back to login/signup with specific error message
- Other OAuth errors: Redirects back to origin page with generic error message
- State parameter ensures users return to the correct page (login vs signup)

## Testing OAuth Flow

### Development Testing
```bash
# Test OAuth initiation (should redirect to Google)
curl -i "http://localhost:8000/auth/oauth/google?origin=login"

# Test OAuth error callback
curl -i "http://localhost:8000/auth/oauth/google/callback?error=access_denied&state=login"
```

### Production Testing
```bash
# Test OAuth initiation (should redirect to Google)
curl -i "https://auth.pulsenews.app/auth/oauth/google?origin=login"

# Test OAuth error callback
curl -i "https://auth.pulsenews.app/auth/oauth/google/callback?error=access_denied&state=login"
```

## Frontend Integration

The frontend automatically passes the `origin` parameter when initiating OAuth:
- Login page: `?origin=login`
- Signup page: `?origin=signup`

This ensures users are redirected back to the appropriate page if they cancel the OAuth flow.