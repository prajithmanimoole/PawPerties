"""
Quick test to verify Pinata CID restoration works
"""
import os
from blockchain import PropertyBlockchain

print("\n" + "="*70)
print("TESTING PINATA CID RESTORATION")
print("="*70)

# Read CID from file
with open("pinata_cid.txt", 'r') as f:
    cid = f.read().strip()

print(f"\nCID from file: {cid}")

# Set environment variable (simulating Render)
os.environ['PINATA_RESTORE_CID'] = cid

print("\n" + "-"*70)
print("Initializing blockchain with IPFS restore...")
print("-"*70)

# Initialize blockchain - it should restore from IPFS
blockchain = PropertyBlockchain(verbose=True, auto_restore=True)

print("\n" + "-"*70)
print("RESULTS:")
print("-"*70)
print(f"Total Blocks: {len(blockchain.chain)}")
print(f"Total Properties: {len([k for k in blockchain.property_index if k != 'GENESIS'])}")

# Show all properties
properties = blockchain.get_all_properties()
print(f"\nProperties loaded: {len(properties)}")
for i, prop in enumerate(properties[:5], 1):  # Show first 5
    print(f"  {i}. {prop['property_key']}: {prop['owner']}")
if len(properties) > 5:
    print(f"  ... and {len(properties) - 5} more")

print("\n" + "-"*70)
print("RECENT LOGS:")
print("-"*70)
for log in blockchain.logs[-15:]:
    print(f"  {log}")

print("\n" + "="*70)
if len(properties) > 0:
    print("✅ SUCCESS! Data restored from Pinata IPFS")
else:
    print("❌ FAILED! No data loaded")
print("="*70)
