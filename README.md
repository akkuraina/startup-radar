# 🚀 Startup Radar

**Automated system to discover recently-funded startups and detect when they're hiring.**

Uses **Tavily API** for web search, **Claude LLM** for intelligent data extraction, **Supabase PostgreSQL** for cloud storage, and **Next.js** for the dashboard.

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Deployment](#deployment)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase Account (Free) - see [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
- API Keys: Tavily, Claude, Resend

### Local Development

**1. Clone & Setup Backend**

```bash
cd startup-radar
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

**2. Configure Supabase Database**

**📖 Complete guide**: [SUPABASE_SETUP.md](SUPABASE_SETUP.md)

Quick steps:

1. Create free Supabase project at https://supabase.com
2. Get connection string from Settings → Database
3. Save in `.env` as `DATABASE_URL`

**3. Configure Environment**

```bash
# Copy .env.example to .env
cp ../.env.example ../.env

# Update with your values:
# - DATABASE_URL from Supabase (see SUPABASE_SETUP.md)
# - TAVILY_API_KEY from https://tavily.com
# - ANTHROPIC_API_KEY from https://console.anthropic.com
# - RESEND_API_KEY from https://resend.com
```

**4. Start Backend**

```bash
# From backend/ directory
uvicorn main:app --reload
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

**5. Start Frontend (in new terminal)**

```bash
cd frontend
npm install
npm run dev
# Dashboard available at http://localhost:3000
```

### Docker Compose (All Services)

```bash
# Build and start all services
docker-compose up --build

# Access:
# - API: http://localhost:8000
# - Frontend: http://localhost:3000
# - Database: Supabase cloud-hosted (no local database needed)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│           SCHEDULER (APScheduler)                    │
│         Runs pipeline every 6 hours                 │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │   DATA FETCHER   │
        │  - Tavily API    │
        │  - RSS Feeds     │
        └────────┬────────┘
                 │  Raw articles
        ┌────────▼────────┐
        │  AI PARSER       │
        │  (Claude API)    │
        │  Extracts JSON:  │
        │  - Company       │
        │  - Amount        │
        │  - Round         │
        │  - Investors     │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  DEDUPLICATOR    │
        │  Insert/Update   │
        │  existing        │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  ENRICHER        │
        │  - Website       │
        │  - LinkedIn      │
        │  - Hiring detect │
        └────────┬────────┘
                 │
        ┌────────▼────────────────┐
        │  Supabase PostgreSQL DB  │
        │  (Cloud-Hosted)          │
        └────────┬────────────────┘
                 │
     ┌───────────┴──────────┐
     │                      │
┌────▼─────┐          ┌──────▼──────┐
│ FastAPI  │          │  ALERTER    │
│ REST API │          │ (Resend)    │
└────┬─────┘          └─────────────┘
     │
┌────▼──────────────┐
│  Next.js Frontend  │
│  - Dashboard       │
│  - Filters         │
│  - Export          │
└───────────────────┘
```

---

## ✨ Features

### Data Collection

- **Tavily API**: Real-time web search for funding announcements
- **RSS Feeds**: TechCrunch, Bloomberg, CNBC, Reuters
- **Multi-source**: Combines data from multiple sources, deduplicates

### AI Extraction

- **Claude API**: Intelligent extraction of structured data from articles
- **JSON Output**: Standardized schema for all companies
- **Error Handling**: Graceful fallback if extraction fails

### Data Quality

- **Deduplication**: Checks if company exists before inserting
- **Normalization**: Standardized names, amounts, dates
- **Enrichment**: Website detection, LinkedIn URLs, hiring signals

### Hiring Detection

- **Careers Page Detection**: Checks for /careers, /jobs, /hiring pages
- **Tech Roles**: Identifies engineering, design, product roles
- **Alert Integration**: Email alerts when companies start hiring

### Dashboard

- **Real-time Stats**: Total companies, funding, hiring count
- **Filterable Table**: Search by company, country, funding round
- **Hiring Signals**: Dedicated section for actively hiring companies
- **One-click Export**: Download companies as CSV
- **Pipeline Trigger**: Run data collection from dashboard

---

## 🔌 API Endpoints

### Status

- `GET /health` - Health check
- `GET /` - API info

### Statistics

- `GET /api/stats` - Dashboard stats (companies, funding, hiring)

### Companies

- `GET /api/companies` - List all companies (with pagination, filters)
  - Query params: `skip`, `limit`, `country`, `round_type`, `search`, `hiring_only`
- `GET /api/companies/{company_id}` - Single company details
- `GET /api/companies/hiring/active` - Only hiring companies

### Export

- `GET /api/export/csv` - Download as CSV
- `GET /api/export/json` - Download as JSON

### Pipeline

- `POST /api/pipeline/run` - Manually trigger data collection

### Interactive Docs

- `GET /docs` - Swagger UI (auto-generated API documentation)

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Database (Supabase PostgreSQL - Cloud Hosted)
# Get from: https://supabase.com (see SUPABASE_SETUP.md)
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres

# Tavily API (Web Search)
TAVILY_API_KEY=your_tavily_key

# Anthropic Claude (LLM)
ANTHROPIC_API_KEY=your_anthropic_key

# Resend Email
RESEND_API_KEY=your_resend_key
FROM_EMAIL=noreply@yourapp.com
TO_EMAILS=email1@example.com,email2@example.com

# Server
PORT=8000

# Scheduler
SCHEDULE_INTERVAL_HOURS=6
ENABLE_SCHEDULER=true
```

### Getting API Keys

**Tavily API** (Free)

1. Go to https://tavily.com
2. Sign up for free account
3. Copy API key

**Claude API** (Free tier available)

1. Go to https://console.anthropic.com
2. Create account
3. Generate API key
4. Free tier includes $5 credits/month

**Resend Email** (Free)

1. Go to https://resend.com
2. Sign up
3. Verify sending domain
4. Generate API key

---

## 📁 Project Structure

```
startup-radar/
├── backend/
│   ├── main.py                  # FastAPI server
│   ├── scheduler.py             # APScheduler jobs
│   ├── fetcher.py               # Tavily + RSS
│   ├── parser.py                # Claude LLM
│   ├── deduplicator.py          # DB upsert
│   ├── enricher.py              # Hiring detection
│   ├── alerter.py               # Email alerts
│   ├── models.py                # SQLAlchemy ORM
│   ├── database.py              # DB connection
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Dashboard
│   │   ├── layout.tsx           # Layout
│   │   └── globals.css          # Styles
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── .env.local
├── docker-compose.yml
├── Dockerfile.backend
└── README.md
```

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# In background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down
```

### Environment Variables for Docker

Create a `.env` file in the root directory with all configuration values. Docker Compose will automatically load it.

### Database Initialization

Database tables are created automatically on first run. No manual migration needed.

---

## 📊 Pipeline Execution

### Automated (Every 6 hours)

When `ENABLE_SCHEDULER=true`, the pipeline runs automatically:

1. Fetches articles from Tavily API + RSS
2. Parses with Claude LLM
3. Deduplicates against existing companies
4. Enriches with website, LinkedIn, hiring signals
5. Sends alerts for newly hiring companies

### Manual (Via API)

```bash
curl -X POST http://localhost:8000/api/pipeline/run
```

Or use the dashboard "Run Pipeline" button.

---

## 🔍 Data Schema

### companies

- `id` - Primary key
- `company_name` - Unique company name
- `amount_usd` - Funding amount
- `round_type` - Series A, Seed, etc.
- `investors` - JSON array of investors
- `country` - Country of operation
- `announcement_date` - When funding announced
- `website_url` - Company website
- `is_hiring` - Boolean hiring status
- `open_roles_count` - Number of open positions
- `job_titles` - JSON array of found tech roles
- `created_at`, `updated_at` - Timestamps

---

## 🚀 Scaling

### Current Setup

- **Database**: Supabase PostgreSQL (cloud-hosted, easily scales to thousands of companies)
- **API**: FastAPI (handles hundreds of requests/second)
- **Pipeline**: Runs every 6 hours (can be adjusted)

### Future Scaling

1. **Upgrade Plan**: Supabase Pro ($25/month) for 8GB storage
2. **Caching**: Add Redis for frequently accessed data
3. **Queue**: Use Celery + RabbitMQ for distributed pipeline
4. **Load Balancer**: Multiple API replicas
5. **Monitoring**: Add Prometheus + Grafana
6. **CDN**: Serve frontend through CDN

---

## 📝 Logging

Logs are written to:

- **Console**: Real-time output
- **File**: `backend/logs/app.log`

Toggle debug mode in `config.py`.

---

## 🐛 Troubleshooting

### Database Connection Error

```
1. Check DATABASE_URL in .env matches your Supabase connection string
2. Verify Supabase project is active
3. Check password is correct in connection string
4. Test: psql [YOUR_CONNECTION_STRING]
See SUPABASE_SETUP.md for complete Supabase setup
```

### API Key Errors

```
Verify TAVILY_API_KEY, ANTHROPIC_API_KEY in .env
Check keys haven't expired at their respective dashboards
```

### Claude API Errors

```
Common: Rate limiting (free tier: 50k tokens/month)
Solution: Wait or upgrade plan
```

### Resend Email Issues

```
FROM_EMAIL must be verified in Resend dashboard
Check email spam folder for delivery
```

---
