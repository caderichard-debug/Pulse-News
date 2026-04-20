# API Documentation

Base URL: `http://localhost:8000`

Interactive docs: http://localhost:8000/docs

> **Related Documentation:**
> - [System Architecture](../architecture/ARCHITECTURE.md) - Understand the underlying system design
> - [Development Setup](../development/SETUP.md) - Get the API server running locally
> - [Testing Guide](../testing/TESTING.md) - Learn how to test these endpoints

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
POST /auth/register
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

### Extended Preferences Endpoints

#### Get All Topics

```http
GET /preferences/topics
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Politics",
    "description": "Political news and analysis",
    "is_active_default": true
  },
  {
    "id": 2,
    "name": "Technology",
    "description": "Tech industry news",
    "is_active_default": true
  }
]
```

---

#### Subscribe to Topic

```http
POST /preferences/topics/{topic_id}/subscribe
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Subscribed to topic successfully"
}
```

---

#### Unsubscribe from Topic

```http
POST /preferences/topics/{topic_id}/unsubscribe
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Unsubscribed from topic successfully"
}
```

---

#### Get Newsletter Preview

```http
GET /preferences/newsletter-preview
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "source": "Reuters",
      "summary": "Brief summary..."
    }
  ],
  "topic_breakdown": {
    "Politics": 3,
    "Technology": 2
  }
}
```

---

#### Get Source Preferences

```http
GET /preferences/sources
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "source_id": 1,
    "name": "Reuters",
    "trust_score": 9.5,
    "political_lean": "center",
    "subscribed": true
  },
  {
    "source_id": 2,
    "name": "Fox News",
    "trust_score": 6.2,
    "political_lean": "right",
    "subscribed": false
  }
]
```

---

#### Update Source Preferences

```http
PUT /preferences/sources
```

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "source_ids": [1, 2, 3],
  "discovery_mode": "some"
}
```

**Response:**
```json
{
  "message": "Source preferences updated"
}
```

---

#### Get User Settings

```http
GET /preferences/settings
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "article_order": "good_first",
  "articles_per_topic": 5,
  "discovery_mode": "some"
}
```

---

#### Update User Settings

```http
PUT /preferences/settings
```

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "article_order": "mixed",
  "articles_per_topic": 7
}
```

**Response:**
```json
{
  "message": "Settings updated successfully"
}
```

---

### Analytics Endpoints

#### Get User Statistics

```http
GET /analytics/user-stats
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "articles_read": 127,
  "newsletters_received": 42,
  "topics_tracked": 5,
  "avg_sentiment": -0.3
}
```

---

#### Get Sentiment Over Time

```http
GET /analytics/sentiment-over-time
```

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `days` (int, optional) - Number of days to fetch (default: 30)
- `topics` (str, optional) - Comma-separated topic IDs

**Response:**
```json
[
  {
    "date": "2025-10-01",
    "Politics": -2.3,
    "Technology": 4.5,
    "Climate": -1.2
  },
  {
    "date": "2025-10-02",
    "Politics": -1.8,
    "Technology": 3.9,
    "Climate": -0.5
  }
]
```

---

#### Get Bias Distribution

```http
GET /analytics/bias-distribution
```

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `weeks` (int, optional) - Number of weeks (default: 4)

**Response:**
```json
[
  {
    "week": "2025-09-25",
    "left": 35,
    "center": 40,
    "right": 25
  },
  {
    "week": "2025-10-02",
    "left": 30,
    "center": 45,
    "right": 25
  }
]
```

---

#### Get Framework Heatmap

```http
GET /analytics/framework-heatmap
```

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `framework1_id` (int, required) - First framework ID
- `framework2_id` (int, required) - Second framework ID
- `days` (int, optional) - Number of days (default: 30)

**Response:**
```json
[
  {
    "x": -8,
    "y": 6,
    "article_count": 23,
    "avg_sentiment": -4.2,
    "sample_articles": [
      {"id": 123, "title": "..."},
      {"id": 124, "title": "..."}
    ]
  }
]
```

---

#### Get Available Frameworks

```http
GET /analytics/frameworks/available
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Individual Liberty vs. Collective Welfare",
    "description": "Core tension between personal freedom and community benefit",
    "article_count": 45
  }
]
```

---

### Feed Endpoints

#### Get Article Feed

```http
GET /feed/articles
```

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `topic_ids` (str, optional) - Comma-separated topic IDs
- `source_ids` (str, optional) - Comma-separated source IDs
- `sentiment_min` (float, optional) - Minimum sentiment (-10 to 10)
- `sentiment_max` (float, optional) - Maximum sentiment (-10 to 10)
- `page` (int, optional) - Page number (default: 1)
- `page_size` (int, optional) - Items per page (default: 20)

**Response:**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "Breaking News",
      "source_name": "Reuters",
      "published_at": "2025-10-04T08:00:00Z",
      "sentiment_score": 2.3,
      "political_lean": "center",
      "summary": "Brief summary...",
      "frameworks": [
        {
          "name": "Liberty vs Welfare",
          "position": 6
        }
      ]
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

#### Get Feed Topics

```http
GET /feed/topics
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Politics",
    "article_count": 45
  },
  {
    "id": 2,
    "name": "Technology",
    "article_count": 32
  }
]
```

---

#### Get Feed Sources

```http
GET /feed/sources
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Reuters",
    "article_count": 28
  },
  {
    "id": 2,
    "name": "BBC",
    "article_count": 19
  }
]
```

---

### Article Endpoints

#### Get Analyzed Articles

```http
GET /articles/analyzed
```

**Query Parameters:**
- `limit` (int, optional) - Number of articles (default: 10)
- `offset` (int, optional) - Pagination offset (default: 0)

**Response:**
```json
{
  "total": 50,
  "articles": [
    {
      "id": 1,
      "title": "Article Title",
      "url": "https://...",
      "source": {
        "name": "Reuters",
        "url": "https://reuters.com"
      },
      "published_at": "2025-10-04T08:00:00Z",
      "word_count": 850,
      "analysis": {
        "summary": "100-word summary...",
        "sentiment_score": 2.3,
        "political_lean": "center",
        "bias_indicators": ["minimal loaded language"],
        "key_stats": ["50% increase"],
        "processed_at": "2025-10-04T09:00:00Z"
      }
    }
  ]
}
```

---

#### Get Article Detail

```http
GET /articles/{article_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "title": "Article Title",
  "url": "https://...",
  "published_at": "2025-10-04T08:00:00Z",
  "source_name": "Reuters",
  "source_url": "https://reuters.com",
  "topic_category": "Politics",
  "content_preview": "First 500 characters...",
  "summary": "100-word AI summary...",
  "sentiment_score": 2.3,
  "political_lean": "center",
  "statistics": [
    {
      "statistic": "50% increase in crossings",
      "verification_status": "verified",
      "confidence": 0.85,
      "source_name": "DHS",
      "source_url": "https://...",
      "source_credibility_score": 8.5,
      "fact_check_status": "confirmed",
      "fact_check_source": "FactCheck.org"
    }
  ],
  "frameworks": [
    {
      "framework_id": 1,
      "framework_name": "Liberty vs Welfare",
      "left_position": "Individual rights",
      "right_position": "Community welfare",
      "position_on_axis": 6,
      "relevance_score": 0.85,
      "explanation": "Article emphasizes collective benefit..."
    }
  ],
  "related_articles": [
    {
      "id": 2,
      "title": "Related Coverage",
      "source_name": "BBC",
      "published_at": "2025-10-04T09:00:00Z",
      "sentiment_score": -3.1,
      "political_lean": "center",
      "url": "https://..."
    }
  ],
  "context": {
    "background": "This issue dates back to...",
    "key_players": "Biden, Congress...",
    "timeline": "Jan 2024: Initial proposal...",
    "significance": "This matters because..."
  }
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
