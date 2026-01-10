# Virtual Environment Guide

## What is a Virtual Environment?

A virtual environment is an **isolated Python environment** for your project. It keeps your project's dependencies separate from:
- Your system Python installation
- Other Python projects on your computer

Think of it as a "sandbox" for your project's packages.

## Why Use Virtual Environments?

✅ **Prevent conflicts:** Different projects can use different package versions
✅ **Clean dependencies:** Only install what you need for this project
✅ **Easy deployment:** Recreate the exact same environment anywhere
✅ **No system pollution:** Don't clutter your system Python with project packages

## Your Project Structure

This project uses `.venv/` as the virtual environment folder (notice the dot at the start).

```
PawParties/
├── .venv/              ← Virtual environment (ignored by Git)
├── .env                ← API keys (ignored by Git)
├── app.py              ← Your code (tracked by Git)
├── requirements.txt    ← Package list (tracked by Git)
└── ...other files
```

## How to Use

### Activate the Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

**You'll see `(.venv)` appear in your terminal prompt when activated.**

### Install Packages (with venv activated)
```bash
pip install -r requirements.txt
```

All packages install into `.venv/` folder, not your system Python.

### Deactivate (when done working)
```bash
deactivate
```

## Common Questions

**Q: Why are there multiple venv folders mentioned in .gitignore?**
A: Different developers use different naming conventions:
- `.venv/` - Common in VS Code and modern Python
- `venv/` - Traditional Python convention
- `env/`, `ENV/` - Alternative names

The `.gitignore` covers all variants, but **you only need ONE** - this project uses `.venv/`

**Q: Should I commit the .venv folder to Git?**
A: **NO!** Virtual environments are:
- Too large (100s of MB)
- Machine-specific (Windows vs Linux paths differ)
- Easy to recreate with `pip install -r requirements.txt`

**Q: What if someone else clones my repo?**
A: They create their own virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Q: How do I know if my venv is activated?**
A: Look for `(.venv)` at the start of your terminal prompt:
```bash
(.venv) D:\Googlethon\PawParties>
```

**Q: Can I delete .venv and recreate it?**
A: Yes! It's safe to delete:
```bash
# Delete the folder
rmdir /s .venv  # Windows
# rm -rf .venv  # Linux/Mac

# Recreate it
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Best Practices

✅ **DO:**
- Always activate venv before working on the project
- Keep `requirements.txt` updated when adding packages
- Add venv folders to `.gitignore`

❌ **DON'T:**
- Install packages without activating venv
- Commit the venv folder to Git
- Share your venv folder with others

## Quick Reference

```bash
# Activate
.venv\Scripts\activate           # Windows
source .venv/bin/activate        # Linux/Mac

# Install packages
pip install package-name

# Save dependencies
pip freeze > requirements.txt

# Deactivate
deactivate
```
