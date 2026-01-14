# IPFS Backup and Restore Documentation (Database-Free)

## Overview

This document explains how the PawParties property registration system handles automatic backup and restoration of blockchain data using IPFS (InterPlanetary File System) through Pinata, ensuring data persistence even when the Render server restarts - **without requiring any database**.

## Problem Statement

When deployed on Render's free tier:
- The server automatically spins down after periods of inactivity
- The filesystem is ephemeral - all local files are lost on restart
- Without proper backup, all blockchain data (property records) would be lost
- **No database is available or connected**

## Solution Architecture

### Database-Free CID Persistence

Since there's no database, we use multiple methods to persist the IPFS CID:

1. **Render Environment Variables** (via Render API)
2. **Pinata Metadata** (search by project tags)
3. **GitHub Gist** (optional backup)
4. **Local Files** (for development)

### 1. Automatic IPFS Backup on Shutdown

When the server is shutting down (detected via `atexit` hook):

1. **IPFS Upload**: The blockchain is uploaded to IPFS via Pinata API
2. **CID Storage**: The IPFS Content Identifier (CID) is saved to:
   - Render environment variable `PINATA_LATEST_CID` (via API)
   - Pinata metadata (tagged with the upload)
   - GitHub Gist (if configured)
   - Local file `latest_cid.txt` (for local development)

### 2. Automatic Restoration on Startup

When the server starts up, the restoration priority is:

1. **Render Environment Variable**: Check `PINATA_LATEST_CID`
2. **Pinata Metadata Search**: Query Pinata for latest backup by metadata
3. **GitHub Gist**: Check configured Gist for CID
4. **Local Backup File**: Check `.render_cid_backup.json`
5. **Fallback**: Check `PINATA_RESTORE_CID` environment variable
6. **Download from IPFS**: Use the CID to fetch and restore blockchain data

## Configuration

### Required Environment Variables

Set these in your Render dashboard under Environment Variables:

```bash
# Pinata IPFS Configuration (REQUIRED)
PINATA_API_KEY=your_pinata_api_key_here
PINATA_SECRET_KEY=your_pinata_secret_api_key_here

# Render API Configuration (RECOMMENDED for automatic CID updates)
RENDER_API_KEY=your_render_api_key_here
RENDER_SERVICE_ID=your_render_service_id_here

# GitHub Gist Configuration (OPTIONAL backup method)
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_GIST_ID=your_gist_id_here

# Manual Restore Override (OPTIONAL - for emergency recovery)
PINATA_RESTORE_CID=QmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Application secrets
SECRET_KEY=your_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here  # Optional for AI chatbot
```

### Getting Required API Keys

#### 1. Pinata API Keys (Required)
1. Sign up for free at [Pinata Cloud](https://pinata.cloud)
2. Go to API Keys section
3. Create a new API key with these permissions:
   - `pinFileToIPFS`
   - `pinList`
   - `hashMetadata`
4. Copy the API Key and Secret Key

#### 2. Render API Key (Recommended)
1. Go to your Render dashboard
2. Navigate to Account Settings → API Keys
3. Create a new API key
4. Get your service ID from the service URL (e.g., `srv-xxxxx`)

#### 3. GitHub Personal Access Token (Optional)
1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate a new token with `gist` scope
3. Create a new Gist and copy its ID from the URL

## How It Works

### CID Manager

The `cid_manager.py` module handles CID persistence without a database:

```python
class CIDManager:
    def save_cid(cid, metadata):
        # Saves to multiple sources:
        # 1. Render env var via API
        # 2. Pinata metadata
        # 3. GitHub Gist
        # 4. Local files
    
    def get_latest_cid():
        # Retrieves from sources in priority order
        # Returns the first CID found
```

### Backup Process (On Shutdown)

```python
# app.py - auto_backup_on_shutdown()
1. Get encrypted blockchain data
2. Upload to IPFS via Pinata API
3. Receive CID (Content Identifier)
4. Save CID using CIDManager:
   - Update PINATA_LATEST_CID env var via Render API
   - Tag the Pinata upload with metadata
   - Update GitHub Gist (if configured)
   - Save to local files
```

### Restore Process (On Startup)

```python
# blockchain.py - _auto_restore_from_ipfs()
1. Use CIDManager to get latest CID:
   - Check PINATA_LATEST_CID env var
   - Search Pinata by metadata tags
   - Check GitHub Gist
   - Check local backup files
2. Download blockchain data from IPFS using CID
3. Decrypt and restore blockchain
4. Verify blockchain integrity
```

## Render Deployment Setup

### 1. Update render.yaml

```yaml
services:
  - type: web
    name: pawperties-app
    env: python
    region: oregon
    plan: free
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/render_startup.py && gunicorn app:app --bind 0.0.0.0:$PORT
    healthCheckPath: /
    envVars:
      - key: SECRET_KEY
        sync: false
      - key: PINATA_API_KEY
        sync: false
      - key: PINATA_SECRET_KEY
        sync: false
      - key: RENDER_API_KEY
        sync: false
      - key: RENDER_SERVICE_ID
        sync: false
```

### 2. Deploy to Render

```bash
git add .
git commit -m "Add database-free IPFS backup/restore for Render"
git push origin main
```

## Manual Operations

### Force Backup to IPFS

Admin users can manually trigger IPFS backup:
1. Login as admin
2. Go to `/admin/blockchain`
3. Click "Backup to IPFS"
4. The CID will be automatically saved to all configured storage methods

### Force Restore from IPFS

Admin users can restore from a specific CID:
1. Login as admin
2. Go to `/admin/blockchain`
3. Enter the CID in "Restore from IPFS" section
4. Click "Restore"

### Emergency Recovery

If automatic restoration fails:
1. Find the last known good CID from:
   - Render dashboard logs
   - Pinata dashboard
   - GitHub Gist
   - Local backup files
2. Set `PINATA_RESTORE_CID` environment variable in Render
3. Restart the service

## Monitoring and Debugging

### Check Restoration Status

The startup script logs detailed information:

```
RENDER STARTUP RESTORE PROCESS
===============================
✓ Running on Render deployment
🔄 Initializing blockchain with auto-restore...
Found CID in Render environment: QmXXX...
✅ Blockchain successfully restored!
   Total blocks: 42
   Total properties: 10
   ✓ Blockchain integrity verified

📝 CID Persistence Methods:
   ✓ Render environment variables (via API)
   ✓ Pinata metadata search
   ✓ GitHub Gist backup
   ✓ Local file backup (for development)
```

### Troubleshooting

#### Issue: Data not persisting after restart

**Check:**
1. Verify PINATA_API_KEY and PINATA_SECRET_KEY are set correctly
2. Check if RENDER_API_KEY and RENDER_SERVICE_ID are configured
3. Look for CID save errors in shutdown logs
4. Verify at least one persistence method is working

**Solution:**
- Ensure at least Pinata API keys are configured
- Optionally add Render API keys for better persistence
- Check Pinata dashboard to verify uploads are successful

#### Issue: "No IPFS CID found"

**Causes:**
- First deployment (no previous backups)
- All persistence methods failed
- CID was not saved properly on last shutdown

**Solution:**
1. Check Pinata dashboard for recent uploads
2. Look for files with metadata: `type=blockchain_backup`, `project=PawParties`
3. Copy the CID and set `PINATA_RESTORE_CID` environment variable
4. Restart the service

#### Issue: Render API not updating environment variables

**Check:**
1. RENDER_API_KEY is valid
2. RENDER_SERVICE_ID matches your service
3. API key has proper permissions

**Solution:**
- Regenerate Render API key
- Verify service ID from Render dashboard URL
- Use Pinata metadata search as fallback

## How Each Storage Method Works

### 1. Render Environment Variables (via API)

```python
# Saves CID to PINATA_LATEST_CID env var
# Uses Render API to update programmatically
# Persists across restarts
# Requires RENDER_API_KEY and RENDER_SERVICE_ID
```

### 2. Pinata Metadata Search

```python
# Tags each upload with metadata:
{
    "type": "blockchain_backup",
    "project": "PawParties",
    "latest": "true",
    "timestamp": "2024-01-01T00:00:00"
}
# Searches for latest backup by querying metadata
# Works as long as files remain pinned
```

### 3. GitHub Gist (Optional)

```python
# Stores CID in a JSON file in a Gist
# Updates via GitHub API
# Provides external backup
# Requires GITHUB_TOKEN and GITHUB_GIST_ID
```

### 4. Local Files

```python
# latest_cid.txt - Simple text file with CID
# .render_cid_backup.json - JSON with history
# Works for local development
# Lost on Render restart (ephemeral filesystem)
```

## Best Practices

1. **Configure Multiple Methods**: Use at least 2 persistence methods for redundancy
2. **Monitor Pinata Usage**: Free tier has limits; monitor your usage
3. **Keep CID Records**: Document important CIDs outside the system
4. **Test Recovery**: Periodically test restoration with known CIDs
5. **Regular Backups**: Admin should trigger manual backups before major changes

## Cost Considerations

All services used offer free tiers:

- **Pinata Free Tier**: 1GB storage, 100 uploads/month
- **Render Free Tier**: Unlimited env vars, API calls
- **GitHub**: Unlimited public Gists
- **No Database Required**: $0 database costs

## Security Notes

1. **Encryption**: All blockchain data is encrypted before upload to IPFS
2. **API Keys**: Store all API keys as environment variables, never in code
3. **Access Control**: Only admin users can trigger manual backup/restore
4. **IPFS Public**: Data on IPFS is public but encrypted

## Advantages of This Approach

✅ **No Database Required** - Completely database-free solution  
✅ **Multiple Redundancy** - 4 different storage methods  
✅ **Zero Cost** - Uses only free tier services  
✅ **Automatic** - No manual intervention needed  
✅ **Resilient** - Works even if some methods fail  
✅ **Simple** - No complex database setup or management  

## Conclusion

This database-free IPFS backup/restore system ensures that your blockchain data persists across Render server restarts without requiring any database connection. The multi-layered approach provides redundancy and reliability while keeping costs at zero.