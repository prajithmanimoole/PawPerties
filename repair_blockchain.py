"""
Blockchain Repair Utility
Automatically detects and repairs corrupted block hashes
"""

from blockchain import PropertyBlockchain
import re


def is_valid_sha256_hash(hash_string):
    """Check if a string is a valid SHA-256 hash (64 hex characters)"""
    if not hash_string or len(hash_string) != 64:
        return False
    # SHA-256 hashes should only contain 0-9 and a-f
    return bool(re.match(r'^[0-9a-f]{64}$', hash_string.lower()))


def repair_blockchain():
    """
    Repair corrupted blockchain by recalculating ALL hashes with deterministic serialization.
    This fixes blocks with corrupted hashes and ensures all hashes are calculated consistently.
    """
    print("="*60)
    print("BLOCKCHAIN REPAIR UTILITY")
    print("="*60)
    
    # Load blockchain
    print("\n[1/4] Loading blockchain...")
    blockchain = PropertyBlockchain(verbose=True)
    
    if not blockchain.chain or len(blockchain.chain) == 0:
        print("❌ No blockchain found! Nothing to repair.")
        return False
    
    print(f"✓ Loaded {len(blockchain.chain)} blocks")
    
    # Detect corrupted blocks
    print("\n[2/4] Scanning for hash inconsistencies...")
    corrupted_blocks = []
    
    for i, block in enumerate(blockchain.chain):
        issues = []
        
        # Check if hash is valid SHA-256
        if not is_valid_sha256_hash(block.hash):
            issues.append(f"Invalid hash format: {block.hash[:20]}...")
        
        # Check if hash matches calculated hash (with deterministic serialization)
        calculated_hash = block.calculate_hash()
        if block.hash != calculated_hash:
            issues.append(f"Hash mismatch (recalculation needed due to serialization fix)")
        
        # Check if previous_hash reference is valid (skip genesis)
        if i > 0:
            expected_prev_hash = blockchain.chain[i-1].hash
            if block.previous_hash != expected_prev_hash:
                issues.append(f"Invalid previous_hash reference")
        
        if issues:
            corrupted_blocks.append((i, block, issues))
            print(f"⚠️  Block #{i} ({block.property_key}): {', '.join(issues)}")
    
    if not corrupted_blocks:
        print("✅ No corrupted blocks found! Blockchain is healthy.")
        return True
    
    print(f"\n⚠️  Found {len(corrupted_blocks)} block(s) needing repair")
    print("    (This is expected after fixing JSON serialization)")
    
    # Repair ALL blocks to ensure deterministic hashing
    print("\n[3/4] Recalculating ALL block hashes with deterministic serialization...")
    
    for i, block in enumerate(blockchain.chain):
        if i == 0:
            # Genesis block
            old_hash = block.hash
            block.hash = block.calculate_hash()
            if old_hash != block.hash:
                print(f"  ✓ Block #{i} (GENESIS): Hash updated")
        else:
            # Regular blocks - ensure previous_hash is correct first
            previous_block = blockchain.chain[i - 1]
            block.previous_hash = previous_block.hash
            
            # Recalculate hash
            old_hash = block.hash
            block.hash = block.calculate_hash()
            
            if old_hash != block.hash:
                print(f"  ✓ Block #{i} ({block.property_key}): Hash updated")
    
    print(f"\n✓ All blocks recalculated with deterministic serialization")
    
    # Validate repaired blockchain
    print("\n[4/4] Validating repaired blockchain...")
    if blockchain.is_chain_valid():
        print("✅ Blockchain validation PASSED!")
        
        # Save repaired blockchain
        print("\nSaving repaired blockchain...")
        if blockchain._save_blockchain():
            print("✅ Repaired blockchain saved successfully!")
            print("\n" + "="*60)
            print("REPAIR COMPLETE!")
            print("="*60)
            print("\nYou can now use the application normally.")
            print("The blockchain history and view pages should work correctly.")
            return True
        else:
            print("❌ Failed to save repaired blockchain")
            return False
    else:
        print("❌ Blockchain validation FAILED after repair!")
        print("   Manual intervention may be required.")
        return False


if __name__ == "__main__":
    try:
        success = repair_blockchain()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ REPAIR FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
