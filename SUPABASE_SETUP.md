# 🚀 Supabase Setup Guide

This project uses **Supabase** for cloud-hosted PostgreSQL database. No local database installation needed!

---

## ✅ Why Supabase?

- ✅ **Free tier**: 500MB database storage, unlimited API calls
- ✅ **No setup**: Database created automatically
- ✅ **Auto-scaling**: Grows with your data
- ✅ **Built-in authentication**: Ready for future features
- ✅ **REST API**: Supabase provides additional APIs (optional)
- ✅ **Backups**: Automatic daily backups

---

## 🔧 Step 1: Create Supabase Project (5 minutes)

### 1. Go to Supabase

- Navigate to https://supabase.com
- Click **"Start your project"**

### 2. Sign Up

- Use email or GitHub account
- Verify your email

### 3. Create Project

- Click **"New Project"**
- **Project Name**: `startup-radar`
- **Password**: Save it securely (you'll need it)
- **Region**: Choose closest to you (e.g., us-east-1, eu-central-1)
- Click **"Create new project"**

### 4. Wait for Setup

- Takes 1-2 minutes for Supabase to provision
- You'll see: **"Your project is ready"**

---

## 📋 Step 2: Get Connection String (2 minutes)

### 1. Click **Settings** (bottom left)

### 2. Click **Database**

### 3. Under "Connection string", click **PostgreSQL**

### 4. Copy the connection string

Should look like:

```
postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

**⚠️ Replace `[PASSWORD]` with your actual password you set earlier**

---

## 🔐 Step 3: Add to Your .env File

Edit your `.env` file:

```bash
# Before:
DATABASE_URL=postgresql://postgres:[YOUR_SUPABASE_PASSWORD]@aws-0-[YOUR_REGION].pooler.supabase.com:5432/postgres

# After (replace with actual values):
DATABASE_URL=postgresql://postgres.abc123xyz:[myPassword123!]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

**Example:**

```
DATABASE_URL=postgresql://postgres.xyzabc:[SecurePass123!]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

---

## ✨ Step 4: Start Your Application

### Local Development

```bash
cd backend
uvicorn main:app --reload
```

**You should see:**

```
✅ Database initialized successfully
✅ Database connection verified
Tables in database: ['companies', 'dedup_logs', 'fetch_logs', 'alerts']
```

### Docker Compose

```bash
# From project root
docker-compose up --build
```

---

## 🔍 Step 5: Verify Database

### Via Supabase Dashboard

1. Go to https://supabase.com
2. Select your project
3. Click **SQL Editor** (left sidebar)
4. Run query:
   ```sql
   SELECT * FROM companies LIMIT 5;
   ```

### Via Command Line

```bash
# Install psql if needed, then:
psql "postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres" \
  -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
```

Should show 4 tables:

- `companies`
- `dedup_logs`
- `fetch_logs`
- `alerts`

---

## 🆚 Connection Methods

Supabase offers **two connection methods**:

### 1. **Direct Connection** (What we use)

- Port: `5432`
- URL: `postgresql://postgres.[id]:[pass]@aws-0-[region].pooler.supabase.com:5432/postgres`
- Best for: Application servers, batch jobs

### 2. **Connection Pooler** (Optional)

- Port: `6543`
- URL: `postgresql://postgres.[id]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres`
- Best for: High-frequency connections, serverless

We use the **direct connection (port 5432)** which is simpler and sufficient.

---

## 📊 Database Management

### Supabase Dashboard

Access your database dashboard:

1. Go to your Supabase project
2. Click **SQL Editor**
3. Pre-built queries available
4. Create custom queries

### Tables Created Automatically

| Table        | Purpose                    |
| ------------ | -------------------------- |
| `companies`  | Funded startup data        |
| `dedup_logs` | Deduplication audit trail  |
| `fetch_logs` | Pipeline execution history |
| `alerts`     | Email alert tracking       |

---

## 🚨 Common Issues

### Issue: "Connection refused"

**Solution**: Check that DATABASE_URL in `.env` is correct

- Verify password is correct
- Verify region matches your project
- Verify no typos

### Issue: "FATAL: password authentication failed"

**Solution**:

1. Go to Supabase Dashboard
2. Click Settings → Database
3. Click "Reset database password"
4. Update your `.env` with new password

### Issue: "SSL certificate problem"

**Solution**: Already handled in our code (sslmode=require)

- Make sure you're using latest Python psycopg2

### Issue: Database still empty after running pipeline

**Solution**:

1. Check that API keys are set in `.env`
2. Check backend logs: `uvicorn main:app --reload`
3. Verify DATABASE_URL is accessible: `psql [CONNECTION_STRING]`

---

## 🔄 Backups & Safety

Supabase automatically:

- ✅ Creates daily backups
- ✅ Keeps 7 days of backups (free tier)
- ✅ Allows 1-click restore

To restore:

1. Go to Project Settings
2. Click Backups
3. Choose backup date
4. Click Restore

---

## 🚀 Deploying to Production

When you deploy your Docker image:

1. **Set environment variable**:

   ```bash
   export DATABASE_URL="postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres"
   ```

2. **On AWS/GCP/Azure**:
   - Add DATABASE_URL to environment variables
   - Tables create automatically on first run

3. **Scale with confidence**:
   - Multiple API replicas can connect to same Supabase DB
   - Connection pooling built-in
   - Auto-scaling as needed

---

## 💰 Pricing

### Free Tier (Enough for MVP)

- 500MB storage
- Unlimited API calls
- Daily backups for 7 days
- Support via community forum

### Pro Tier ($25/month)

- 8GB storage
- 100GB bandwidth
- 24/7 email support
- Advanced security

---

## 📚 Useful Resources

- **Supabase Docs**: https://supabase.com/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Connection Strings**: https://supabase.com/docs/guides/database/connecting-to-postgres
- **Database Functions**: https://supabase.com/docs/guides/database/functions

---

## ✅ Checklist

- [ ] Supabase account created
- [ ] Project created
- [ ] Database password saved securely
- [ ] Connection string copied
- [ ] `.env` file updated with DATABASE_URL
- [ ] Backend started and connected
- [ ] Tables created (4 tables visible)
- [ ] Dashboard accessible at http://localhost:3000
- [ ] API health check passing at http://localhost:8000/health

---

## 🎉 You're Ready!

Your application now uses Supabase for cloud-hosted PostgreSQL. No local database maintenance needed!

```bash
# Start your app
uvicorn main:app --reload

# Or with Docker
docker-compose up

# Open dashboard
http://localhost:3000
```

Happy building! 🚀
