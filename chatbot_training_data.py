"""
PawParties Property System - Comprehensive AI Chatbot Training Data
This document contains detailed information about all features, workflows, and common user queries
"""

# ============================================================================
# SYSTEM OVERVIEW
# ============================================================================

SYSTEM_OVERVIEW = """
PawParties is a blockchain-based property registration and management system for India.
It uses advanced cryptographic technology to ensure tamper-proof, permanent property records.
Every transaction is recorded on an immutable blockchain, providing complete transparency and security.
The system eliminates property fraud and provides instant verification of ownership.
"""

# ============================================================================
# USER ROLES AND PERMISSIONS
# ============================================================================

USER_ROLES = {
    "user": {
        "name": "Regular User / Property Owner",
        "can_do": [
            "View their own properties on dashboard",
            "Search for any property using property key",
            "View complete property history and ownership chain",
            "Schedule appointments with officers",
            "Update personal profile information",
            "Download property history reports",
            "View blockchain transactions related to their properties"
        ],
        "cannot_do": [
            "Directly transfer properties (must go through officer)",
            "Add new properties to system",
            "Modify blockchain data",
            "Access other users' private information",
            "Approve or process transfers"
        ]
    },
    "officer": {
        "name": "Government Officer",
        "can_do": [
            "Process property registrations",
            "Handle property transfers",
            "Manage and approve appointments",
            "Verify documents (Aadhar, PAN, property papers)",
            "Add new properties to blockchain",
            "Search and view all properties",
            "Process inheritance transfers",
            "Generate property reports"
        ],
        "cannot_do": [
            "Modify blockchain settings",
            "Access admin panel",
            "Delete or alter historical records",
            "Create new user accounts"
        ]
    },
    "admin": {
        "name": "System Administrator",
        "can_do": [
            "All officer permissions",
            "Access admin control panel",
            "Manage blockchain backups and restoration",
            "Export data to IPFS",
            "View system-wide statistics",
            "User account management",
            "System configuration",
            "Database maintenance",
            "Security settings management"
        ],
        "cannot_do": [
            "Alter immutable blockchain records",
            "Forge property transactions"
        ]
    }
}

# ============================================================================
# COMPLETE FEATURES GUIDE
# ============================================================================

FEATURES_GUIDE = {
    "dashboard": {
        "name": "Dashboard",
        "description": "Main control center showing overview of properties and activities",
        "for_users": [
            "View list of all properties you own",
            "See recent transactions and updates",
            "Check upcoming appointments",
            "Quick access to schedule new appointments",
            "Property count and value overview",
            "Recent activity timeline"
        ],
        "for_officers": [
            "Overview of all registered properties",
            "Pending transfer requests",
            "Today's appointments",
            "System statistics and metrics",
            "Quick action buttons"
        ],
        "how_to_access": "Login → Redirects automatically to dashboard",
        "common_questions": [
            "Where can I see my properties?",
            "How do I check my appointments?",
            "Where is my dashboard?"
        ]
    },
    
    "add_property": {
        "name": "Add Property / Register Property",
        "description": "Register new properties into the blockchain system",
        "who_can_use": "Officers and Admins only",
        "required_info": [
            "Property owner's full name",
            "Owner's Aadhar card number (12 digits)",
            "Owner's PAN card number (format: ABCDE1234F)",
            "Complete property address",
            "Property type (Residential/Commercial/Agricultural/Industrial)",
            "Property area (in sq ft or sq meters)",
            "Property value/market price"
        ],
        "required_documents": [
            "Original property ownership documents",
            "Sale deed or gift deed",
            "Encumbrance certificate",
            "Property tax receipts",
            "Aadhar card of owner",
            "PAN card of owner",
            "NOC from society/builder (if applicable)"
        ],
        "process_steps": [
            "1. Officer logs in and clicks 'Add Property'",
            "2. Fill in all property details in the form",
            "3. Upload required documents",
            "4. Verify all information is correct",
            "5. Submit the form",
            "6. System generates unique Property Key (PROP-XXXXX-XXX)",
            "7. Property is added to blockchain",
            "8. Transaction recorded with cryptographic hash",
            "9. Property appears in owner's dashboard"
        ],
        "fees": "₹5,000 (one-time registration fee)",
        "time": "7-15 working days for complete verification",
        "how_to_access": "Dashboard → Add Property button",
        "common_questions": [
            "How to register property?",
            "What documents needed for registration?",
            "How much is registration fee?",
            "How long does registration take?"
        ]
    },
    
    "transfer_property": {
        "name": "Transfer Property / Change Ownership",
        "description": "Transfer property ownership from one person to another",
        "who_can_use": "Officers process transfers, Users request via appointments",
        "required_info": [
            "Property key of the property to transfer",
            "Current owner's details",
            "New owner's full name",
            "New owner's Aadhar (12 digits)",
            "New owner's PAN (ABCDE1234F format)",
            "Transfer reason (sale/gift/exchange)",
            "Transaction value (for stamp duty calculation)"
        ],
        "required_documents": [
            "Original property documents",
            "Sale agreement signed by both parties",
            "NOC from current owner",
            "New owner's identity proofs",
            "Payment receipts for property transaction",
            "Encumbrance certificate",
            "Power of attorney (if applicable)"
        ],
        "process_steps": [
            "1. USER: Schedule appointment from dashboard",
            "2. USER: Submit all required documents",
            "3. OFFICER: Review appointment and documents",
            "4. OFFICER: Verify both parties' identities",
            "5. OFFICER: Calculate fees (₹3,000 + 2% stamp + 5% registration)",
            "6. OFFICER: Process payment",
            "7. OFFICER: Execute transfer in system",
            "8. SYSTEM: Creates new blockchain entry",
            "9. SYSTEM: Updates ownership records",
            "10. Both parties receive confirmation"
        ],
        "fees": {
            "base": "₹3,000",
            "stamp_duty": "2% of property transaction value",
            "registration_fee": "5% of property transaction value",
            "example": "For ₹10 lakh property: ₹3,000 + ₹20,000 + ₹50,000 = ₹73,000 total"
        },
        "time": "10-20 working days",
        "how_to_access": "Officers: Dashboard → Transfer Property | Users: Dashboard → Schedule Appointment",
        "important_notes": [
            "Both parties must be present or provide authorization",
            "Cannot transfer property with pending legal disputes",
            "Previous owner loses all access after transfer",
            "Transfer is recorded permanently on blockchain"
        ],
        "common_questions": [
            "How to transfer property?",
            "Can I sell my property?",
            "What is transfer fee?",
            "How to change ownership?"
        ]
    },
    
    "inherit_property": {
        "name": "Inherit Property / Succession",
        "description": "Handle property inheritance after owner's death",
        "who_can_use": "Officers process, Legal heirs request via appointments",
        "required_documents": [
            "Death certificate of deceased owner",
            "Legal heir certificate from government",
            "Succession certificate from court",
            "Will document (if available)",
            "Family tree affidavit",
            "Heirs' identity proofs (Aadhar, PAN)",
            "No objection from other family members"
        ],
        "process_steps": [
            "1. Legal heir schedules appointment",
            "2. Submit death certificate and legal documents",
            "3. Officer verifies all documents",
            "4. Court succession certificate validation",
            "5. Verify all legal heirs",
            "6. Determine ownership distribution",
            "7. Process inheritance transfer",
            "8. Update blockchain with new owner(s)",
            "9. Generate inheritance certificate"
        ],
        "fees": {
            "base": "₹2,000",
            "stamp_duty": "1% of property value",
            "example": "For ₹10 lakh property: ₹2,000 + ₹10,000 = ₹12,000"
        },
        "time": "15-30 working days (depends on legal verification)",
        "how_to_access": "Dashboard → Inherit Property",
        "important_notes": [
            "All legal heirs must be documented",
            "Will takes precedence if valid",
            "Multiple heirs can share ownership",
            "Legal disputes must be resolved first"
        ],
        "common_questions": [
            "How to inherit property?",
            "What documents needed for inheritance?",
            "Can property be inherited without will?"
        ]
    },
    
    "search_property": {
        "name": "Search Properties",
        "description": "Find and view property information",
        "who_can_use": "All users",
        "search_options": [
            "By Property Key (PROP-XXXXX-XXX)",
            "By Owner Name",
            "By Aadhar Number",
            "By PAN Card Number",
            "By Location/Address"
        ],
        "what_you_can_see": [
            "Property address and details",
            "Current owner information",
            "Property type and area",
            "Complete ownership history",
            "All past transactions",
            "Blockchain verification status"
        ],
        "how_to_access": "Dashboard → Search / Navigation → Search",
        "common_questions": [
            "How to find a property?",
            "How to search by owner?",
            "How to verify property ownership?"
        ]
    },
    
    "appointments": {
        "name": "Appointments System",
        "description": "Schedule meetings with officers for property matters",
        "who_can_use": "All users can book, Officers manage",
        "appointment_types": [
            "Property Transfer",
            "Property Registration Query",
            "Document Verification",
            "Inheritance Processing",
            "General Property Query"
        ],
        "how_to_book": [
            "1. Go to Dashboard → My Appointments",
            "2. Click 'Schedule New Appointment'",
            "3. Select appointment type and reason",
            "4. Choose preferred date and time",
            "5. Enter contact details",
            "6. Add any specific notes",
            "7. Submit appointment request",
            "8. Receive confirmation"
        ],
        "what_happens_next": [
            "Officer reviews your request",
            "Appointment is approved/rescheduled",
            "You receive email/SMS confirmation",
            "Attend appointment with required documents",
            "Officer processes your request"
        ],
        "fees": "Free to schedule appointments",
        "how_to_access": "Dashboard → My Appointments",
        "common_questions": [
            "How to book appointment?",
            "How to schedule meeting?",
            "Can I reschedule appointment?"
        ]
    },
    
    "property_history": {
        "name": "Property History / Ownership Chain",
        "description": "View complete transaction history of any property",
        "who_can_use": "All users",
        "what_it_shows": [
            "Original registration details",
            "All ownership transfers with dates",
            "Previous owners list",
            "Transaction amounts",
            "Blockchain verification hashes",
            "Timestamps for each transaction",
            "Officer who processed each transfer"
        ],
        "how_to_access": "Search property → Click 'View History'",
        "benefits": [
            "Verify property authenticity",
            "Check for any disputes",
            "See complete ownership chain",
            "Blockchain proof of records"
        ],
        "common_questions": [
            "How to check property history?",
            "Who owned this property before?",
            "How to verify property records?"
        ]
    },
    
    "blockchain_view": {
        "name": "Blockchain Viewer",
        "description": "View technical blockchain data and verification",
        "who_can_use": "All users (limited), Admins (full access)",
        "what_you_can_see": [
            "All blocks in the chain",
            "Block hashes",
            "Transaction data in each block",
            "Timestamps",
            "Chain validation status",
            "Cryptographic proofs"
        ],
        "how_to_access": "Dashboard → View Blockchain",
        "common_questions": [
            "What is blockchain?",
            "How is data secured?",
            "Can records be changed?"
        ]
    },
    
    "profile": {
        "name": "User Profile",
        "description": "Manage your account information",
        "who_can_use": "All users",
        "what_you_can_update": [
            "Full name",
            "Email address",
            "Phone number",
            "Address",
            "Password"
        ],
        "how_to_access": "Navigation → Profile",
        "common_questions": [
            "How to change password?",
            "How to update contact info?"
        ]
    }
}

# ============================================================================
# FEES AND CHARGES
# ============================================================================

FEES_STRUCTURE = {
    "registration": {
        "amount": "₹5,000",
        "description": "One-time fee for adding new property to blockchain",
        "includes": ["Document verification", "Blockchain entry", "Property key generation"]
    },
    "transfer": {
        "base_fee": "₹3,000",
        "stamp_duty": "2% of property transaction value",
        "registration_fee": "5% of property transaction value",
        "example": "For ₹10,00,000 property: ₹3,000 + ₹20,000 (2%) + ₹50,000 (5%) = ₹73,000 total"
    },
    "inheritance": {
        "base_fee": "₹2,000",
        "stamp_duty": "1% of property value",
        "example": "For ₹10,00,000 property: ₹2,000 + ₹10,000 (1%) = ₹12,000 total"
    },
    "document_verification": "₹500 per document set",
    "appointment": "Free",
    "history_report": "Free download"
}

# ============================================================================
# DOCUMENTS REQUIRED
# ============================================================================

DOCUMENTS_REQUIRED = {
    "registration": [
        "Aadhar Card (12-digit number)",
        "PAN Card (ABCDE1234F format)",
        "Property ownership documents (Sale deed/Gift deed)",
        "Encumbrance certificate",
        "Property tax receipts",
        "NOC from society/builder (if applicable)",
        "Passport size photographs",
        "Address proof"
    ],
    "transfer": [
        "All registration documents",
        "Sale agreement between parties",
        "NOC from current owner",
        "New owner's identity proofs",
        "Payment receipts",
        "Power of attorney (if applicable)"
    ],
    "inheritance": [
        "Death certificate of deceased owner",
        "Legal heir certificate",
        "Succession certificate from court",
        "Will document (if available)",
        "Family tree affidavit",
        "Identity proofs of all heirs",
        "NOC from other family members"
    ]
}

# ============================================================================
# BLOCKCHAIN TECHNOLOGY
# ============================================================================

BLOCKCHAIN_INFO = {
    "what_is_it": "A blockchain is a distributed, immutable ledger that records transactions in blocks linked cryptographically",
    "how_it_works": [
        "Each property transaction creates a new block",
        "Block contains transaction data, timestamp, and cryptographic hash",
        "Each block links to previous block using hash",
        "Creates an unbreakable chain of records",
        "Any tampering attempt is immediately detected",
        "SHA-256 encryption ensures security"
    ],
    "benefits": [
        "Tamper-proof records - cannot be altered",
        "Complete transparency - full audit trail",
        "No single point of failure",
        "Instant verification of authenticity",
        "Eliminates property fraud",
        "Permanent record keeping"
    ],
    "security": [
        "SHA-256 cryptographic hashing",
        "Proof-of-work validation",
        "Distributed data storage",
        "Encrypted data transmission",
        "IPFS backup for redundancy"
    ]
}

# ============================================================================
# COMMON PROBLEMS AND SOLUTIONS
# ============================================================================

TROUBLESHOOTING = {
    "login_issues": {
        "forgot_password": "Click 'Forgot Password' on login page, or contact admin for manual reset",
        "account_locked": "Contact system administrator",
        "wrong_credentials": "Verify username/email and password, check caps lock"
    },
    "property_issues": {
        "property_not_showing": "Check if registration is complete. Allow 24-48 hours for processing. Contact officer if issue persists.",
        "wrong_information": "File a correction request through appointment system with supporting documents",
        "transfer_delayed": "Ensure all documents are submitted correctly. Check appointment status. Contact assigned officer.",
        "cannot_find_property": "Verify property key format (PROP-XXXXX-XXX). Check if property is registered in system."
    },
    "appointment_issues": {
        "cannot_book": "Check if you selected valid date/time. Ensure all required fields are filled.",
        "no_confirmation": "Check your email spam folder. Contact support if not received within 24 hours.",
        "need_to_cancel": "Go to My Appointments → Find appointment → Cancel button"
    },
    "technical_issues": {
        "page_not_loading": "Clear browser cache, try different browser, check internet connection",
        "upload_failed": "Reduce file size, ensure format is PDF/JPG/PNG, try again",
        "system_error": "Note error message, try logging out and back in, contact support if persists"
    }
}

# ============================================================================
# COMMON USER QUESTIONS AND ANSWERS
# ============================================================================

FAQ_DATABASE = {
    # General Questions
    "What is PawParties?": "PawParties is a blockchain-based property registration and management system for India. It uses advanced cryptography to ensure tamper-proof, permanent records of all property transactions.",
    
    # Registration Questions
    "How do I register a property?": "Property registration is done by Officers or Admins. Users need to schedule an appointment and provide all required documents including Aadhar, PAN, and property papers. Registration fee is ₹5,000.",
    
    "What documents do I need to register property?": "You need: Aadhar card (12 digits), PAN card (ABCDE1234F format), property ownership documents (sale deed), encumbrance certificate, property tax receipts, and NOC from society if applicable.",
    
    "How long does registration take?": "Property registration typically takes 7-15 working days after document verification.",
    
    # Transfer Questions  
    "How do I transfer my property?": "Schedule an appointment through your dashboard. Submit all required documents. An officer will verify everything and process the transfer. Both parties must be present.",
    
    "What is the transfer fee?": "Transfer fee is ₹3,000 plus 2% stamp duty and 5% registration fee on the property value. Example: For ₹10 lakh property = ₹73,000 total.",
    
    "Can I transfer property without owner permission?": "No, you must have the current owner's consent and NOC to transfer property.",
    
    # Inheritance Questions
    "How to inherit property after death?": "You need death certificate, legal heir certificate, succession certificate from court, and will (if any). Schedule appointment with officer to process inheritance transfer.",
    
    # Search Questions
    "How do I search for a property?": "Go to Search in navigation. You can search by property key (PROP-XXXXX-XXX), owner name, Aadhar, or PAN number.",
    
    "Can I see property history?": "Yes! Search for the property and click 'View History' to see complete ownership chain with all transactions.",
    
    # Appointment Questions
    "How to book an appointment?": "Go to Dashboard → My Appointments → Schedule New. Select type, date, time and submit. You'll receive confirmation.",
    
    "Is appointment booking free?": "Yes, scheduling appointments is completely free.",
    
    # Blockchain Questions
    "What is blockchain?": "Blockchain is a secure, tamper-proof digital ledger where all property transactions are permanently recorded and cryptographically linked.",
    
    "Can blockchain records be changed?": "No! Blockchain records are immutable. Once written, they cannot be altered, ensuring complete security and trust.",
    
    "How is my data secured?": "Data is secured using SHA-256 encryption, cryptographic hashing, and distributed storage. All records are tamper-proof.",
    
    # Fee Questions
    "What are all the fees?": "Registration: ₹5,000 | Transfer: ₹3,000 + 2% stamp + 5% registration | Inheritance: ₹2,000 + 1% stamp | Document verification: ₹500 | Appointments: Free",
    
    # Role Questions
    "What can regular users do?": "Users can view their properties, search any property, view history, schedule appointments, and update their profile.",
    
    "What is difference between officer and admin?": "Officers process registrations and transfers. Admins have additional access to system settings, blockchain management, and user administration.",
    
    # Technical Questions
    "What is property key?": "Property key is a unique identifier in format PROP-XXXXX-XXX generated during registration. It's used for all transactions and searches.",
    
    "How to check property authenticity?": "Search for the property using its key, then view the blockchain history. All transactions are cryptographically verified.",
    
    # Problem Questions
    "Property not showing in dashboard?": "Check if registration is complete. Wait 24-48 hours for processing. Contact the officer who processed your registration if issue persists.",
    
    "Forgot my password?": "Click 'Forgot Password' on the login page, or contact your system administrator for a password reset.",
    
    "Transfer is taking too long?": "Ensure all documents are submitted correctly. Check your appointment status. Contact the assigned officer for updates.",
}

# ============================================================================
# KEYWORDS FOR INTENT DETECTION
# ============================================================================

INTENT_KEYWORDS = {
    "registration": ["register", "add property", "new property", "registration", "registering", "regiter", "registr"],
    "transfer": ["transfer", "sell", "change owner", "ownership", "trasfer", "tranfer", "tranfser"],
    "inheritance": ["inherit", "inheritance", "death", "legal heir", "succession", "will", "inhrit"],
    "search": ["search", "find", "lookup", "locate", "check", "serch", "seach"],
    "appointment": ["appointment", "schedule", "book", "meeting", "slot", "apoointment", "apointment"],
    "fees": ["fee", "cost", "price", "charge", "payment", "money", "rate", "fess", "feez"],
    "documents": ["document", "paper", "aadhar", "pan", "certificate", "documnt"],
    "blockchain": ["blockchain", "secure", "technology", "hash", "encryption", "blokchain"],
    "history": ["history", "previous", "past", "record", "chain", "histroy"],
    "dashboard": ["dashboard", "home", "main page", "overview", "dashbord"],
    "login": ["login", "password", "forgot", "sign in", "account", "loggin"],
    "help": ["help", "support", "assist", "guide", "stuck", "halp"],
    "profile": ["profile", "account", "update info", "change password"],
    "roles": ["role", "admin", "officer", "user", "permission", "access"],
}

# ============================================================================
# SYSTEM CONSTRAINTS AND RULES
# ============================================================================

SYSTEM_RULES = {
    "aadhar_format": "12 digits (e.g., 1234 5678 9012)",
    "pan_format": "10 characters - 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)",
    "property_key_format": "PROP-XXXXX-XXX (e.g., PROP-12345-001)",
    "min_password_length": "8 characters",
    "working_days": "Monday to Friday, 9 AM to 5 PM",
    "max_file_size": "10 MB per document",
    "supported_file_types": "PDF, JPG, PNG",
}
