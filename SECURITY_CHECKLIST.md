# Security Checklist for Deployment

Before deploying your Property Registration Blockchain System, ensure you have completed the following:

## ✅ Environment Variables

- [ ] Created `.env` file with all required API keys
- [ ] Set `SECRET_KEY` to a strong random value (not the default)
- [ ] Set `GEMINI_API_KEY` with your actual Google AI Studio API key
- [ ] Set `PINATA_API_KEY` with your Pinata API key
- [ ] Set `PINATA_SECRET_KEY` with your Pinata secret key
- [ ] Verified `.env` is listed in `.gitignore`

## ✅ Files NOT to Upload to Git

The following files/folders should NEVER be committed to Git:
- `.env` - Contains your API keys and secrets
- `.venv/` or `venv/` - Virtual environment (too large, can be recreated)
- `instance/` - Contains database files
- `blocks/` - Contains blockchain backup files
- `revenue_data.json` - Contains production/test data
- `*.db`, `*.sqlite`, `*.sqlite3` - Database files
- `__pycache__/` - Python cache files

All of these are already in your `.gitignore` file.

## ✅ Production Setup

- [ ] Change default admin password (`admin123`) in production
- [ ] Change default officer password (`officer123`) in production
- [ ] Set `SESSION_COOKIE_SECURE = True` in config.py (requires HTTPS)
- [ ] Set `DEBUG = False` in config.py for production
- [ ] Use a production-grade WSGI server (like gunicorn) instead of Flask dev server

## ✅ API Key Security

- [ ] Never share your `.env` file
- [ ] Never commit API keys to version control
- [ ] Rotate API keys if they are accidentally exposed
- [ ] Use separate API keys for development and production
- [ ] Set up API key usage limits/alerts on provider dashboards

## ✅ Deployment

- [ ] Set environment variables on your hosting platform
- [ ] Test that the application loads environment variables correctly
- [ ] Verify the application fails gracefully if API keys are missing
- [ ] Monitor application logs for any API key errors

## 📝 What to Upload to Git

You SHOULD upload these files:
- All `.py` source files (app.py, blockchain.py, config.py, etc.)
- `requirements.txt`
- `README.md`
- `.env.example` (example environment file without real secrets)
- `.gitignore`
- `templates/` folder
- `static/` folder

## 🔒 Emergency Response

If you accidentally commit sensitive data:
1. Immediately rotate all exposed API keys
2. Use `git filter-branch` or BFG Repo-Cleaner to remove sensitive data from Git history
3. Force push the cleaned repository
4. Notify all team members to re-clone the repository

## 📚 Additional Resources

- [Google AI Studio](https://aistudio.google.com/app/apikey) - Get Gemini API key
- [Pinata Cloud](https://pinata.cloud/) - Get IPFS API keys
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
