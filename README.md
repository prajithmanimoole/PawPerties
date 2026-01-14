# Property Registration Blockchain System 🏠⛓️

A secure internal web application for property registration using custom blockchain technology with **Indian property standards** (Aadhar, PAN, Survey Numbers).

## 🎯 System Overview

This application is designed for **authorized blockchain officers and administrators only**. It provides an immutable, transparent property registration system where every transaction is recorded on a custom blockchain.

## 🏗️ Simplified Architecture

### Core Files (Only 9 essential files!)
- **app.py** - Main Flask application with all routes
- **blockchain.py** - Custom blockchain implementation (Indian standards)
- **auth.py** - Authentication service
- **models.py** - SQLite user models
- **config.py** - Application configuration
- **chatbot_service.py** - AI chatbot service with intelligent query handling
- **chatbot_training_data.py** - Comprehensive knowledge base for chatbot
- **requirements.txt** - Dependencies
- **README.md** - This file

### Technology Stack
- **Backend**: Python Flask 3.0.0
- **Blockchain**: Custom Python implementation with SHA-256 hashing
- **Database**: SQLite (authentication ONLY)
- **Frontend**: HTML/CSS with Jinja2 templates
- **Security**: Encrypted blockchain storage, identity validation

### Key Principles
1. **Blockchain data is NEVER stored in SQLite**
2. **SQLite is used ONLY for officer authentication and roles**
3. **Every property operation creates a new immutable block**
4. **Indian identity validation**: Aadhar (12 digits), PAN (ABCDE1234F format)
5. **Survey number uniqueness enforcement**
6. **Security and access control are mandatory**

## 👥 User Roles

### Officer
- Add new properties
- Transfer property ownership
- Record property inheritance
- View and search properties

### Admin
- All officer capabilities
- Validate blockchain integrity
- View complete blockchain
- Create blockchain backups

## 🔐 Default Login Credentials

**⚠️ CHANGE THESE IN PRODUCTION!**

- **Admin**: 
  - Username: `admin`
  - Password: `admin123`

- **Officer**: 
  - Username: `officer1`
  - Password: `officer123`

## 📋 Features

### Property Operations
1. **Add Property** - Register new property on blockchain
2. **Transfer Property** - Transfer ownership between parties
3. **Inherit Property** - Record property inheritance
4. **View Property** - See current property state
5. **Property History** - View complete transaction history
6. **Search by Owner** - Find all properties owned by a person
7. **View All Properties** - List all registered properties

### AI Chatbot Assistant 🤖
- **Floating popup chatbot** available on all pages
- Intelligent query handling with fuzzy matching for typos
- Comprehensive knowledge about all system features
- Handles questions about:
  - Property registration and transfer processes
  - Fees and payment structure
  - Document requirements
  - Appointment scheduling
  - Blockchain technology and security
  - User roles and permissions
  - Troubleshooting common issues
- Works offline with fallback responses when AI unavailable

### Blockchain Management (Admin Only)
1. **Validate Blockchain** - Check blockchain integrity
2. **View Full Blockchain** - Inspect all blocks
3. **Create Backup** - Save blockchain to timestamped file

## 🔒 Security Features

### Authentication
- Session-based authentication
- Password hashing using Werkzeug
- Automatic session expiration (2 hours)
- Secure cookie settings

### Authorization
- Role-based access control (RBAC)
- Route-level decorators:
  - `@login_required` - Requires authentication
  - `@officer_or_admin_required` - Property operations
  - `@admin_required` - Blockchain management

### Blockchain Security
- SHA-256 cryptographic hashing
- Proof-of-work mining
- Immutable block structure
- Chain validation mechanisms

## 📁 Project Structure

```
PawParties/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── blockchain.py               # Custom blockchain implementation
├── blockchain_service.py       # Blockchain operations wrapper
├── models.py                   # Database models (auth only)
├── auth.py                     # Authentication services
├── database.db                 # SQLite database (auto-generated)
├── blockchain_data.pkl         # Blockchain persistence (auto-generated)
├── templates/                  # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── add_property.html
│   ├── transfer_property.html
│   ├── inherit_property.html
│   ├── view_property.html
│   ├── property_history.html
│   ├── search_owner.html
│   ├── all_properties.html
│   ├── blockchain_admin.html
│   └── view_blockchain.html
└── static/
    └── style.css               # Professional styling
```

## 🔄 Data Flow

### 1. Authentication Flow
```
User Login → SQLite Validates → Session Created → Access Granted
```

### 2. Property Registration Flow
```
Officer Submits Form → Flask Route Validates → Blockchain Service Creates Block → 
Block Mined (PoW) → Added to Chain → Saved to Disk → Confirmation Returned
```

### 3. Property Query Flow
```
User Requests Property → Blockchain Service Reconstructs State → 
Iterates All Blocks → Applies Transactions → Returns Current State
```

### 4. Blockchain Validation Flow
```
Admin Triggers → Validate Each Block Hash → Verify Previous Hash Links → 
Check Proof of Work → Return Validation Status
```

## 🧩 Core Components

### 1. Blockchain (`blockchain.py`)
- **Block Class**: Individual block with hash, data, timestamp
- **PropertyBlockchain Class**: Complete blockchain with operations
- **Mining**: Proof-of-work with configurable difficulty
- **Validation**: Integrity checking and hash verification

### 2. Blockchain Service (`blockchain_service.py`)
- **Singleton Pattern**: Single blockchain instance
- **Thread Safety**: Lock-based synchronization
- **Persistence**: Automatic save after operations
- **High-level API**: Property operations wrapper

### 3. Authentication (`auth.py`)
- **AuthService**: Login, logout, session management
- **Decorators**: Route protection based on roles
- **Security**: Password hashing, session validation

### 4. Database Models (`models.py`)
- **User Model**: Officers and admins
- **Attributes**: username, password_hash, role, timestamps
- **Methods**: Password validation, role checking

### 5. Flask Application (`app.py`)
- **Routes**: All HTTP endpoints
- **Security**: Decorator-protected routes
- **Error Handling**: 404, 500 handlers
- **Session Management**: Flask session configuration

## 📊 Blockchain Structure

### Genesis Block
```json
{
  "index": 0,
  "timestamp": "2024-01-01T00:00:00",
  "data": {
    "type": "genesis",
    "message": "Property Blockchain Initialized"
  },
  "previous_hash": "0",
  "hash": "00abc123...",
  "nonce": 42
}
```

### Property Registration Block
```json
{
  "index": 1,
  "timestamp": "2024-01-01T10:30:00",
  "data": {
    "type": "add_property",
    "property_key": "PROP-2024-001",
    "owner": "John Doe",
    "address": "123 Main St",
    "area": 2500.0,
    "property_type": "Residential",
    "officer": "officer1",
    "action": "Property Registered"
  },
  "previous_hash": "00abc123...",
  "hash": "00def456...",
  "nonce": 187
}
```

### Transfer Block
```json
{
  "index": 2,
  "timestamp": "2024-01-02T14:20:00",
  "data": {
    "type": "transfer_property",
    "property_key": "PROP-2024-001",
    "from_owner": "John Doe",
    "to_owner": "Jane Smith",
    "officer": "officer1",
    "action": "Property Transferred"
  },
  "previous_hash": "00def456...",
  "hash": "00ghi789...",
  "nonce": 234
}
```

## ⚠️ Important Notes

1. **Immutability**: Once a block is added, it cannot be modified or deleted
2. **No Deletion**: Properties cannot be deleted, only transferred
3. **Exact Names**: Owner names must match exactly for transfers
4. **Unique Keys**: Property keys must be unique across the system
5. **Backup Regularly**: No built-in disaster recovery
6. **SQLite Limitations**: Not for high-concurrency production use

## 📄 License

Internal Use Only - Property Registration System

---

**Built with security, immutability, and transparency in mind.**

## 🔗 Sharing Blockchain Data

### 1. Manual File Sharing
- Send the files from your `blocks/` folder (such as `blockchain_data.encrypted`) to your collaborators using email, Google Drive, Dropbox, or any file-sharing service.
- The recipient should place these files in their own `blocks/` folder inside the project directory.

### 2. Decentralized Sharing via IPFS/Pinata
- Use the built-in admin feature to back up the blockchain to IPFS (Pinata).
- Share the IPFS CID (Content Identifier) with your collaborators.
- They can restore the blockchain by using the CID to download the file from IPFS and placing it in their `blocks/` folder, or by using the admin restore feature in the app.

**Example Workflow:**
1. Admin creates a backup (file or IPFS) from the app.
2. Shares the file or CID with another admin.
3. The other admin restores the blockchain using the file or CID.
