# Pulse News Aggregator

> 🧠 **AI-powered news aggregation** that transforms scattered headlines into coherent understanding through ethical framework mapping and intelligent analysis.

**Version:** ✅ **v1.0** - Production ready with complete feature set
**Tests:** 234/234 passing (100% - 127 backend + 107 frontend)

---

## 🎯 The Problem

Reading the news without long-term context feels like processing **scattered, unrelated tidbits** that your brain immediately forgets. Traditional news apps don't help you understand how stories relate to broader debates and ethical frameworks.

## 💡 The Solution

**Pulse** aggregates news from trusted sources, uses AI to:
- 🔍 Scrape articles from 8+ trusted news sources via RSS feeds
- 📊 Analyze sentiment, bias, and ethical frameworks with OpenAI GPT-4o-mini
- ✅ Verify statistics with 3-stage pipeline (source tracing, credibility, fact-checking)
- 🎯 Map articles to underlying ethical debates and framework positions
- 📧 Generate personalized daily newsletters that connect the dots
- 📈 Provide visualizations showing how news shapes discourse over time

### Example Framework Mapping

```
Article: "Biden Cancels Student Loan Debt"
Framework: Individual Liberty vs. Collective Welfare
Position: +6 (leans toward collective welfare)
Explanation: This policy prioritizes community benefit (debt relief)
over individual responsibility (loan repayment).
```

## 🚀 Quick Start

> **New to Pulse?** Start with our [📚 Documentation](docs/) for complete setup guides.

### Prerequisites
- **Docker & Docker Compose** - For containerized development
- **OpenAI API Key** - [Get one](https://platform.openai.com/)
- **Resend API Key** - [Get one](https://resend.com/) (for newsletters)

### One-Command Setup
```bash
git clone <your-repo>
cd Pulse
cp .env.example .env
# Edit .env with your API keys
docker-compose up --build
```

This starts:
- **Backend** (FastAPI) - http://localhost:8000
- **Frontend** (Next.js) - http://localhost:3000
- **Database** (PostgreSQL) - localhost:5432

### Next Steps
1. **Initialize Database:** `docker-compose exec backend alembic upgrade head`
2. **Seed Data:** `docker-compose exec backend python -m app.seed_data`
3. **Test Setup:** Visit http://localhost:8000/health (should return `{"status": "ok"}`)

For detailed setup instructions, see [Development Setup Guide](docs/development/SETUP.md).

### 🔧 Environment Configuration

**Important**: When updating environment variables, update both `.env` (local) and `render.yaml` (production).

Key environment variables:
```bash
# Required
OPENAI_API_KEY=sk-proj-...
RESEND_API_KEY=re_...

# Documentation Link
DOCUMENTATION_URL=https://docs.pulsenews.app

# See .env.example for complete list
```

## 🏗️ Tech Stack

### Backend (Python)
- **FastAPI** - REST API framework
- **SQLModel** - ORM with validation
- **PostgreSQL** - Primary database
- **Alembic** - Database migrations
- **APScheduler** - Background jobs
- **OpenAI GPT-4o-mini** - AI analysis

### Frontend (Next.js)
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **React** - UI framework
- **Recharts** - Data visualizations

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Render/Railway** - Deployment platforms
- **Resend** - Email delivery
- **RSS Feeds** - News source integration

## 📊 Project Status

### ✅ Completed (Version 1.0)

**Backend Systems** - Fully Operational
- [x] Complete article pipeline (scrape → extract → analyze → frameworks)
- [x] Statistics verification V2 with 3-stage pipeline (source tracing, credibility, fact-checking)
- [x] Article clustering & context generation
- [x] Newsletter generation & email delivery
- [x] User authentication & preferences (topics, sources, settings)
- [x] Complete admin panel with database management & job monitoring
- [x] Article URL analysis (on-demand analysis of any URL)
- [x] **127 backend tests passing**

**Frontend Systems** - Complete User Experience
- [x] Modern landing page with hero section
- [x] Full authentication flow (login, 2-step signup)
- [x] Enhanced preferences management (topics, sources, settings)
- [x] Interactive dashboard with analytics visualizations
- [x] Article feed with filtering & pagination
- [x] Comprehensive article detail pages with full analysis
- [x] Global navigation bar with user state
- [x] "How It Works" educational page
- [x] Article URL analysis interface
- [x] Complete admin panel interface (users, sources, articles, audit logs)
- [x] Performance monitoring and system health dashboard
- [x] React Query for optimized data fetching and caching
- [x] List virtualization components for large datasets
- [x] **107 frontend tests passing**

**Challenge System**
- [x] Weekly viewpoint engagement tracking
- [x] Viewpoint diversity analytics
- [x] Curated reflections and insights
- [x] Challenge completion tracking

### 🔮 Future Endeavors

**Advanced Features** - Future Enhancement
- [ ] Real-time updates (WebSockets)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics (claim recurrence, heatmap animations)
- [ ] Additional performance optimizations

## 📚 Documentation

### 🚀 Getting Started
- **[Development Setup](docs/development/SETUP.md)** - Installation & configuration
- **[Testing Guide](docs/testing/TESTING.md)** - Running and writing tests
- **[Deployment Guide](docs/guides/DEPLOYMENT_GUIDE.md)** - Production deployment

### 🏗️ Technical Documentation
- **[System Architecture](docs/architecture/ARCHITECTURE.md)** - Complete system design
- **[API Documentation](docs/api/API.md)** - REST API reference
- **[Statistics Verification V2](docs/architecture/STATISTICS_VERIFICATION_V2_PLAN.md)** - Stats pipeline design

### 📖 Reference Guides
- **[Git Workflow](docs/development/GIT_WORKFLOW_CHEATSHEET.md)** - Common git commands
- **[Email Testing](docs/guides/HOW_TO_SEND_TEST_EMAIL.md)** - Email testing guide
- **[Admin Panel Quick Start](docs/guides/ADMIN_PANEL_QUICK_START.md)** - Admin interface guide

### 📋 Planning & Architecture
- **[Frontend Architecture Plan](docs/planning/FRONTEND_ARCHITECTURE_PLAN.md)** - 16-week roadmap
- **[Admin Panel Plan](docs/planning/ADMIN_PANEL_PLAN.md)** - Complete implementation plan
- **[Feature Plans](docs/planning/features/)** - Individual feature specifications

## 🔧 Development

### Project Structure
```
Pulse/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── routes/         # API endpoints (including admin panel)
│   │   ├── services/       # Business logic
│   │   ├── models/         # Database schemas
│   │   ├── jobs/           # Background tasks
│   │   ├── utils/          # Utility functions
│   │   └── main.py        # Application entry
│   ├── alembic/          # Database migrations
│   ├── scripts/           # Utility scripts
│   └── tests/             # Backend tests (127 passing)
├── frontend/               # Next.js application
│   ├── src/app/          # App router pages (including admin panel)
│   ├── src/components/    # Reusable components
│   ├── src/lib/           # API client and utilities
│   └── __tests__/         # Frontend tests (107 passing)
├── docs/                 # Organized documentation
│   ├── architecture/       # System design docs
│   ├── api/              # API documentation
│   ├── development/       # Development guides
│   ├── testing/           # Testing documentation
│   ├── guides/            # How-to guides
│   └── planning/          # Feature plans
├── extension/             # Chrome extension
├── scripts/              # Development scripts
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml     # Development environment
├── render.yaml           # Production deployment config
├── Makefile             # Build automation
└── package.json         # Project metadata
```

### Running Tests
```bash
# Backend (all tests)
docker-compose exec backend pytest

# Frontend (all tests)
cd frontend && npm test

# With coverage
docker-compose exec backend pytest tests/ --cov=app --cov-report=html
```

### Database Operations
```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Manual job trigger
curl -X POST http://localhost:8000/admin/scrape
```

## 🌟 Key Features

### 1. AI-Generated Ethical Frameworks
- Start with 10 hand-curated ethical debates
- AI discovers new frameworks weekly from article clusters
- Automatic deduplication and archival

### 2. Context-Rich Newsletters
- Daily personalized newsletters
- Articles filtered by user preferences
- Framework connections explain "The Bigger Picture"
- Bias indicators and sentiment analysis

### 3. Statistics Verification Pipeline
- **Stage 1:** Source tracing and credibility assessment
- **Stage 2:** Source rating and context gathering
- **Stage 3:** External fact-checking API integration
- V2 pipeline with comprehensive verification tracking

### 4. Article URL Analysis
- On-demand analysis of any article URL
- Complete AI pipeline applied instantly
- User-submitted articles appear in feed
- Duplicate detection and de-duplication

## 🔐 Security & Privacy

- **JWT-based authentication** with secure token handling
- **Bcrypt password hashing** for security
- **Environment-based secrets** management
- **No third-party tracking** (user-controlled email preferences)
- **GDPR-compliant** data handling

## 🔗 Quick Links

- **Interactive API Docs**: http://localhost:8000/docs
- **Frontend Dev Server**: http://localhost:3000
- **Complete Documentation**: [docs/](docs/)
- **AI Assistant Guide**: [llm-instructions.md](llm-instructions.md)
- **Project Changelog**: [CHANGELOG.md](CHANGELOG.md)

## 🤝 Contributing

This is a personal project, but feedback is welcome!

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** (add tests!)
4. **Run the test suite** (`npm test` and `pytest`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## 🤝 Contributing

This is a personal project, but feedback is welcome!

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** (add tests!)
4. **Run the test suite** (`npm test` and `pytest`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

## 📝 License

This project is free for personal/non-commercial use under the [CC BY-NC 4.0 License](https://creativecommons.org/licenses/by-nc/4.0/).
For commercial use, please contact [email] for a commercial license.


---

## 🏆 Version 1.0

**Built to make news less overwhelming**

*Last updated: October 24, 2025*