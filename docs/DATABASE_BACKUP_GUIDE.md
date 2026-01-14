# Database Backup & Restore System

## Overview

Your PawParties blockchain system now uses a **dual-backup strategy** for maximum data reliability:

1. **Primary Backup: PostgreSQL Database** (fast, reliable, always available)
2. **Secondary Backup: IPFS/Pinata** (decentralized, immutable, off-site)

## How It Works

### Automatic Backup (On Every Save)

When blockchain data is saved, the system automatically:

1. ✅ Saves encrypted blockchain to local file
2. ✅ Backs up to PostgreSQL database
3. ✅ Optionally backs up to IPFS/Pinata

**No manual intervention required!**

### Automatic Restore (On Server Startup)

The system tries to restore in this priority order:

1. **PostgreSQL Database** - Fastest and most reliable
2. **IPFS/Pinata** - Falls back if database is empty
3. **Local File** - Falls back if IPFS unavailable
4. **Genesis Block** - Creates new blockchain if nothing found

## Benefits

### PostgreSQL Database Backup

✅ **Instant Restoration** - No network delays  
✅ **Always Available** - Part of your Render infrastructure  
✅ **Version History** - Multiple backups with timestamps  
✅ **Reliable** - Managed database with automatic backups  
✅ **Fast** - Direct database connection  

### IPFS Backup (Secondary)

✅ **Decentralized** - Data stored on IPFS network  
✅ **Immutable** - Cannot be tampered with  
✅ **Off-site** - Geographic redundancy  
✅ **Free** - Using Pinata free tier  

## Configuration

### Environment Variables

```bash
# PostgreSQL Database (Primary Backup)
DATABASE_URL=postgresql://user:password@host:port/database

# IPFS/Pinata (Secondary Backup)
PINATA_API_KEY=your_api_key
PINATA_SECRET_KEY=your_secret_key

# Optional: Render API for CID persistence
RENDER_API_KEY=your_render_api_key
RENDER_SERVICE_ID=srv-xxxxx
```

## Usage

### Viewing Backups

To see all database backups:

```python
from models import BlockchainBackup

# List all backups
backups = BlockchainBackup.query.order_by(BlockchainBackup.created_at.desc()).all()
for backup in backups:
    print(f"ID: {backup.id}, Name: {backup.name}, Created: {backup.created_at}")
```

### Manual Database Backup

```python
from blockchain import PropertyBlockchain

blockchain = PropertyBlockchain()
blockchain.backup_to_database(admin_id=1, backup_name="Manual Backup Before Update")
```

### Manual Database Restore

```python
from blockchain import PropertyBlockchain

blockchain = PropertyBlockchain()

# Restore from latest backup
blockchain.restore_from_database()

# Or restore from specific backup ID
blockchain.restore_from_database(backup_id=42)
```

### Manual IPFS Backup

```python
from blockchain import PropertyBlockchain

blockchain = PropertyBlockchain()
cid = blockchain.backup_to_ipfs()
print(f"Backed up to IPFS: {cid}")
```

## Database Schema

The `blockchain_backups` table stores:

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Backup display name |
| filename | String | Original filename reference |
| backup_data | Text | Encrypted blockchain data |
| created_at | DateTime | Backup timestamp |
| created_by | Integer | User ID who created backup |

## Monitoring

### On Render Deployment

Check Render logs for:

```
✓ Running on Render deployment
🔄 Initializing blockchain with auto-restore...
   Priority 1: PostgreSQL database (fastest)
   Priority 2: IPFS/Pinata backup
   Priority 3: Local encrypted file
✅ Blockchain successfully restored!
   Total blocks: 42
   Total properties: 10
✓ PostgreSQL database detected
   Auto-backup to database enabled
   Database restoration is primary recovery method
```

### Backup Confirmation

Every time data is saved, you should see:

```
Blockchain saved to read-only encrypted file: blocks/blockchain_data.encrypted
✅ Blockchain backed up to database!
   Backup ID: 123
   Name: Auto-backup 2026-01-14 15:30:45
   Size: 45678 bytes
   Blocks: 42
```

## Troubleshooting

### Database Backup Not Working

**Problem**: No database backups being created

**Solutions**:
1. Check `DATABASE_URL` is set correctly
2. Verify PostgreSQL is accessible
3. Check database tables exist (run migrations)
4. Look for errors in application logs

### Database Restore Failing

**Problem**: Cannot restore from database

**Solutions**:
1. Check if backups exist: `BlockchainBackup.query.count()`
2. Verify backup data is not corrupted
3. Try restoring from specific backup ID
4. Fall back to IPFS restore if needed

### IPFS Backup Not Working

**Problem**: IPFS backups failing

**Solutions**:
1. Verify `PINATA_API_KEY` and `PINATA_SECRET_KEY` are set
2. Check Pinata dashboard for API key status
3. Verify API key has `pinFileToIPFS` permission
4. Check network connectivity

## Migration from IPFS-Only System

Your system will automatically work with the new dual-backup approach. No migration needed!

**First Deployment After Update**:
1. System tries to restore from database (empty on first run)
2. Falls back to IPFS (your existing backups)
3. Restores successfully from IPFS
4. Immediately creates database backup
5. Future restores will use database (much faster!)

## Best Practices

1. **Monitor Logs** - Check that both backups are succeeding
2. **Test Restores** - Periodically verify restoration works
3. **Keep IPFS Active** - Maintain IPFS as secondary backup
4. **Database Maintenance** - Regularly check database health
5. **Clean Old Backups** - Archive old backups to save space

## Recovery Scenarios

### Scenario 1: Server Reboot (Normal Operation)
- ✅ Restores from PostgreSQL database instantly
- ⚡ Fast startup (< 1 second)

### Scenario 2: Database Corruption
- ⚠️ Database restore fails
- ✅ Falls back to IPFS restore
- ⚡ Slower but still works (3-10 seconds)

### Scenario 3: Both Database and IPFS Fail
- ⚠️ All restores fail
- ✅ Uses local encrypted file if available
- 📝 Manual recovery may be needed

### Scenario 4: Fresh Deployment
- ℹ️ No backups available
- ✅ Creates new blockchain with genesis block
- 📝 Normal for first deployment

## Manual Recovery

If automatic restore fails, you can manually restore:

### From Database Backup

```python
# In Python shell or script
from app import app
from blockchain import PropertyBlockchain
from models import db

with app.app_context():
    blockchain = PropertyBlockchain()
    
    # List available backups
    from models import BlockchainBackup
    backups = BlockchainBackup.query.all()
    for b in backups:
        print(f"{b.id}: {b.name} - {b.created_at}")
    
    # Restore specific backup
    blockchain.restore_from_database(backup_id=123)
```

### From IPFS Backup

```python
from blockchain import PropertyBlockchain

blockchain = PropertyBlockchain()
blockchain.restore_from_ipfs("QmYourCIDHere")
```

## Maintenance

### Clean Old Backups (Optional)

To prevent database from growing too large:

```python
from models import BlockchainBackup, db
from datetime import datetime, timedelta

# Keep only backups from last 30 days
cutoff_date = datetime.utcnow() - timedelta(days=30)
old_backups = BlockchainBackup.query.filter(BlockchainBackup.created_at < cutoff_date).all()

print(f"Found {len(old_backups)} old backups to delete")
for backup in old_backups:
    db.session.delete(backup)
db.session.commit()
```

## Security

- All backups are **encrypted** using the same encryption as local files
- Database backups inherit PostgreSQL security
- IPFS backups are public but encrypted (data is unreadable without encryption key)
- Never commit encryption keys or database credentials to Git

## Support

For issues or questions:
1. Check Render deployment logs
2. Review this documentation
3. Test restore manually
4. Check database connectivity
5. Verify IPFS API keys

---

**Built for reliability, speed, and redundancy.** 🚀
