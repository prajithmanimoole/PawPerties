# Deployment Guide

## Quick Start for Git Upload

### Step 1: Verify Your .env File
Make sure your `.env` file exists and contains your API keys:
```bash
# Check if .env exists
dir .env

# If it doesn't exist, copy from .env.example
copy .env.example .env
```

Then edit `.env` with your actual API keys.

### Step 2: Initialize Git Repository
```bash
# Initialize git
git init

# Add all files (sensitive files are automatically excluded by .gitignore)
git add .

# Check what will be committed (make sure .env is NOT listed)
git status

# Verify .env is ignored
git check-ignore .env
# Should output: .env
```

### Step 3: Commit Your Code
```bash
# Commit the changes
git commit -m "Initial commit: Property Registration Blockchain System"
```

### Step 4: Push to Remote Repository
```bash
# Add your remote repository (replace with your GitHub URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Files That Will Be Uploaded

✅ **These files WILL be uploaded:**
- All `.py` source files (app.py, blockchain.py, etc.)
- `requirements.txt`
- `README.md`
- `.env.example` (example without real secrets)
- `.gitignore`
- `templates/` folder
- `static/` folder
- `SECURITY_CHECKLIST.md`
- `DEPLOYMENT_GUIDE.md`

❌ **These files will NOT be uploaded (automatically excluded):**
- `.env` (your actual API keys)
- `instance/` (database folder)
- `blocks/` (blockchain backups)
- `revenue_data.json` (data files)
- `*.db`, `*.sqlite` (database files)
- `__pycache__/` (Python cache)

## Setting Up on a New Machine / Server

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

### 2. Set Up Virtual Environment

**For this project (already has .venv):**
```bash
# Activate the existing virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

**For fresh setup (if .venv doesn't exist):**
```bash
# Create a new virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

**What is a Virtual Environment?**
A virtual environment is an isolated Python environment that keeps your project's dependencies separate from your system Python. This prevents version conflicts between different projects.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Copy the example file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env and add your actual API keys
notepad .env  # Windows
# nano .env  # Linux/Mac
```

Required variables:
- `SECRET_KEY` - Generate a strong random key
- `GEMINI_API_KEY` - From https://aistudio.google.com/app/apikey
- `PINATA_API_KEY` - From https://pinata.cloud/
- `PINATA_SECRET_KEY` - From https://pinata.cloud/

### 5. Run the Application
```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## Production Deployment

### Environment Variables on Hosting Platforms

Different platforms have different ways to set environment variables:

**Heroku:**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set GEMINI_API_KEY=your-gemini-key
heroku config:set PINATA_API_KEY=your-pinata-key
heroku config:set PINATA_SECRET_KEY=your-pinata-secret
```

**Render / Railway / Fly.io:**
- Use their web dashboard to add environment variables
- Or use their CLI tools

**AWS / Google Cloud / Azure:**
- Set environment variables in the service configuration
- Or use secrets management services (AWS Secrets Manager, Google Secret Manager, Azure Key Vault)

### Production Checklist

Before going live:
1. ✅ Change all default passwords
2. ✅ Set `DEBUG = False` in config.py
3. ✅ Set `SESSION_COOKIE_SECURE = True` (requires HTTPS)
4. ✅ Use production WSGI server (gunicorn)
5. ✅ Set up SSL/HTTPS
6. ✅ Enable firewall rules
7. ✅ Set up database backups
8. ✅ Monitor application logs
9. ✅ Set API rate limits

### Using Gunicorn (Production Server)
```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Troubleshooting

### "No module named 'dotenv'"
```bash
pip install python-dotenv
```

### "Gemini AI not working"
Check if `GEMINI_API_KEY` is set:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Key set:', bool(os.environ.get('GEMINI_API_KEY')))"
```

### "Pinata backup failing"
Check if Pinata keys are set:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', bool(os.environ.get('PINATA_API_KEY'))); print('Secret:', bool(os.environ.get('PINATA_SECRET_KEY')))"
```

## Security Notes

- ⚠️ NEVER commit your `.env` file to Git
- ⚠️ NEVER share your API keys publicly
- ⚠️ Rotate API keys immediately if exposed
- ⚠️ Use different API keys for dev/staging/production
- ⚠️ Enable API usage alerts on provider dashboards

## Support

For issues or questions:
1. Check the `SECURITY_CHECKLIST.md` file
2. Review the `README.md` documentation
3. Verify environment variables are set correctly
4. Check application logs for errors
