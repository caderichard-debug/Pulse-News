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
- OpenAI GPT-4o-mini for AI analysis

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
- OpenAI API key ([get one](https://platform.openai.com/))
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

✅ **All systems operational** - 234/234 tests passing (100%)
- **Backend**: 127 tests passing
- **Frontend**: 107 tests passing

### ✅ Completed

**Backend (Phase 1-3)**
- [x] Database models & migrations (18 tables)
- [x] Docker configuration
- [x] RSS scraper service (8 sources)
- [x] Article extraction (trafilatura + readability fallback)
- [x] APScheduler background jobs (8 scheduled tasks)
- [x] OpenAI GPT-4o-mini integration (analysis & framework generation)
- [x] Statistics verification V2 (3-stage pipeline: source tracing, credibility, fact-checking)
- [x] Article clustering & context generation
- [x] Newsletter generation & email sending
- [x] User authentication (JWT)
- [x] API endpoints (28 routes: auth, preferences, analytics, feed, articles, admin)
- [x] Comprehensive test suite (127 tests, 100% passing)
- [x] Render.com deployment configuration

**Frontend (Phase 1-3)**
- [x] Landing page with hero section
- [x] Authentication (login, 2-step signup with topic selection)
- [x] Enhanced preferences (topics, sources, settings) with 3-tab interface
- [x] Dashboard with analytics visualizations (sentiment, bias, framework heatmap)
- [x] Article feed with filtering (topic, source, political lean) and pagination
- [x] Article detail pages (full analysis, verified statistics, frameworks, context, related articles)
- [x] Global navigation bar
- [x] "How It Works" educational page
- [x] Comprehensive test suite (107 tests, 100% passing)

### 🔄 In Progress (Phase 4)
- [ ] Challenge system (weekly viewpoint engagement tracking)
- [ ] Viewpoint diversity analytics
- [ ] Curated reflections

### 📅 Upcoming (Phase 5-6)
- [ ] Advanced analytics (claim recurrence, animated heatmaps)
- [ ] Performance optimization (React Query, virtualization)
- [ ] Dark mode & accessibility enhancements
- [ ] Mobile responsive refinements

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
│   │   ├── utils/           # Helpers
│   ├── Dockerfile           # Dockerfile
│   ├── docker-compose.yml
├── frontend/                # Next.js app
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
- OpenAI GPT-4o-mini API (~$2/month)
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
2. **OpenAI GPT-4o-mini**: Cost-effective at $0.150/1M input tokens, $0.600/1M output tokens
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

## 📚 Documentation

- **[Setup Guide](docs/SETUP.md)** - Installation and configuration
- **[Render Deployment](docs/RENDER_DEPLOYMENT.md)** - Deploy to Render with Blueprint
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Architecture](docs/ARCHITECTURE.md)** - System design and data flow
- **[Testing Guide](docs/TESTING.md)** - Running and writing tests

Interactive API docs: http://localhost:8000/docs

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
- AI: OpenAI GPT-4o-mini
- Inspiration: The need for better news context and mental models

## 📞 Contact

[Your contact info]

---

**Built with** ❤️ **and AI to make news less overwhelming**
