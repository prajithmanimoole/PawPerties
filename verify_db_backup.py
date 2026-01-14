
import os
import sys
from flask import Flask
from models import db, BlockchainBackup, init_db
from blockchain import PropertyBlockchain

# Configure test app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test'
app.config['PINATA_API_KEY'] = 'test' # Mock
app.config['PINATA_SECRET_KEY'] = 'test'

init_db(app)

def test_db_backup():
    print("Testing database backup...")
    with app.app_context():
        # Setup DB
        db.create_all()
        
        # Create blockchain instance
        bc = PropertyBlockchain(verbose=True)
        
        # Mocking data
        bc._create_genesis_block()
        
        # Try backup using the internal method called by save_and_exit
        # We need to ensure _save_blockchain calls backup_to_database and it works
        
        # Force the backup_to_database call explicitly to check return value
        success = bc.backup_to_database(admin_id=1, backup_name="Test Backup")
        
        if success:
            print("PASS: backup_to_database returned True")
            
            # Verify record exists
            count = BlockchainBackup.query.count()
            if count == 1:
                print("PASS: 1 backup found in database")
            else:
                print(f"FAIL: Expected 1 backup, found {count}")
        else:
            print("FAIL: backup_to_database returned False")
            
if __name__ == "__main__":
    test_db_backup()
