#!/usr/bin/env python3
"""
Render Startup Script
This script runs on Render server startup to ensure blockchain data is restored from IPFS
"""

import os
import sys
import time
from datetime import datetime

# Add parent directory to path to import blockchain module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import CID manager
from cid_manager import cid_manager


def startup_restore():
    """
    Perform startup restoration tasks for Render deployment
    """
    print("\n" + "=" * 60)
    print("RENDER STARTUP RESTORE PROCESS")
    print("=" * 60)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Import blockchain module
        from blockchain import PropertyBlockchain

        # Check if we're on Render (environment variable set by Render)
        is_render = os.environ.get("RENDER", False) or os.environ.get(
            "IS_PULL_REQUEST", False
        )

        if is_render:
            print("\n✓ Running on Render deployment")
        else:
            print("\n✓ Running in local/development environment")

        # Initialize blockchain with auto-restore enabled
        print("\n🔄 Initializing blockchain with auto-restore...")
        print("   Priority 1: PostgreSQL database (fastest)")
        print("   Priority 2: IPFS/Pinata backup")
        print("   Priority 3: Local encrypted file")
        blockchain = PropertyBlockchain(verbose=True, auto_restore=True)

        # Check restoration status
        if len(blockchain.chain) > 1:
            print(f"\n✅ Blockchain successfully restored!")
            print(f"   Total blocks: {len(blockchain.chain)}")
            print(
                f"   Total properties: {len([k for k in blockchain.property_index if k != 'GENESIS'])}"
            )

            # Verify blockchain integrity
            if blockchain.is_chain_valid():
                print("   ✓ Blockchain integrity verified")
            else:
                print("   ⚠ Warning: Blockchain integrity check failed")
        else:
            print("\n⚠ Blockchain has only genesis block")
            print("   This is normal for first deployment or if no backups exist")

        # Check IPFS configuration
        pinata_api_key = os.environ.get("PINATA_API_KEY", "")
        pinata_secret_key = os.environ.get("PINATA_SECRET_KEY", "")

        if (
            pinata_api_key
            and pinata_secret_key
            and pinata_api_key != "your_pinata_api_key_here"
        ):
            print("\n✓ IPFS (Pinata) configuration detected")
            print("   Auto-backup to IPFS will be enabled on data changes")
        else:
            print("\n⚠ IPFS (Pinata) not configured")
            print("   Set PINATA_API_KEY and PINATA_SECRET_KEY environment variables")
            print("   to enable automatic IPFS backups")

        # Check database configuration
        database_url = os.environ.get("DATABASE_URL", "")
        if database_url and "postgresql" in database_url:
            print("\n✓ PostgreSQL database detected")
            print("   Auto-backup to database enabled")
            print("   Database restoration is primary recovery method")
        else:
            print("\n⚠ PostgreSQL not configured (using SQLite)")
            print("   Database backups will use SQLite (not recommended for production)")

        # Check CID persistence methods
        print("\n📝 CID Persistence Methods:")
        if os.environ.get("RENDER_API_KEY"):
            print("   ✓ Render environment variables (via API)")
        if pinata_api_key:
            print("   ✓ Pinata metadata search")
        if os.environ.get("GITHUB_TOKEN"):
            print("   ✓ GitHub Gist backup")
        print("   ✓ Local file backup (for development)")

        print("\n" + "=" * 60)
        print("STARTUP RESTORE COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Startup restore failed: {str(e)}")
        print("\nThe application will continue with a fresh blockchain")
        print("=" * 60 + "\n")
        return False


def check_cid_storage():
    """
    Check CID storage configuration and latest CID availability
    """
    try:
        print("\n🔍 Checking CID storage configuration...")

        # Check if CID manager can retrieve a CID
        latest_cid = cid_manager.get_latest_cid()
        if latest_cid:
            print(f"✓ Found latest CID: {latest_cid}")

            # Show CID history if available
            history = cid_manager.get_cid_history()
            if history:
                print(f"✓ CID history available: {len(history)} backups recorded")
        else:
            print("⚠ No previous CID found - this is normal for first deployment")

        # Check Render API configuration
        if os.environ.get("RENDER_API_KEY") and os.environ.get("RENDER_SERVICE_ID"):
            print("✓ Render API configured for environment variable updates")
        else:
            print(
                "⚠ Render API not configured (set RENDER_API_KEY and RENDER_SERVICE_ID)"
            )

        # Check GitHub Gist configuration
        if os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_GIST_ID"):
            print("✓ GitHub Gist configured for backup storage")
        else:
            print("⚠ GitHub Gist not configured (optional backup method)")

        return True

    except Exception as e:
        print(f"⚠ Could not check CID storage: {str(e)}")
        return False


if __name__ == "__main__":
    # Check CID storage configuration
    check_cid_storage()

    # Perform startup restoration
    success = startup_restore()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
