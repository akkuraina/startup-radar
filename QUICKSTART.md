# 🚀 Quick Start Reference

## 30-Second Start

```bash
# Prerequisites:
# 1. Create free Supabase account (https://supabase.com)
# 2. Get DATABASE_URL from Supabase (see SUPABASE_SETUP.md)
# 3. Add DATABASE_URL to .env with other API keys

# Then:
docker-compose up

# Wait 2 minutes, then:
# - Dashboard: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

---

## Setup Checklist

- [ ] Supabase account created
- [ ] Database connection string obtained
- [ ] `.env` file created with DATABASE_URL and API keys
- [ ] Docker Desktop installed (or Python 3.11 + Node 18 for local dev)

**See [SUPABASE_SETUP.md](SUPABASE_SETUP.md)** for detailed setup instructions.

---

## Development Quick Commands

### Backend Only

```bash
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

### Frontend Only

```bash
cd frontend
npm run dev
# Open http://localhost:3000
```

### Run Pipeline Manually

```bash
curl -X POST http://localhost:8000/api/pipeline/run
```

### Check API Health

```bash
curl http://localhost:8000/health
```

### Query Supabase Database

```bash
# Using psql (if installed):
psql "postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres" \
  -c "SELECT COUNT(*) FROM companies;"

# Or use Supabase Dashboard: SQL Editor section
```

### View Backend Logs

```bash
# Docker
docker-compose logs -f backend

# Local
tail -f backend/logs/app.log
```

### Stop Everything

```bash
docker-compose down
```

---

## File to Edit Checklists

### Adding New Data Source

1. Edit `backend/fetcher.py` → Add function in `fetch_all_sources()`
2. Update `backend/parser.py` → Adjust parser if needed
3. Restart: `docker-compose restart backend`

### Changing Email Alerts

1. Edit `backend/alerter.py` → Modify `format_funding_alert()` and `format_hiring_alert()`
2. Update `TO_EMAILS` in `.env`
3. Restart: `docker-compose restart backend`

### Customizing Dashboard

1. Edit `frontend/app/page.tsx`
2. Save (auto-reloads in dev mode)
3. For production: `npm run build && npm run start`

### Changing Pipeline Schedule

1. Edit `.env` → `SCHEDULE_INTERVAL_HOURS=X` (default: 6)
2. Restart: `docker-compose restart backend`

---

## API Endpoints Quick Reference

```bash
# Get stats
curl http://localhost:8000/api/stats

# List companies (first 10)
curl "http://localhost:8000/api/companies?limit=10"

# Search companies
curl "http://localhost:8000/api/companies?search=OpenAI"

# Filter by country
curl "http://localhost:8000/api/companies?country=USA"

# Get hiring companies
curl "http://localhost:8000/api/companies/hiring/active"

# Export CSV
curl http://localhost:8000/api/export/csv -o companies.csv

# Export JSON
curl http://localhost:8000/api/export/json -o companies.json

# Trigger pipeline
curl -X POST http://localhost:8000/api/pipeline/run

# View Swagger docs
open http://localhost:8000/docs
```

---

## Environment Variables Quick Edit

```powershell
# Edit .env
notepad .env

# Must have:
TAVILY_API_KEY=
ANTHROPIC_API_KEY=
RESEND_API_KEY=
```

---

## Troubleshooting One-Liners

```powershell
# Port in use?
netstat -ano | findstr :8000

# Database not responding?
psql -U postgres -c "SELECT 1;"

# Clear Docker containers?
docker-compose down -v

# Rebuild everything?
docker-compose up --build --force-recreate

# See all API logs?
docker-compose logs -f backend

# Is frontend running?
curl http://localhost:3000
```

---

## Deployment Quick Checklist

- [ ] .env configured with real API keys
- [ ] DATABASE_URL points to production database
- [ ] TO_EMAILS configured with real addresses
- [ ] docker-compose up runs without errors
- [ ] All three services healthy: `docker-compose ps`
- [ ] Dashboard loads at http://localhost:3000
- [ ] Pipeline runs: `curl -X POST http://localhost:8000/api/pipeline/run`
- [ ] CSV export works: `curl http://localhost:8000/api/export/csv`

---

## Cost Summary (Monthly)

| Service    | Free Tier     | Cost for 1M Requests |
| ---------- | ------------- | -------------------- |
| Tavily     | ✅ 100 calls  | $10-50               |
| Claude     | ✅ $5 credits | $20-100              |
| Resend     | ✅ 100 emails | $0 (included)        |
| PostgreSQL | ❌            | $15-50 (AWS RDS)     |
| **Total**  | **✅ Free**   | **~$45-200**         |

**Free option**: Use Docker with local PostgreSQL, demo data only.

---

## Next Steps

1. Copy `.env.example` to `.env`
2. Fill in your API keys (see SETUP.md)
3. Run `docker-compose up`
4. Open http://localhost:3000
5. Click "Run Pipeline"
6. Watch it discover startups! 🚀

---

## Support

- **Errors?** Check `backend/logs/app.log`
- **API Issues?** Check `/docs` endpoint
- **DB Problems?** See troubleshooting above
- **More Help?** Read SETUP.md and README.md

---

**You've got this! 💪**
