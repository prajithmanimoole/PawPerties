# 🏗️ PawPerty Deployment & Security Notes

This document merges all essential deployment, backup, and security notes for your Property Registration Blockchain System.

---

## 🚀 Deployment Quick Start

### 1. Prepare Environment

- Ensure `.env` exists with all API keys (`SECRET_KEY`, `GEMINI_API_KEY`, `PINATA_API_KEY`, `PINATA_SECRET_KEY`).
- Never commit `.env` to Git. Use `.env.example` for reference.

### 2. Git Setup

```bash
git init
git add .
git status         # Ensure .env is NOT listed
git check-ignore .env
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

### 3. Install & Run

```bash
# Setup virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Visit [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## 🔒 Security Checklist

- [ ] Use strong, unique `SECRET_KEY`
- [ ] Change all default passwords before production
- [ ] Set `SESSION_COOKIE_SECURE = True` (requires HTTPS)
- [ ] Set `DEBUG = False` in production
- [ ] Never commit API keys or `.env` to Git
- [ ] Rotate keys if exposed
- [ ] Use separate keys for dev/prod
- [ ] Monitor logs for API errors

**Files NEVER to upload to Git:**
- `.env`, `instance/`, `blocks/`, `revenue_data.json`, `*.db`, `*.sqlite*`, `__pycache__/`, `.venv/`

---

## 🗄️ Dual Backup System (Database + IPFS)

- **Primary:** PostgreSQL database (fastest restore)
- **Secondary:** IPFS/Pinata (decentralized, immutable)
- On startup: tries DB → IPFS → local file → new blockchain
- On every save: backs up to DB and optionally to IPFS

**Env vars:**
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
PINATA_API_KEY=your_key
PINATA_SECRET_KEY=your_secret
```

---

## 🌐 Database-Free IPFS Backup (Render Free Tier)

- No DB? Uses IPFS for persistence.
- CID (Content Identifier) is saved to:
  - Render env var (`PINATA_LATEST_CID`)
  - Pinata metadata
  - GitHub Gist (optional)
  - Local file (for dev)
- On startup: finds CID, restores blockchain from IPFS.

**Env vars:**
```bash
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key
SECRET_KEY=your_secret_key
# Optional for better persistence:
RENDER_API_KEY=your_render_api_key
RENDER_SERVICE_ID=srv-xxxxx
GITHUB_TOKEN=your_github_token
GITHUB_GIST_ID=your_gist_id
PINATA_RESTORE_CID=QmXXXXX  # Manual override
```

---

## 🛠️ Mutation Bug Fix Summary

- **Issue:** Viewing property history mutated blockchain data, breaking validation.
- **Fix:** 
  - `Block.to_dict()` returns deep copies.
  - All view routes use deep copies for masking.
  - Hash calculation is deterministic.
- **Result:** Blockchain is now immutable and always validates after any view.

---

## 📝 What to Upload to Git

- All `.py` source files
- `requirements.txt`
- `README.md`
- `.env.example`
- `.gitignore`
- `templates/`, `static/`
- `SECURITY_CHECKLIST.md`, `DEPLOYMENT_GUIDE.md`

---

## 🆘 Emergency Response

If you accidentally commit sensitive data:
1. Rotate all exposed API keys immediately.
2. Remove sensitive data from Git history (`git filter-branch` or BFG).
3. Force push cleaned repo.
4. Notify team to re-clone.

---

## 📚 Resources

- [Google AI Studio](https://aistudio.google.com/app/apikey)
- [Pinata Cloud](https://pinata.cloud/)
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- See `docs/` for full backup/restore guides.

---

**Your blockchain data is now doubly protected, immutable, and production-ready!**