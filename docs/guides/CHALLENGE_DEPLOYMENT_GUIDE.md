# Challenge System Deployment Guide

This guide provides comprehensive instructions for deploying and monitoring the newsletter challenge system in production.

## 🚀 Quick Deployment

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL database (handled by Docker Compose)
- Node.js for frontend (optional, can be deployed separately)
- SSL certificate for production HTTPS

### One-Command Deployment

```bash
# Navigate to project directory
cd /Users/caderichard/Projects/Pulse

# Run the deployment script
./scripts/deploy-challenge-system.sh
```

The script will:
- ✅ Backup current database state
- ✅ Pull latest changes and rebuild images
- ✅ Run database migrations
- ✅ Verify all challenge system tables
- ✅ Test API endpoints and functionality
- ✅ Verify newsletter integration
- ✅ Run performance and security checks
- ✅ Generate comprehensive deployment report

## 📊 System Monitoring

### Health Check Endpoints

#### Basic Health Check
```bash
curl http://localhost:8000/monitoring/health
```

#### Detailed Health Report
```bash
curl http://localhost:8000/monitoring/health/detailed
```

#### Active Alerts
```bash
curl http://localhost:8000/monitoring/alerts
```

#### Executive Summary
```bash
curl http://localhost:8000/monitoring/summary
```

### Monitoring Dashboard

Access the monitoring dashboard through the web interface:
- Navigate to `/monitoring` in the admin panel
- View real-time system health metrics
- Monitor participation trends and engagement rates
- Track error rates and system performance

## 🔧 Configuration

### Environment Variables

Ensure these environment variables are configured in `backend/.env`:

```bash
# Challenge System Configuration
CHALLENGE_GENERATION_ENABLED=true
CHALLENGE_SCHEDULE_ENABLED=true

# AI Configuration (for claim generation)
OPENAI_API_KEY=your-openai-api-key
AI_MODEL=gpt-4o-mini

# Email Configuration
RESEND_API_KEY=your-resend-api-key
FROM_EMAIL=newsletter@yourdomain.com
FROM_NAME=Pulse News

# Database Configuration
DATABASE_URL=postgresql://postgres:password@db:5432/news_db

# Monitoring Configuration
MONITORING_ENABLED=true
HEALTH_CHECK_ENABLED=true
ALERT_NOTIFICATIONS=true
```

### Scheduler Configuration

The challenge system uses APScheduler for background jobs. Key jobs:

1. **Weekly Challenge Generation** (Wednesday 2:00 PM PST)
2. **Daily Article Assignment** (6:00 AM PST)
3. **Analytics Processing** (Hourly)

### Job Monitoring

```bash
# Check active jobs
docker-compose exec backend python3 -c "
from app.jobs.scheduler import scheduler
print('Active jobs:')
for job in scheduler.get_jobs():
    print(f'  - {job.id}: {job.name}')
"

# Check job status
docker-compose exec backend python3 -c "
from app.jobs.scheduler import scheduler
jobs = scheduler.get_jobs()
for job in jobs:
    print(f'Job {job.id}:')
    print(f'  Name: {job.name}')
    print(f'  Next run: {job.next_run_time}')
    print(f'  Trigger: {job.trigger}')
"
```

## 📈 Performance Monitoring

### Key Metrics to Monitor

#### System Health
- **Overall Status**: healthy/warning/critical
- **Database Connectivity**: Connection status and response times
- **API Response Times**: Average response time for all endpoints
- **Error Rates**: Percentage of failed requests

#### Challenge System Metrics
- **Challenge Generation Success Rate**: % of successful weekly challenges
- **User Participation Rate**: % of active users engaging with challenges
- **Response Completion Rate**: % of users completing 7-day sequences
- **Article Assignment Success**: % of successful article assignments

#### Engagement Metrics
- **Justification Rate**: % of responses with detailed explanations
- **Article Read Rate**: % of assigned articles actually read
- **Perspective Diversity Score**: Variety of political viewpoints consumed

### Performance Benchmarks

| Metric | Target | Warning | Critical |
|--------|--------|---------|
| API Response Time | <2s | 2-5s | >5s |
| Error Rate | <1% | 1-5% | >5% |
| Challenge Generation Success | >95% | 80-95% | <80% |
| User Participation Rate | >60% | 40-60% | <40% |
| Assignment Completion Rate | >85% | 70-85% | <70% |

## 🔔 Security Monitoring

### Security Checks

The deployment script includes automated security checks:

1. **Authentication Validation**: All sensitive endpoints require authentication
2. **Authorization Verification**: Admin endpoints restricted to admin users
3. **Input Validation**: Protection against SQL injection and XSS attacks
4. **Rate Limiting**: Protection against brute force attacks

### SSL/TLS Configuration

For production deployment:

```bash
# Generate SSL certificate
./scripts/setup-ssl.sh

# Configure HTTPS
# Update nginx or reverse proxy configuration
```

### Security Headers

The application includes security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

## 📱 Logging and Alerting

### Log Locations

- **Application Logs**: `docker-compose logs -f news_backend`
- **Database Logs**: Available through PostgreSQL logs
- **Scheduler Logs**: Included in application logs
- **Error Logs**: Automatically captured and logged

### Log Levels

```bash
# Configure log levels in backend/.env
LOG_LEVEL=INFO
CHALLENGE_LOG_LEVEL=DEBUG
```

### Alert Configuration

Set up alerts for critical conditions:

1. **System Down**: API health check failures
2. **High Error Rates**: Error rate > 5%
3. **Performance Issues**: Response time > 5 seconds
4. **Data Quality Issues**: Orphaned records detected

## 🔄 Maintenance Tasks

### Regular Maintenance

#### Weekly Tasks
- Review system health reports
- Check for orphaned records
- Monitor challenge generation success
- Review user participation trends

#### Monthly Tasks
- Database optimization and cleanup
- Review and update challenge claim quality
- Analyze engagement patterns
- Update security patches

#### Quarterly Tasks
- Performance optimization review
- Capacity planning and scaling
- Security audit and penetration testing
- User feedback analysis and improvements

### Automated Cleanup

```bash
# Run cleanup operations (dry run first)
curl -X POST "http://localhost:8000/monitoring/admin/cleanup?dry_run=true" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Run actual cleanup
curl -X POST "http://localhost:8000/monitoring/admin/cleanup" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 📊 Analytics and Reporting

### Executive Dashboard

Access comprehensive analytics through the monitoring dashboard:

1. **User Participation Trends**: Weekly and monthly participation rates
2. **Engagement Quality Metrics**: Response quality and article completion rates
3. **System Performance**: Response times, error rates, capacity utilization
4. **Content Quality**: Claim diversity, article matching effectiveness

### Data Export

```bash
# Export participation data
curl -X GET "http://localhost:8000/monitoring/participation?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/json"

# Export quality metrics
curl -X GET "http://localhost:8000/monitoring/quality" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/json"
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database container
docker ps | grep news_db

# Check database logs
docker logs news_db

# Test database connection
docker-compose exec postgres psql -U postgres news_db -c "SELECT 1;"
```

#### API Response Issues
```bash
# Check backend container
docker ps | grep news_backend

# Check backend logs
docker logs news_backend -f

# Test API connectivity
curl -v http://localhost:8000/monitoring/health
```

#### Scheduler Issues
```bash
# Check scheduler status
docker-compose exec backend python3 -c "
from app.jobs.scheduler import scheduler
print('Scheduler status:', scheduler.state)
"

# Restart scheduler
docker-compose restart backend
```

#### Frontend Issues
```bash
# Check frontend logs
cd frontend && npm run build

# Test frontend connectivity
curl -I http://localhost:3000
```

### Recovery Procedures

#### System Recovery
```bash
# Full system recovery
./scripts/deploy-challenge-system.sh

# Database recovery from backup
docker-compose exec postgres psql -U postgres news_db < /path/to/backup.sql

# Service restart
docker-compose restart
```

#### Data Recovery
```bash
# Identify orphaned records
curl -X GET "http://localhost:8000/monitoring/quality" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Run cleanup operations
curl -X POST "http://localhost:8000/monitoring/admin/cleanup" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 📚 Monitoring API Reference

### Health Check Endpoints

| Endpoint | Method | Description | Requires Auth |
|---------|--------|-------------|-------------|
| `/monitoring/health` | GET | Basic health check | No |
| `/monitoring/health/detailed` | GET | Comprehensive health report | No |
| `/monitoring/alerts` | GET | Active system alerts | No |
| `/monitoring/performance` | GET | Performance metrics | No |
| `/monitoring/summary` | GET | Executive summary | No |

### Participation Metrics

| Endpoint | Method | Description | Parameters |
|---------|--------|-------------|-----------|
| `/monitoring/participation` | GET | Participation metrics | `days` (1-365) |

### Quality Metrics

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/monitoring/quality` | GET | Data quality metrics |

### Admin Endpoints

| Endpoint | Method | Description | Requires Admin |
|---------|--------|-------------|--------------|
| `/monitoring/admin/system` | GET | System information | Yes |
| `/monitoring/admin/cleanup` | POST | Cleanup operations | Yes |

## 🎯 Success Metrics

### Performance Goals
- **99%+ uptime** for challenge system
- **Sub-second response times** for challenge form
- **<1% error rate** for all API endpoints
- **99%+ success rate** for challenge generation

### Engagement Goals
- **60%+** of newsletter users engage with challenges
- **40%+** complete full 7-day challenge sequences
- **1.5x** higher engagement for challenge articles vs regular articles

### Quality Goals
- **Balanced political perspective distribution** in assigned articles
- **High-quality claim generation** (controversy score 0.3-0.8)
- **Effective article matching** (opposition score 0.6+)
- **Positive user feedback** on challenge value

---

## 📞 Support

For deployment issues or questions:

1. **Check logs**: `docker-compose logs -f news_backend`
2. **Health check**: `curl http://localhost:8000/monitoring/health`
3. **Review alerts**: `curl http://localhost:8000/monitoring/alerts`
4. **System status**: `curl http://localhost:8000/monitoring/summary`

## 📝 Documentation Updates

This guide should be updated when:
- New monitoring endpoints are added
- Performance benchmarks change
- Security requirements evolve
- New alert conditions are implemented