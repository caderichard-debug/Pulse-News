# Test User

The seed script (`app/seed_data.py`) automatically creates a test user for development and testing purposes.

## Default Credentials

- **Email**: `test@pulse.com`
- **Password**: `testpassword123`
- **Name**: Test User

## Customization

You can customize the test user by setting environment variables:

```bash
# .env or environment variables
TEST_USER_EMAIL=mytest@example.com
TEST_USER_PASSWORD=securepassword123
TEST_USER_NAME=My Test User
```

## Usage

### Local Development

Login via the frontend:
```
http://localhost:3000/login
Email: test@pulse.com
Password: testpassword123
```

### API Testing

Get an auth token:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@pulse.com","password":"testpassword123"}'
```

Use the token for authenticated endpoints:
```bash
TOKEN="eyJ..."
curl -X GET http://localhost:8000/preferences/topics \
  -H "Authorization: Bearer $TOKEN"
```

## Production Deployment

⚠️ **Security Warning**: For production deployments on Render or other platforms:

1. **Change the default credentials** via environment variables:
   ```
   TEST_USER_EMAIL=admin@yourdomain.com
   TEST_USER_PASSWORD=strong-random-password-here
   TEST_USER_NAME=Admin User
   ```

2. **Or delete the test user** after creating your production admin account:
   ```sql
   DELETE FROM users WHERE email = 'test@pulse.com';
   ```

3. **Restrict access** by using a non-obvious email address for the test account

## Features

The test user is automatically:
- ✅ Email verified (`email_verified: true`)
- ✅ Active (`is_active: true`)
- ✅ Subscribed to all default topics (politics, technology, science, etc.)
- ✅ Set up with default preferences (priority level 3, 5 articles per topic)

## When is the Test User Created?

1. **Docker startup**: The seed script runs on container start via `Dockerfile` CMD
2. **Manual seeding**: Run `python -m app.seed_data`
3. **Render deployment**: Automatically created on first backend startup

The test user creation is **idempotent** - it checks if the user exists before creating, so it's safe to run multiple times.

## Troubleshooting

### Test user not created

Check the logs:
```bash
# Docker logs
docker logs news_backend | grep "test user"

# Render logs
# Go to Render Dashboard > Backend Service > Logs
```

### Can't log in with test user

1. Verify the user exists in the database:
   ```bash
   docker-compose exec backend python3 -c "
   from app.database import get_session
   from app.models import User
   from sqlmodel import select

   with next(get_session()) as session:
       user = session.exec(select(User).where(User.email == 'test@pulse.com')).first()
       if user:
           print(f'User found: {user.email}')
           print(f'Verified: {user.email_verified}')
           print(f'Active: {user.is_active}')
       else:
           print('Test user not found')
   "
   ```

2. Check if custom credentials are set:
   ```bash
   echo $TEST_USER_EMAIL
   echo $TEST_USER_PASSWORD
   ```

3. Manually create the test user:
   ```bash
   docker-compose exec backend python3 -c "
   from app.seed_data import create_test_user
   from app.database import get_session

   with next(get_session()) as session:
       create_test_user(session)
   "
   ```

## Related Files

- [seed_data.py](app/seed_data.py) - Seed script with test user creation
- [auth.py](app/routes/auth.py) - Authentication routes
- [utils/auth.py](app/utils/auth.py) - Password hashing utilities
- [RENDER_DEPLOYMENT.md](../docs/RENDER_DEPLOYMENT.md) - Deployment guide with test user info
