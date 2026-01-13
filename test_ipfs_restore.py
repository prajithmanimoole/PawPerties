"""
Test script to demonstrate automatic IPFS restoration feature.

This script shows how the blockchain automatically restores from Pinata IPFS
when pinata_cid.txt exists in the project root.
"""

from blockchain import PropertyBlockchain
import os

def test_ipfs_auto_restore():
    """Test automatic restoration from IPFS."""
    
    print("\n" + "="*70)
    print("TESTING AUTOMATIC IPFS RESTORATION")
    print("="*70)
    
    # Check if pinata_cid.txt exists
    if os.path.exists("pinata_cid.txt"):
        print(f"\n✓ Found pinata_cid.txt in project root")
        with open("pinata_cid.txt", 'r') as f:
            cid = f.read().strip()
        print(f"  CID: {cid}")
    else:
        print(f"\n✗ No pinata_cid.txt found")
        print("  Create this file with a valid Pinata CID to enable auto-restore")
        return
    
    print("\n" + "-"*70)
    print("Initializing PropertyBlockchain...")
    print("-"*70)
    
    # Initialize blockchain - it will automatically try IPFS restoration first
    blockchain = PropertyBlockchain(verbose=True, auto_restore=True)
    
    print("\n" + "-"*70)
    print("BLOCKCHAIN INFO:")
    print("-"*70)
    print(f"Total Blocks: {len(blockchain.chain)}")
    print(f"Total Properties: {len([k for k in blockchain.property_index if k != 'GENESIS'])}")
    print(f"Latest Hash: {blockchain.get_latest_block().hash[:20]}...")
    
    # Show all properties
    properties = blockchain.get_all_properties()
    print(f"\n{len(properties)} properties loaded:")
    for prop in properties:
        print(f"  - {prop['property_key']}: {prop['owner']} ({prop['address']})")
    
    print("\n" + "="*70)
    print("RESTORATION LOGS (last 10):")
    print("="*70)
    for log in blockchain.logs[-10:]:
        print(f"  {log}")
    
    print("\n" + "="*70)
    print("Test completed!")
    print("="*70)

if __name__ == "__main__":
    test_ipfs_auto_restore()
