# Quick Start: IPFS Auto-Restore

## 🚀 5-Minute Setup for Render Deployment

### Step 1: Backup Your Blockchain (One Time)

Run this locally:

```bash
python -c "from blockchain import PropertyBlockchain; bc = PropertyBlockchain(verbose=True); bc.backup_to_ipfs()"
```

This will:
- Upload blockchain to Pinata IPFS
- Save CID to `pinata_cid.txt` automatically
- Print the CID for your reference

### Step 2: Verify CID File

```bash
cat pinata_cid.txt
# Should show something like: QmXYZ123abc456def...
```

### Step 3: Set Environment Variables in Render

In your Render dashboard, add:
- `PINATA_API_KEY` = your Pinata API key
- `PINATA_SECRET_KEY` = your Pinata secret key

### Step 4: Deploy to Render

Push your code:
```bash
git add .
git commit -m "Add IPFS auto-restore"
git push
```

### Step 5: Done! ✅

Your server will automatically:
1. Find `pinata_cid.txt` on startup
2. Read the CID
3. Download and restore blockchain from IPFS
4. Continue normal operation

## 🔍 Check Logs

In Render logs, look for:
```
[INFO] Found Pinata CID in pinata_cid.txt: QmXYZ...
[INFO] Attempting to restore blockchain from Pinata IPFS...
[INFO] Downloaded XXXXX bytes
[INFO] ✅ Successfully auto-restored blockchain from Pinata IPFS
```

## 💡 Tips

- **First Deploy**: Make sure `pinata_cid.txt` exists before deploying
- **Updates**: Run backup again to update CID when blockchain changes
- **Testing**: Use `python test_ipfs_restore.py` to test locally

## ❓ Troubleshooting

**Q: Logs show "No pinata_cid.txt found"**
- A: Run the backup command (Step 1) to create it

**Q: IPFS restore fails**
- A: Check Pinata API keys in environment variables
- A: System will auto-fallback to other restore methods

**Q: Want to update blockchain on server?**
- A: Run backup locally, push updated `pinata_cid.txt`, redeploy

## 📚 More Info

See [`IPFS_RESTORE_GUIDE.md`](IPFS_RESTORE_GUIDE.md) for complete documentation.
