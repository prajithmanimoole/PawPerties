# Database-Free IPFS Backup & Restore Solution

## Overview

This solution provides persistent blockchain data storage for Render deployments **without requiring any database connection**. When the Render server restarts, all property data is automatically restored from IPFS.

## The Problem

- Render's free tier has an ephemeral filesystem (data is lost on restart)
- No database is connected or available
- Need to persist blockchain data across server restarts

## The Solution

We use **IPFS (via Pinata)** for decentralized storage and multiple methods to persist the CID (Content Identifier) without a database:

1. **Render Environment Variables** (updated via Render API)
2. **Pinata Metadata** (searchable tags on uploads)
3. **GitHub Gist** (optional external backup)
4. **Local Files** (for development)

## Quick Start

### 1. Run Setup Script

```bash
python setup_render.py
```

This interactive script will:
- Generate a secure secret key
- Configure Pinata API keys
- Set up Render API (optional but recommended)
- Configure GitHub Gist backup (optional)
- Create `.env` file with all settings

### 2. Get Required API Keys

#### Pinata (Required)
1. Sign up free at [pinata.cloud](https://pinata.cloud)
2. Create API key with permissions: `pinFileToIPFS`, `pinList`, `hashMetadata`

#### Render API (Recommended)
1. Go to Render Dashboard → Account Settings → API Keys
2. Create new API key
3. Get service ID from your service URL (e.g., `srv-xxxxx`)

#### GitHub Gist (Optional)
1. Create personal access token with `gist` scope
2. Create a new Gist and copy its ID

### 3. Deploy to Render

```bash
git add .
git commit -m "Add database-free IPFS backup"
git push origin main
```

## How It Works

### On Server Shutdown
```
1. Blockchain data is encrypted
2. Uploaded to IPFS via Pinata
3. CID is saved to:
   - Render env var (PINATA_LATEST_CID)
   - Pinata metadata tags
   - GitHub Gist (if configured)
   - Local files
```

### On Server Startup
```
1. CID Manager checks all sources for latest CID
2. Downloads data from IPFS using CID
3. Decrypts and restores blockchain
4. Verifies integrity
5. Application starts with all data intact
```

## Key Components

### 1. `cid_manager.py`
Handles CID persistence without database:
- Saves CID to multiple sources
- Retrieves CID with fallback priority
- No database dependency

### 2. `scripts/render_startup.py`
Runs on server startup:
- Checks CID storage configuration
- Triggers blockchain restoration
- Provides detailed logging

### 3. Auto-Backup on Shutdown
Uses `atexit` hook to automatically backup when server stops

## Environment Variables

```bash
# Required
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key
SECRET_KEY=your_secret_key

# Recommended (for better persistence)
RENDER_API_KEY=your_render_api_key
RENDER_SERVICE_ID=srv-xxxxx

# Optional
GITHUB_TOKEN=your_github_token
GITHUB_GIST_ID=your_gist_id
GEMINI_API_KEY=your_gemini_key

# Emergency Recovery
PINATA_RESTORE_CID=QmXXXXX  # Manual CID override
```

## Monitoring

Check Render logs for:
```
✓ Running on Render deployment
✓ Found CID in Render environment: QmXXX...
✅ Blockchain successfully restored!
   Total blocks: 42
   Total properties: 10
```

## Troubleshooting

### No data after restart?
1. Check if Pinata API keys are correct
2. Verify CID was saved on last shutdown
3. Check Pinata dashboard for uploads
4. Set `PINATA_RESTORE_CID` manually if needed

### CID not saving?
1. Ensure at least one persistence method is configured
2. Check Render API credentials
3. Verify Pinata API key permissions

### Manual Recovery
1. Find CID from:
   - Render logs
   - Pinata dashboard (look for `PawParties_Backup_*`)
   - GitHub Gist
2. Set `PINATA_RESTORE_CID=<your_cid>` in Render
3. Restart service

## Advantages

✅ **No Database Required** - Zero database costs  
✅ **Multiple Redundancy** - 4 different storage methods  
✅ **Fully Automatic** - No manual intervention  
✅ **Cost-Free** - Uses only free tier services  
✅ **Decentralized** - Data stored on IPFS  
✅ **Encrypted** - All data is encrypted before upload  

## File Structure

```
PawParties/
├── cid_manager.py           # CID persistence without database
├── scripts/
│   └── render_startup.py    # Startup restoration script
├── setup_render.py          # Interactive setup helper
├── .env                     # Environment variables (git-ignored)
├── render.yaml              # Render deployment config
└── docs/
    └── IPFS_BACKUP_RESTORE.md  # Detailed documentation
```

## Testing Locally

```bash
# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the app
python app.py

# Add some properties
# Restart and verify data persists
```

## Support

If restoration fails:
1. Check all environment variables are set
2. Verify Pinata uploads are successful
3. Look for CID in multiple sources
4. Use manual recovery with PINATA_RESTORE_CID

## Conclusion

This solution provides reliable, database-free data persistence for Render deployments using IPFS and multiple CID storage methods. Your blockchain data will automatically persist across server restarts without any database dependency.