# Automatic IPFS Restoration Feature

## Overview

The blockchain now automatically restores from Pinata IPFS when the server starts up, eliminating the need for database-hosted backups while supporting deployment on platforms like Render that don't provide persistent storage.

## How It Works

### 1. **Restoration Priority Order**

When `PropertyBlockchain` initializes, it attempts restoration in this order:

1. **IPFS (Pinata)** - First checks for `pinata_cid.txt` in project root
2. **Local Encrypted File** - Tries to load from `blocks/blockchain_data.encrypted`
3. **Database Backup** - Falls back to database backup (if `auto_restore=True`)
4. **New Genesis** - Creates a fresh blockchain if all above fail

### 2. **Automatic CID Storage**

When you backup to IPFS using `blockchain.backup_to_ipfs()`:
- The CID is automatically saved to `pinata_cid.txt` in the project root
- On next server startup, the blockchain will auto-restore from this CID
- No manual intervention required!

### 3. **Git Safety**

The `pinata_cid.txt` file is:
- Stored in the project root (NOT in `blocks/` folder)
- Automatically ignored by git (added to `.gitignore`)
- Never committed to your repository

## Usage

### Basic Usage (Automatic)

```python
from blockchain import PropertyBlockchain

# Simply initialize - automatic restoration happens behind the scenes
blockchain = PropertyBlockchain(verbose=True, auto_restore=True)

# Check the logs to see which method was used
for log in blockchain.logs[-10:]:
    print(log)
```

### Manual Backup to IPFS

```python
from blockchain import PropertyBlockchain

blockchain = PropertyBlockchain(verbose=True)

# Backup to Pinata IPFS
cid = blockchain.backup_to_ipfs()

if cid:
    print(f"Backup successful! CID: {cid}")
    print(f"CID automatically saved to pinata_cid.txt")
    print(f"Next server restart will auto-restore from this CID")
```

### Manual CID File Creation

If you already have a CID and want to enable auto-restore:

1. Create `pinata_cid.txt` in your project root
2. Add the CID to the file (just the CID, nothing else)
3. Next server startup will automatically restore from this CID

```bash
# Example:
echo "QmXYZ123abc..." > pinata_cid.txt
```

## Configuration

### Environment Variables

Set these in your `.env` file:

```bash
PINATA_API_KEY=your_pinata_api_key_here
PINATA_SECRET_KEY=your_pinata_secret_key_here
```

### File Location

The CID file must be named exactly:
```
pinata_cid.txt
```

And located in the project root (same directory as `app.py`).

## Logging

Enable verbose logging to see restoration details:

```python
blockchain = PropertyBlockchain(verbose=True, auto_restore=True)
```

Sample log output:
```
[INFO] Found Pinata CID in pinata_cid.txt: QmXYZ123abc...
[INFO] Attempting to restore blockchain from Pinata IPFS...
[INFO] Downloaded 45678 bytes
[INFO] Loaded 25 blocks successfully
[INFO] ✅ Successfully auto-restored blockchain from Pinata IPFS (CID: QmXYZ123abc...)
```

## Benefits

### For Render Deployment

- **No Database Required** - IPFS provides decentralized storage
- **Fast Startup** - Direct restoration from IPFS on server boot
- **Cost Effective** - Pinata free tier is sufficient for most use cases
- **Automatic** - No manual configuration after first backup

### For Development

- **Simple** - Just backup once, auto-restore forever
- **Reliable** - Falls back to other methods if IPFS fails
- **Portable** - Share CID file across team members easily

### For Production

- **Decentralized** - Data stored on IPFS, not single database
- **Immutable** - IPFS content addressing ensures data integrity
- **Redundant** - Multiple restoration methods provide safety

## Troubleshooting

### Issue: Auto-restore not working

**Check:**
1. Does `pinata_cid.txt` exist in project root?
2. Is the CID valid and not empty?
3. Are Pinata API keys set in `.env`?
4. Check logs with `verbose=True`

### Issue: CID file not created after backup

**Check:**
1. Did `backup_to_ipfs()` return a CID successfully?
2. Are Pinata credentials valid?
3. Check file permissions in project directory

### Issue: Restoration fails with CID

**Fallback:**
The system will automatically fall back to:
1. Local encrypted file (if available)
2. Database backup (if `auto_restore=True`)
3. New genesis block (as last resort)

## Testing

Test the feature with the provided script:

```bash
python test_ipfs_restore.py
```

This will:
- Check for `pinata_cid.txt`
- Initialize blockchain with auto-restore
- Show restoration logs and loaded data

## Security Notes

- The CID file contains only the IPFS hash (public)
- Actual blockchain data is encrypted before upload
- The CID is safe to share (read-only access)
- Keep your Pinata API keys secret in `.env`

## Example Workflow

### Initial Setup

```bash
# 1. Set up Pinata credentials
echo "PINATA_API_KEY=your_key" >> .env
echo "PINATA_SECRET_KEY=your_secret" >> .env

# 2. Backup your blockchain
python -c "from blockchain import PropertyBlockchain; bc = PropertyBlockchain(); bc.backup_to_ipfs()"

# 3. Verify CID file was created
cat pinata_cid.txt

# 4. Deploy to Render - it will auto-restore on startup!
```

### Regular Operation

```python
# Your Flask app (app.py)
from blockchain import PropertyBlockchain

# Initialize - automatic restoration happens here
blockchain = PropertyBlockchain(verbose=True, auto_restore=True)

# Use blockchain normally
@app.route('/properties')
def get_properties():
    return jsonify(blockchain.get_all_properties())
```

## API Reference

### New Methods

#### `_auto_restore_from_ipfs() -> bool`
Automatically called during initialization. Checks for `pinata_cid.txt` and restores from IPFS if found.

**Returns:** `True` if restoration successful, `False` otherwise

### Modified Methods

#### `backup_to_ipfs() -> Optional[str]`
Now automatically saves the returned CID to `pinata_cid.txt`.

**Returns:** IPFS CID hash if successful, `None` otherwise

## Files Modified

1. [`blockchain.py`](blockchain.py) - Added auto-restore logic
2. [`.gitignore`](.gitignore) - Added `pinata_cid.txt`
3. [`test_ipfs_restore.py`](test_ipfs_restore.py) - Test script (new)
4. [`IPFS_RESTORE_GUIDE.md`](IPFS_RESTORE_GUIDE.md) - This documentation (new)

## Support

For issues or questions:
1. Check the logs with `verbose=True`
2. Verify Pinata credentials in `.env`
3. Test with `test_ipfs_restore.py`
4. Check Pinata dashboard for CID availability
