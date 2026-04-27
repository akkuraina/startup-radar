# 📖 Complete Setup Guide for Startup Radar

This guide walks you through setting up Startup Radar from scratch.

---

## Step 1: Get API Keys (15 minutes)

### Tavily API (Web Search)

1. Go to https://tavily.com
2. Click "Get Started" (Free)
3. Sign up with email
4. Copy your API key from dashboard
5. Paste into `.env` as `TAVILY_API_KEY`

### Anthropic Claude (LLM)

1. Go to https://console.anthropic.com
2. Sign up with email
3. Add payment method (or use free tier: $5/month)
4. Generate API key in "Account Settings"
5. Paste into `.env` as `ANTHROPIC_API_KEY`

### Resend (Email Delivery)

1. Go to https://resend.com
2. Sign up (Free)
3. Generate API key
4. Add and verify your email domain
5. Paste into `.env` as `RESEND_API_KEY`

---

## Step 2: Clone & Install (10 minutes)

### On Windows PowerShell

```powershell
# Navigate to your projects folder
cd D:\DJSCE\CODING\startup-radar

# Check what we have
ls

# You should see: backend/, frontend/, docker-compose.yml, README.md
```

### Setup Backend

```powershell
cd backend

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Setup Frontend

```powershell
# From startup-radar root
cd frontend

# Install Node dependencies
npm install
```

---

## Step 3: Configure Environment (.env)

From the `startup-radar` root directory:

```powershell
# Copy example to actual .env
Copy-Item .env.example .env

# Edit .env with your API keys
notepad .env
```

**For DATABASE_URL, see [SUPABASE_SETUP.md](SUPABASE_SETUP.md)** - it has complete Supabase connection instructions.

Quick preview:

```
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
TAVILY_API_KEY=tvly-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
RESEND_API_KEY=re-xxxxx
FROM_EMAIL=noreply@startup-radar.com
TO_EMAILS=your-email@example.com
```

---

## Step 4: Setup Supabase Database (5 minutes)

**🎉 No local database installation needed!** We use Supabase cloud PostgreSQL.

**Complete guide**: [SUPABASE_SETUP.md](SUPABASE_SETUP.md)

**Quick steps**:

1. Go to https://supabase.com
2. Create free project
3. Get connection string from Settings → Database
4. Paste into `.env` as `DATABASE_URL`

---

## Step 5: Run Your Application

### Option A: Local Development (Recommended)

```powershell
cd backend

# Activate venv
.\venv\Scripts\Activate.ps1

# Run API
uvicorn main:app --reload

# You should see:
# ✅ Database initialized successfully
# ✅ Database connection verified
# Uvicorn running on http://0.0.0.0:8000
```

**In another PowerShell window**:

```powershell
cd frontend
npm run dev

# You should see:
# > next dev
# - ready started server on 0.0.0.0:3000
```

### Option B: Docker Compose (Full Stack)

```powershell
# From startup-radar root
docker-compose up --build

# All services start automatically
# You should see:
# backend_1   | ✅ Database initialized successfully
# frontend_1  | ready started server on 0.0.0.0:3000
```

### Access Your App

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

---

## Step 6: Test the System

### 1. Check API Health

```powershell
# In PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/health" | Select-Object -ExpandProperty Content
# Should return: {"status":"healthy","timestamp":"..."}
```

### 2. Check API Docs

Open browser: http://localhost:8000/docs

### 3. View Dashboard

Open browser: http://localhost:3000

### 4. Trigger Pipeline

```powershell
# Via API
curl -X POST http://localhost:8000/api/pipeline/run

# Or click "Run Pipeline" button in dashboard
```

---

## Step 6: Configure Alerts (Optional)

### Email Alerts

1. Update `TO_EMAILS` in `.env` with your email
2. Verify your domain in Resend dashboard
3. Pipeline will email you when:
   - New funding is detected
   - A company starts hiring

### Slack Integration (Future)

Currently using Resend email. Can easily add Slack webhooks.

---

## Troubleshooting

### Port Already in Use

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with actual number)
taskkill /PID <PID> /F
```

### Database Connection Error

```
Error: could not connect to server: Connection refused

Solutions:
1. Ensure PostgreSQL is running: services.msc → PostgreSQL
2. Check DATABASE_URL in .env
3. For Docker: ensure postgres service is healthy
```

### Python Module Not Found

```powershell
# Ensure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall requirements
pip install -r requirements.txt
```

### Node Module Not Found

```powershell
cd frontend
rm -r node_modules
npm install
npm run dev
```

---

## Next Steps

1. **Configure More Sources**: Edit `fetcher.py` to add more RSS feeds
2. **Customize Parser**: Edit Claude prompt in `parser.py`
3. **Add More Alerts**: Edit `alerter.py` to add Slack, Teams, etc.
4. **Deploy to Cloud**: Use Docker image for AWS, GCP, Azure
5. **Monitor Pipeline**: Check `logs/app.log` for execution details

---

## File Locations

```
startup-radar/
├── .env                          ← Your configuration (KEEP SECRET!)
├── backend/
│   ├── main.py                   ← FastAPI server
│   ├── logs/app.log              ← Execution logs
│   └── requirements.txt
├── frontend/
│   ├── app/page.tsx              ← Dashboard code
│   └── package.json
└── docker-compose.yml            ← Docker config
```

---

## Common Commands

```powershell
# Backend
cd backend
.\venv\Scripts\Activate.ps1      # Activate venv
python main.py                    # Start server
python -m pytest tests/           # Run tests (if added)

# Frontend
cd frontend
npm run dev                        # Start dev server
npm run build                      # Build for production
npm run start                      # Run production build

# Docker
docker-compose up -d              # Start in background
docker-compose logs -f backend    # Watch backend logs
docker-compose down               # Stop all services
docker-compose ps                 # See running containers
```

---

## Architecture Recap

```
Data Collection (Tavily + RSS)
         ↓
LLM Parsing (Claude)
         ↓
Deduplication & Storage (PostgreSQL)
         ↓
Enrichment (Hiring detection)
         ↓
Alerts (Resend email)
         ↓
REST API (FastAPI)
         ↓
Dashboard (Next.js)
```

Each component is independent and can be scaled separately.

---

## Support

- Check `README.md` for general documentation
- Check `docker-compose.yml` for service configuration
- Check logs in `backend/logs/app.log` for errors
- Check API docs at http://localhost:8000/docs for endpoint details

---

**You're all set! 🚀 Start with `docker-compose up` or the local setup above.**
