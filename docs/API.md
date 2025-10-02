# API Documentation

Base URL: `http://localhost:8000`

Interactive docs: http://localhost:8000/docs

## Authentication

Most endpoints require JWT authentication. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

Get a token by logging in via `/auth/login`.

---

## Public Endpoints

### Health Check

```http
GET /health
```

Returns server health status.

**Response:**
```json
{
  "status": "ok"
}
```

---

### User Registration

```http
POST /auth/signup
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2025-10-02T10:30:00Z"
}
```

---

### User Login

```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

---

### List Articles

```http
GET /articles
```

**Query Parameters:**
- `skip` (int, optional) - Pagination offset (default: 0)
- `limit` (int, optional) - Number of results (default: 20, max: 100)
- `topic` (string, optional) - Filter by topic name
- `source` (string, optional) - Filter by source name

**Response:**
```json
{
  "total": 150,
  "articles": [
    {
      "id": 1,
      "title": "Breaking News Article",
      "url": "https://example.com/article",
      "source": {
        "name": "Reuters",
        "trust_score": 9.5
      },
      "published_at": "2025-10-02T08:00:00Z",
      "analysis": {
        "summary": "Brief 100-word summary...",
        "sentiment_score": 0.2,
        "political_lean": "center",
        "key_stats": ["50% increase", "2025 deadline"]
      },
      "frameworks": [
        {
          "name": "Individual Liberty vs. Collective Welfare",
          "position": 6,
          "explanation": "Article emphasizes collective benefit..."
        }
      ]
    }
  ]
}
```

---

### Get Article Details

```http
GET /articles/{article_id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Breaking News Article",
  "url": "https://example.com/article",
  "author": "Jane Reporter",
  "published_at": "2025-10-02T08:00:00Z",
  "content_text": "Full article content...",
  "word_count": 1250,
  "source": {
    "name": "Reuters",
    "description": "International news agency",
    "trust_score": 9.5
  },
  "analysis": {
    "summary": "100-word summary...",
    "sentiment_score": 0.2,
    "political_lean": "center",
    "bias_indicators": ["loaded language: minimal"],
    "key_stats": ["50% increase in Q3", "2025 deadline"]
  },
  "frameworks": [
    {
      "id": 3,
      "name": "Individual Liberty vs. Collective Welfare",
      "description": "Debate between personal freedom and community benefit",
      "position": 6,
      "relevance_score": 0.85,
      "explanation": "Article emphasizes collective welfare..."
    }
  ]
}
```

---

### List Frameworks

```http
GET /frameworks
```

**Response:**
```json
{
  "frameworks": [
    {
      "id": 1,
      "name": "Individual Liberty vs. Collective Welfare",
      "description": "Core tension between personal freedom and community benefit",
      "axis_description": "Left: Personal freedom | Right: Community welfare",
      "left_position": "Individual rights priority",
      "right_position": "Social responsibility priority",
      "article_count": 45,
      "last_active": "2025-10-02T08:00:00Z"
    }
  ]
}
```

---

## Protected Endpoints

### Get Current User

```http
GET /auth/me
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "email_verified": true,
  "subscription_tier": "free",
  "created_at": "2025-09-01T10:00:00Z"
}
```

---

### Get User Preferences

```http
GET /preferences
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "topics": [
    {
      "id": 1,
      "name": "Politics",
      "description": "Political news and analysis",
      "include_in_newsletter": true,
      "priority_level": 1
    },
    {
      "id": 2,
      "name": "Technology",
      "description": "Tech industry news",
      "include_in_newsletter": true,
      "priority_level": 2
    },
    {
      "id": 3,
      "name": "Culture",
      "description": "Arts and culture",
      "include_in_newsletter": false,
      "priority_level": null
    }
  ]
}
```

---

### Update User Preferences

```http
PUT /preferences
```

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "topic_preferences": [
    {
      "topic_id": 1,
      "include_in_newsletter": true,
      "priority_level": 1
    },
    {
      "topic_id": 2,
      "include_in_newsletter": true,
      "priority_level": 2
    },
    {
      "topic_id": 3,
      "include_in_newsletter": false
    }
  ]
}
```

**Response:**
```json
{
  "message": "Preferences updated successfully",
  "updated_count": 3
}
```

---

### Get Latest Newsletter

```http
GET /newsletters/latest
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 42,
  "subject": "Your Daily Pulse - Oct 2, 2025",
  "sent_at": "2025-10-02T07:00:00Z",
  "article_count": 5,
  "framework_count": 3,
  "email_opened": true,
  "links_clicked": 2
}
```

---

### Get Newsletter History

```http
GET /newsletters/history
```

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `skip` (int, optional) - Pagination offset
- `limit` (int, optional) - Number of results (max: 50)

**Response:**
```json
{
  "newsletters": [
    {
      "id": 42,
      "subject": "Your Daily Pulse - Oct 2, 2025",
      "sent_at": "2025-10-02T07:00:00Z",
      "article_count": 5,
      "email_opened": true
    },
    {
      "id": 41,
      "subject": "Your Daily Pulse - Oct 1, 2025",
      "sent_at": "2025-10-01T07:00:00Z",
      "article_count": 5,
      "email_opened": false
    }
  ]
}
```

---

## Admin Endpoints

Require admin role in JWT token.

### Get System Statistics

```http
GET /admin/stats
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "articles": {
    "total": 1250,
    "pending": 45,
    "completed": 1205,
    "failed": 0
  },
  "sources": {
    "total": 8,
    "active": 8
  },
  "frameworks": {
    "total": 15,
    "seed": 10,
    "discovered": 5
  },
  "users": {
    "total": 120,
    "active": 95,
    "verified": 110
  },
  "newsletters": {
    "sent_today": 95,
    "open_rate": 0.42,
    "click_rate": 0.18
  }
}
```

---

### Trigger Manual Scrape

```http
POST /admin/scrape
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "Scrape job started",
  "sources_processed": 8,
  "articles_found": 23,
  "duration_seconds": 12.5
}
```

---

### Trigger Article Extraction

```http
POST /admin/extract
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "Extraction job started",
  "articles_processed": 23,
  "successful": 21,
  "failed": 2,
  "duration_seconds": 45.2
}
```

---

### Trigger AI Analysis

```http
POST /admin/analyze
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "Analysis job started",
  "articles_analyzed": 21,
  "batches_processed": 5,
  "cost_usd": 0.042,
  "duration_seconds": 18.7
}
```

---

### Trigger Framework Generation

```http
POST /admin/frameworks
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "Framework generation completed",
  "articles_mapped": 21,
  "new_frameworks_discovered": 1,
  "duration_seconds": 8.3
}
```

---

### Get Recent Articles

```http
GET /admin/articles/recent
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `limit` (int, optional) - Number of results (default: 50, max: 200)
- `status` (string, optional) - Filter by processing status

**Response:**
```json
{
  "articles": [
    {
      "id": 1250,
      "title": "Latest Article",
      "source": "Reuters",
      "published_at": "2025-10-02T10:00:00Z",
      "processing_status": "completed",
      "extraction_method": "trafilatura",
      "word_count": 850
    }
  ]
}
```

---

### Get Sources Status

```http
GET /admin/sources
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "sources": [
    {
      "id": 1,
      "name": "Reuters",
      "rss_feed_url": "https://reuters.com/feed",
      "is_active": true,
      "trust_score": 9.5,
      "article_count": 342,
      "last_scraped": "2025-10-02T09:00:00Z",
      "last_scrape_article_count": 5
    }
  ]
}
```

---

### Get Scheduler Status

```http
GET /admin/scheduler/status
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "scheduler_running": true,
  "jobs": [
    {
      "id": "scrape_rss",
      "name": "Scrape RSS Feeds",
      "next_run": "2025-10-02T12:00:00Z",
      "last_run": "2025-10-02T09:00:00Z",
      "status": "success"
    },
    {
      "id": "extract_articles",
      "name": "Extract Article Content",
      "next_run": "2025-10-02T13:00:00Z",
      "last_run": "2025-10-02T09:30:00Z",
      "status": "success"
    }
  ]
}
```

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- **Public endpoints**: 100 requests/minute per IP
- **Authenticated endpoints**: 1000 requests/minute per user
- **Admin endpoints**: No limit

Exceeding limits returns `429 Too Many Requests`.

---

## Pagination

List endpoints support pagination:

```http
GET /articles?skip=20&limit=20
```

Response includes total count:
```json
{
  "total": 150,
  "articles": [...]
}
```

---

## Testing with cURL

### Register and Login
```bash
# Register
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Save the token from response
TOKEN="<your_token_here>"
```

### Use Protected Endpoints
```bash
# Get current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Get preferences
curl -X GET http://localhost:8000/preferences \
  -H "Authorization: Bearer $TOKEN"

# Update preferences
curl -X PUT http://localhost:8000/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic_preferences":[{"topic_id":1,"include_in_newsletter":true}]}'
```

---

For interactive API testing, visit http://localhost:8000/docs
