# Pulse News Aggregator

> AI-powered news aggregation with ethical framework mapping to help you build context and connect scattered headlines into a coherent mental model.

## 🎯 The Problem

Reading the news without long-term context feels like processing **scattered, unrelated tidbits** that your brain immediately forgets. Traditional news apps don't help you understand how stories relate to broader debates and ethical frameworks.

## 💡 The Solution

**Pulse** aggregates news from trusted sources, uses AI to:
- Summarize articles (100 words)
- Analyze sentiment and political bias
- Extract and verify key statistics
- **Map articles to underlying ethical debates** (the "competitive edge")
- Generate daily newsletters that connect the dots

### Example Framework Mapping

```
Article: "Biden Cancels Student Loan Debt"
Framework: Individual Liberty vs. Collective Welfare
Position: +6 (leans toward collective welfare)
Explanation: This policy prioritizes community benefit (debt relief)
over individual responsibility (loan repayment).
```

## 🏗️ Architecture

### Tech Stack

**Backend (Python)**
- FastAPI for API
- SQLModel for ORM
- PostgreSQL for database
- Alembic for migrations
- APScheduler for jobs
- Claude Haiku for AI analysis

**Scraping**
- feedparser (RSS feeds)
- trafilatura (article extraction)
- readability-lxml (fallback)

**Email**
- Resend API
- Jinja2 templates

**Frontend (Next.js)**
- TypeScript
- Tailwind CSS
- Newsletter preview
- User preferences

**Infrastructure**
- Docker & Docker Compose
- Railway/Render (free tier MVP)
- DigitalOcean (scale)

### Database Schema

```
sources → articles → article_analysis
   ↓                       ↓
topics              article_frameworks → frameworks
   ↓                                           ↑
user_topic_preferences              (AI-generated debates)
   ↓
users → newsletters
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Anthropic API key ([get one](https://console.anthropic.com/))
- Resend API key ([get one](https://resend.com/))

### Setup

1. **Clone and configure**
   ```bash
   git clone <your-repo>
   cd Pulse
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start services**
   ```bash
   docker-compose up --build
   ```

3. **Run migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Seed initial data**
   ```bash
   docker-compose exec backend python -m app.seed_data
   ```

5. **Test the API**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "ok"}
   ```

## 📊 Project Status

See [SETUP_PROGRESS.md](SETUP_PROGRESS.md) for detailed status.

### ✅ Completed (Foundation)
- [x] Database models (SQLModel)
- [x] Alembic migrations setup
- [x] Docker configuration
- [x] Initial data seeding
- [x] Configuration management
- [x] FastAPI app structure

### 🔄 In Progress
- [ ] RSS scraper service
- [ ] Article extraction
- [ ] APScheduler jobs
- [ ] Claude AI integration
- [ ] Framework generation

### 📅 Upcoming
- [ ] Newsletter builder
- [ ] Email sending
- [ ] User authentication
- [ ] Frontend UI

## 🔧 Development

### Project Structure

```
Pulse/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB session
│   │   ├── models.py        # SQLModel schemas
│   │   ├── seed_data.py     # Initial data
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── jobs/            # Scheduled tasks
│   │   ├── templates/       # Email templates
│   │   └── utils/           # Helpers
├── frontend/                # Next.js app
├── docker-compose.yml
├── dockerfile
└── requirements.txt
```

### Running Locally

**Backend only:**
```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload
```

**Frontend only:**
```bash
cd frontend
npm run dev
```

**With Docker (recommended):**
```bash
docker-compose up
```

### Database Migrations

```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

## 📈 Scaling Strategy

### Phase 1: MVP (50 users) - $0-5/month
- Railway/Render free tier
- Claude Haiku API (~$2/month)
- Resend free tier (3k emails/month)

### Phase 2: Growth (500 users) - $30-50/month
- DigitalOcean droplet ($12-24)
- AI processing ($10-20)
- Resend paid tier ($5-10)

### Phase 3: Scale (5000+ users) - $100-300/month
- Load balancer + multiple servers
- Database read replicas
- Redis for caching
- CDN for static assets

## 💰 Cost Optimization

**AI Costs** (biggest expense):
1. **Batch processing**: 5 articles per API call (60% savings)
2. **Claude Haiku**: Cheapest option at $0.25/1M input tokens
3. **Smart caching**: Don't reprocess similar articles
4. **Selective processing**: Only analyze articles for active topics

**Estimated costs at scale:**
- 50 users: $2-5/month
- 500 users: $30-50/month
- 5000 users: $100-300/month

## 🌟 Unique Features

### 1. AI-Generated Frameworks
- Start with 10 hand-curated ethical debates
- AI discovers new frameworks weekly from article clusters
- Automatic deduplication and archival

### 2. Context-Rich Newsletters
```
📰 Today's Top Stories
[Article summaries with bias indicators]

🧠 The Bigger Picture
These stories connect to ongoing debates:
- Framework 1: How today's articles relate to this debate
- Framework 2: The underlying ethical tension
```

### 3. Personalized Topic Selection
Users toggle topics they care about:
- ✓ Politics
- ✓ Technology
- ✓ Economics
- ✗ Culture
- ✗ Environment

Newsletter includes articles from selected topics + suggested frameworks.

## 🔐 Security & Privacy

- JWT-based authentication
- Bcrypt password hashing
- Environment-based secrets
- No third-party tracking (user controls email tracking)
- GDPR-compliant (email preference management)

## 📚 API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

This is a personal project, but feedback welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- News sources: AP, Reuters, NPR, BBC, NYT, Politico, Ars Technica, The Atlantic
- AI: Anthropic Claude
- Inspiration: The need for better news context and mental models

## 📞 Contact

[Your contact info]

---

**Built with** ❤️ **and AI to make news less overwhelming**
