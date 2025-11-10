# Deployment Guide

## Current State

**Storage:** Chat history is stored in JSON files (`chat_history_{user_id}_{role}.json`)

**Pros:**
- ✅ Simple, no database setup needed
- ✅ Works for testing and small deployments

**Cons:**
- ⚠️ History files accumulate in project directory
- ⚠️ Not ideal for production (file system limitations)
- ⚠️ No concurrent access protection

## Deployment Options

### Option 1: Deploy as-is (JSON files) - Quick Start

**Best for:** Testing, single friend access, temporary deployment

**Steps:**
1. Deploy to any cloud service (Railway, Render, Fly.io, etc.)
2. Set environment variables:
   - `GEMINI_API_KEY=your_key`
3. That's it!

**Limitations:**
- History files will be created on server
- Files persist between restarts (good!)
- Works fine for 1-10 users

### Option 2: Add SQLite Database - Recommended

**Best for:** Production, multiple users, better scalability

**Why SQLite:**
- ✅ No separate database server needed
- ✅ File-based (easy backup)
- ✅ Handles concurrent access
- ✅ Better than JSON files

**Implementation needed:**
- Store chat history in SQLite instead of JSON
- Simple schema: `user_id`, `role`, `message`, `timestamp`

### Option 3: PostgreSQL - For Scale

**Best for:** Large scale, many concurrent users

**When to use:**
- Multiple friends/users
- High traffic expected
- Need advanced queries

## Recommendation

**For your case (one friend):**

**Start with Option 1 (JSON files)** - deploy now, works fine!

**Upgrade to Option 2 (SQLite)** if:
- You get more users
- You want better data management
- You need to query/search history

## Quick Deploy (JSON files)

### Railway.app (Easiest)

1. Push code to GitHub
2. Connect Railway to repo
3. Add env var: `GEMINI_API_KEY`
4. Deploy!

### Render.com

1. Create new Web Service
2. Connect GitHub repo
3. Build: `pip install -r requirements.txt`
4. Start: `python main.py`
5. Add env var: `GEMINI_API_KEY`

### Fly.io

```bash
fly launch
fly secrets set GEMINI_API_KEY=your_key
fly deploy
```

## Environment Variables Needed

```env
GEMINI_API_KEY=your_gemini_key
# Optional:
GEMINI_MODEL=models/gemini-2.5-flash
```

## Important Notes

1. **History files location:** They'll be created in project root on server
2. **File persistence:** Files persist between restarts (good!)
3. **Cleanup:** May want to add cleanup for old history files
4. **Backup:** Consider backing up history files if important

## Next Steps

1. **Deploy now with JSON files** - works fine for your use case
2. **Monitor usage** - see how it performs
3. **Add SQLite later** if needed (easy migration)

