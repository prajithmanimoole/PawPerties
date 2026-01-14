"""
Custom Blockchain Implementation for Property Registration (Indian Standards)
This blockchain is immutable and stores all property transactions with
identity validation (Aadhar, PAN), survey uniqueness, and encrypted persistence.

NO DATABASE STORAGE - All property data lives ONLY in the blockchain.
SQLite is used ONLY for officer authentication in the Flask app.
"""

import base64
import copy
import hashlib
import json
import logging
import os
import subprocess
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import CID manager for persistent storage without database
from cid_manager import cid_manager

# Configure logging (optional - can be disabled)
logger = logging.getLogger(__name__)


class Block:
    """Represents a single block in the property blockchain."""

    def __init__(
        self,
        index: int,
        timestamp: str,
        data: Dict[str, Any],
        previous_hash: str,
        property_key: str,
    ):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.property_key = property_key
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block with deterministic JSON serialization."""
        block_string = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "data": self.data,
                "previous_hash": self.previous_hash,
                "property_key": self.property_key,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(block_string.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary representation with deep copy to prevent mutation."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": copy.deepcopy(self.data),
            "previous_hash": self.previous_hash,
            "property_key": self.property_key,
            "hash": self.hash,
        }


class PropertyBlockchain:
    """Blockchain-based property ledger system with Indian identity validation."""

    STORAGE_FOLDER = "blocks"
    STORAGE_FILE = "blocks/blockchain_data.encrypted"
    PINATA_CID_FILE = "pinata_cid.txt"  # CID file in project root for auto-restore

    # IPFS Configuration (Pinata) - Load from environment variables
    PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
    PINATA_SECRET_KEY = os.environ.get("PINATA_SECRET_KEY")

    def __init__(self, verbose: bool = False, auto_restore: bool = False):
        """
        Initialize PropertyBlockchain.

        Args:
            verbose: Enable console logging (default: False for production)
            auto_restore: Enable automatic restore from database backup if no local blockchain exists
        """
        self.verbose = verbose
        self.chain: List[Block] = []
        self.property_index: Dict[
            str, List[int]
        ] = {}  # Maps property_key to block indices
        self.logs: List[str] = []  # Store recent log messages for debugging

        # Identity registry to ensure Aadhar and PAN uniqueness
        # Format: {"owner_name": {"aadhar": "123456789012", "pan": "ABCDE1234F", "customer_key": "CUST-XXXX"}}
        self.identity_registry: Dict[str, Dict[str, str]] = {}
        # Reverse mappings for quick lookup
        self.aadhar_to_owner: Dict[str, str] = {}  # Maps aadhar -> owner_name
        self.pan_to_owner: Dict[str, str] = {}  # Maps pan -> owner_name
        self.customer_key_to_owner: Dict[
            str, str
        ] = {}  # Maps customer_key -> owner_name
        self.survey_to_property: Dict[
            str, str
        ] = {}  # Maps survey_no -> property_key (ensures uniqueness)

        # Priority 1: Try to restore from database backup (fastest and most reliable)
        if auto_restore and self._auto_restore_from_database():
            self._log("Successfully auto-restored blockchain from database")
        # Priority 2: Try to restore from Pinata IPFS CID if available
        elif self._auto_restore_from_ipfs():
            self._log("Successfully auto-restored blockchain from Pinata IPFS")
        # Priority 3: Try to load existing blockchain from encrypted file
        elif self._load_blockchain():
            self._log("Loaded existing blockchain from encrypted storage")
        else:
            # Create genesis block only if no existing blockchain was loaded
            self._create_genesis_block()
            self._log("Created new blockchain with genesis block")

    def _log(self, message: str, level: str = "info") -> None:
        """Internal logging method (only logs if verbose=True)."""
        # Always store logs for debugging
        self.logs.append(f"[{level.upper()}] {message}")
        # Keep only last 50 logs
        if len(self.logs) > 50:
            self.logs = self.logs[-50:]

        if self.verbose:
            if level == "error":
                logger.error(message)
            else:
                logger.info(message)

    def _create_genesis_block(self) -> None:
        """Create the first block in the chain."""
        genesis_block = Block(
            index=0,
            timestamp=datetime.now().isoformat(),
            data={"type": "genesis", "message": "Property Ledger Genesis Block"},
            previous_hash="0",
            property_key="GENESIS",
        )
        self.chain.append(genesis_block)

    def get_latest_block(self) -> Block:
        """Return the most recent block in the chain."""
        return self.chain[-1]

    def validate_aadhar(self, aadhar: str) -> bool:
        """Validate Aadhar number format (12 digits)."""
        aadhar_clean = aadhar.replace(" ", "").replace("-", "")
        return len(aadhar_clean) == 12 and aadhar_clean.isdigit()

    def validate_pan(self, pan: str) -> bool:
        """Validate PAN card format (10 alphanumeric characters)."""
        import re

        pan_pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
        return bool(re.match(pan_pattern, pan.upper()))

    def validate_aadhar_uniqueness(self, owner: str, aadhar: str) -> None:
        """Validate Aadhar uniqueness immediately upon entry.

        Raises:
            ValueError: If Aadhar is already used by someone else or owner has different Aadhar registered
        """
        aadhar_clean = aadhar.replace(" ", "").replace("-", "")
        owner_normalized = owner.strip()

        # Check if this owner already has a registered Aadhar
        if owner_normalized in self.identity_registry:
            registered_aadhar = self.identity_registry[owner_normalized]["aadhar"]
            if registered_aadhar != aadhar_clean:
                raise ValueError(
                    f"Identity mismatch: Owner '{owner_normalized}' is already registered "
                    f"with Aadhar {registered_aadhar}. Same person cannot have multiple Aadhar numbers."
                )

        # Check if this Aadhar is already used by someone else
        if aadhar_clean in self.aadhar_to_owner:
            existing_owner = self.aadhar_to_owner[aadhar_clean]
            if existing_owner != owner_normalized:
                raise ValueError(
                    f"Aadhar number {aadhar_clean} is already registered to '{existing_owner}'. "
                    f"Each Aadhar must be unique."
                )

    def validate_pan_uniqueness(self, owner: str, pan: str) -> None:
        """Validate PAN uniqueness immediately upon entry.

        Raises:
            ValueError: If PAN is already used by someone else or owner has different PAN registered
        """
        pan_clean = pan.upper()
        owner_normalized = owner.strip()

        # Check if this owner already has a registered PAN
        if owner_normalized in self.identity_registry:
            registered_pan = self.identity_registry[owner_normalized]["pan"]
            if registered_pan != pan_clean:
                raise ValueError(
                    f"Identity mismatch: Owner '{owner_normalized}' is already registered "
                    f"with PAN {registered_pan}. Same person cannot have multiple PAN numbers."
                )

        # Check if this PAN is already used by someone else
        if pan_clean in self.pan_to_owner:
            existing_owner = self.pan_to_owner[pan_clean]
            if existing_owner != owner_normalized:
                raise ValueError(
                    f"PAN number {pan_clean} is already registered to '{existing_owner}'. "
                    f"Each PAN must be unique."
                )

    def _generate_customer_key(self) -> str:
        """Generate a unique customer key for an owner.

        Returns:
            Unique customer key in format CUST-XXXXXXXX
        """
        # Generate a unique key using UUID and take first 8 characters
        unique_id = str(uuid.uuid4()).upper().replace("-", "")[:8]
        customer_key = f"CUST-{unique_id}"

        # Ensure it's unique (extremely unlikely to collide, but be safe)
        while customer_key in self.customer_key_to_owner:
            unique_id = str(uuid.uuid4()).upper().replace("-", "")[:8]
            customer_key = f"CUST-{unique_id}"

        return customer_key

    def validate_survey_uniqueness(
        self, survey_no: str, property_key: str = None
    ) -> None:
        """Validate Survey Number uniqueness immediately upon entry.

        Args:
            survey_no: Survey number to validate
            property_key: Current property key (for updates, not used in initial registration)

        Raises:
            ValueError: If survey number is already registered to another property
        """
        survey_clean = survey_no.strip()

        if survey_clean in self.survey_to_property:
            existing_property = self.survey_to_property[survey_clean]
            # Allow if it's the same property (shouldn't happen in add, but good for future)
            if property_key is None or existing_property != property_key:
                raise ValueError(
                    f"Survey number '{survey_clean}' is already registered to property '{existing_property}'. "
                    f"Each survey number must be unique."
                )

    def register_or_validate_identity(self, owner: str, aadhar: str, pan: str) -> bool:
        """Register a new owner or validate existing owner's identity.

        Args:
            owner: Owner's name
            aadhar: Aadhar number (will be cleaned)
            pan: PAN card number (will be uppercased)

        Returns:
            True if identity is valid and registered/verified

        Raises:
            ValueError: If there's an identity conflict
        """
        # Clean and normalize
        aadhar_clean = aadhar.replace(" ", "").replace("-", "")
        pan_clean = pan.upper()
        owner_normalized = owner.strip()

        # Check if this owner already exists in registry
        if owner_normalized in self.identity_registry:
            # Verify the Aadhar and PAN match
            registered_aadhar = self.identity_registry[owner_normalized]["aadhar"]
            registered_pan = self.identity_registry[owner_normalized]["pan"]

            if registered_aadhar != aadhar_clean:
                raise ValueError(
                    f"Identity mismatch: Owner '{owner_normalized}' is already registered "
                    f"with Aadhar {registered_aadhar}, but provided {aadhar_clean}. "
                    "Same person cannot have multiple Aadhar numbers."
                )

            if registered_pan != pan_clean:
                raise ValueError(
                    f"Identity mismatch: Owner '{owner_normalized}' is already registered "
                    f"with PAN {registered_pan}, but provided {pan_clean}. "
                    "Same person cannot have multiple PAN numbers."
                )

            # Identity matches - all good
            return True

        # Check if this Aadhar is already used by someone else
        if aadhar_clean in self.aadhar_to_owner:
            existing_owner = self.aadhar_to_owner[aadhar_clean]
            if existing_owner != owner_normalized:
                raise ValueError(
                    f"Aadhar number {aadhar_clean} is already registered to '{existing_owner}'. "
                    f"Cannot register same Aadhar to '{owner_normalized}'. "
                    "Each Aadhar must be unique."
                )

        # Check if this PAN is already used by someone else
        if pan_clean in self.pan_to_owner:
            existing_owner = self.pan_to_owner[pan_clean]
            if existing_owner != owner_normalized:
                raise ValueError(
                    f"PAN number {pan_clean} is already registered to '{existing_owner}'. "
                    f"Cannot register same PAN to '{owner_normalized}'. "
                    "Each PAN must be unique."
                )

        # New owner - register them with a unique customer key
        customer_key = self._generate_customer_key()

        self.identity_registry[owner_normalized] = {
            "aadhar": aadhar_clean,
            "pan": pan_clean,
            "customer_key": customer_key,
        }
        self.aadhar_to_owner[aadhar_clean] = owner_normalized
        self.pan_to_owner[pan_clean] = owner_normalized
        self.customer_key_to_owner[customer_key] = owner_normalized

        self._log(
            f"Identity registered: {owner_normalized} | Customer Key: {customer_key}"
        )
        return True

    def get_owner_by_customer_key(self, customer_key: str) -> Optional[Dict[str, Any]]:
        """Get owner information by customer key.

        Args:
            customer_key: The unique customer key

        Returns:
            Dictionary with owner information or None if not found
        """
        if customer_key in self.customer_key_to_owner:
            owner_name = self.customer_key_to_owner[customer_key]
            owner_info = self.identity_registry[owner_name].copy()
            owner_info["name"] = owner_name
            return owner_info
        return None

    def add_property(
        self,
        property_key: str,
        owner: str,
        address: str,
        pincode: str,
        value: float,
        aadhar_no: str,
        pan_no: str,
        survey_no: str,
        rtc_no: str = "",
        village: str = "",
        taluk: str = "",
        district: str = "",
        state: str = "",
        land_area: str = "",
        land_type: str = "",
        description: str = "",
        additional_info: Dict[str, Any] = None,
    ) -> Block:
        """
        Add a new property to the ledger (Indian Standards).

        Args:
            property_key: Unique identifier for the property
            owner: Current owner's name
            address: Property address
            pincode: Postal pincode
            value: Property value in INR
            aadhar_no: Owner's 12-digit Aadhar number
            pan_no: Owner's PAN card number
            survey_no: Survey/Map number of the property
            rtc_no: RTC (Record of Rights, Tenancy and Crops) number
            village: Village name
            taluk: Taluk/Tehsil name
            district: District name
            state: State name
            land_area: Area of land (e.g., "2 acres", "500 sq ft")
            land_type: Type of land (agricultural, residential, commercial)
            description: Optional description
            additional_info: Any additional property details

        Returns:
            The newly created block
        """
        if property_key in self.property_index:
            raise ValueError(
                f"Property with key '{property_key}' already exists. "
                "Use transfer_property() for ownership changes."
            )

        # Validate Aadhar number
        if not self.validate_aadhar(aadhar_no):
            raise ValueError("Invalid Aadhar number. Must be 12 digits.")

        # Validate PAN number
        if not self.validate_pan(pan_no):
            raise ValueError("Invalid PAN number. Must be in format: ABCDE1234F")

        # Register or validate owner identity (ensures Aadhar and PAN uniqueness)
        self.register_or_validate_identity(owner, aadhar_no, pan_no)

        # Validate and register survey number uniqueness
        self.validate_survey_uniqueness(survey_no)

        # Get customer key for the owner
        owner_normalized = owner.strip()
        customer_key = self.identity_registry[owner_normalized]["customer_key"]

        data = {
            "type": "registration",
            "owner": owner,
            "customer_key": customer_key,
            "aadhar_no": aadhar_no.replace(" ", "").replace("-", ""),
            "pan_no": pan_no.upper(),
            "address": address,
            "pincode": pincode,
            "value": value,
            "survey_no": survey_no,
            "rtc_no": rtc_no,
            "location": {
                "village": village,
                "taluk": taluk,
                "district": district,
                "state": state,
            },
            "land_details": {"area": land_area, "type": land_type},
            "description": description,
            "additional_info": additional_info or {},
        }

        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now().isoformat(),
            data=data,
            previous_hash=self.get_latest_block().hash,
            property_key=property_key,
        )

        self.chain.append(new_block)
        self.property_index[property_key] = [new_block.index]

        # Register survey number to property mapping
        self.survey_to_property[survey_no.strip()] = property_key

        self._log(f"Property '{property_key}' registered successfully")
        return new_block

    def transfer_property(
        self,
        property_key: str,
        new_owner: str,
        new_owner_aadhar: str,
        new_owner_pan: str,
        transfer_value: float = None,
        transfer_reason: str = "sale",
        stamp_duty_paid: float = None,
        registration_fee: float = None,
        additional_info: Dict[str, Any] = None,
    ) -> Block:
        """
        Transfer property ownership (inheritance or sale).

        Args:
            property_key: The property's unique identifier
            new_owner: New owner's name
            new_owner_aadhar: New owner's Aadhar number
            new_owner_pan: New owner's PAN card number
            transfer_value: Value at transfer in INR (optional)
            transfer_reason: Reason for transfer (e.g., 'sale', 'inheritance', 'gift')
            stamp_duty_paid: Stamp duty amount paid
            registration_fee: Registration fee paid
            additional_info: Additional transfer details

        Returns:
            The newly created transfer block
        """
        if property_key not in self.property_index:
            raise ValueError(f"Property with key '{property_key}' not found.")

        # Validate new owner's Aadhar
        if not self.validate_aadhar(new_owner_aadhar):
            raise ValueError("Invalid Aadhar number for new owner. Must be 12 digits.")

        # Validate new owner's PAN
        if not self.validate_pan(new_owner_pan):
            raise ValueError(
                "Invalid PAN number for new owner. Must be in format: ABCDE1234F"
            )

        # Register or validate new owner identity (ensures Aadhar and PAN uniqueness)
        self.register_or_validate_identity(new_owner, new_owner_aadhar, new_owner_pan)

        # Get current property state
        current_state = self.get_property_current_state(property_key)
        previous_owner = current_state["owner"]

        # Prevent self-transfer: owner cannot sell property to themselves
        if previous_owner.strip().lower() == new_owner.strip().lower():
            raise ValueError(
                f"Cannot transfer property to the same owner. "
                f"'{previous_owner}' already owns this property."
            )

        # Get customer keys
        new_owner_normalized = new_owner.strip()
        new_owner_customer_key = self.identity_registry[new_owner_normalized][
            "customer_key"
        ]

        # Determine actual transfer value
        actual_transfer_value = transfer_value or current_state.get("value")

        # Calculate default stamp duty (2%) and registration fee (5%) if not provided
        if stamp_duty_paid is None:
            stamp_duty_paid = actual_transfer_value * 0.02
        if registration_fee is None:
            registration_fee = actual_transfer_value * 0.05

        # Calculate new property value after transfer (includes stamp duty and registration fees)
        new_property_value = actual_transfer_value + stamp_duty_paid + registration_fee

        data = {
            "type": "transfer",
            "transfer_reason": transfer_reason,
            "previous_owner": previous_owner,
            "previous_owner_aadhar": current_state.get("aadhar_no", ""),
            "previous_customer_key": current_state.get("customer_key", ""),
            "new_owner": new_owner,
            "new_owner_customer_key": new_owner_customer_key,
            "new_owner_aadhar": new_owner_aadhar.replace(" ", "").replace("-", ""),
            "new_owner_pan": new_owner_pan.upper(),
            "transfer_value": actual_transfer_value,
            "new_property_value": new_property_value,
            "address": current_state["address"],
            "pincode": current_state.get("pincode", ""),
            "survey_no": current_state.get("survey_no", ""),
            "rtc_no": current_state.get("rtc_no", ""),
            "stamp_duty_paid": stamp_duty_paid,
            "registration_fee": registration_fee,
            "additional_info": additional_info or {},
        }

        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now().isoformat(),
            data=data,
            previous_hash=self.get_latest_block().hash,
            property_key=property_key,
        )

        self.chain.append(new_block)
        self.property_index[property_key].append(new_block.index)

        self._log(
            f"Property '{property_key}' transferred from '{previous_owner}' to '{new_owner}' ({transfer_reason})"
        )
        return new_block

    def inherit_property(
        self,
        property_key: str,
        deceased_owner: str,
        heir: str,
        heir_aadhar: str,
        heir_pan: str,
        relationship: str = "",
        legal_heir_certificate_no: str = "",
        additional_info: Dict[str, Any] = None,
    ) -> Block:
        """
        Transfer property through inheritance with owner validation.

        Args:
            property_key: The property's unique identifier
            deceased_owner: Name of the deceased owner (must match current owner)
            heir: The heir's name
            heir_aadhar: Heir's Aadhar number
            heir_pan: Heir's PAN card number
            relationship: Relationship to previous owner
            legal_heir_certificate_no: Legal heir certificate number
            additional_info: Additional inheritance details

        Returns:
            The newly created inheritance block

        Raises:
            ValueError: If property not found or deceased owner name doesn't match
        """
        # Validate property exists
        if property_key not in self.property_index:
            raise ValueError(f"Property with key '{property_key}' not found.")

        # Get current property state to verify owner
        current_state = self.get_property_current_state(property_key)
        current_owner = current_state["owner"]

        # Validate deceased owner name matches current owner
        if current_owner.strip().lower() != deceased_owner.strip().lower():
            raise ValueError(
                f"Deceased owner name mismatch. Property '{property_key}' is currently owned by "
                f"'{current_owner}', but you specified '{deceased_owner}'. "
                f"Please verify the correct owner name before recording inheritance."
            )

        info = additional_info or {}
        info["relationship"] = relationship
        info["legal_heir_certificate_no"] = legal_heir_certificate_no

        return self.transfer_property(
            property_key=property_key,
            new_owner=heir,
            new_owner_aadhar=heir_aadhar,
            new_owner_pan=heir_pan,
            transfer_reason="inheritance",
            additional_info=info,
        )

    def get_property_history(self, property_key: str) -> List[Dict[str, Any]]:
        """
        Retrieve complete history of a property by its key.

        Args:
            property_key: The property's unique identifier

        Returns:
            List of all blocks related to this property
        """
        if property_key not in self.property_index:
            raise ValueError(f"Property with key '{property_key}' not found.")

        block_indices = self.property_index[property_key]
        history = [self.chain[idx].to_dict() for idx in block_indices]
        return history

    def get_property_current_state(self, property_key: str) -> Dict[str, Any]:
        """
        Get the current state of a property.

        Args:
            property_key: The property's unique identifier

        Returns:
            Current property details including owner, address, value
        """
        if property_key not in self.property_index:
            raise ValueError(f"Property with key '{property_key}' not found.")

        # Get the latest block for this property
        latest_index = self.property_index[property_key][-1]
        latest_block = self.chain[latest_index]

        # Build current state from history
        history = self.get_property_history(property_key)

        # Start with registration data
        registration = history[0]["data"]
        location = registration.get("location", {})
        land_details = registration.get("land_details", {})

        current_state = {
            "property_key": property_key,
            "owner": registration["owner"],
            "customer_key": registration.get("customer_key", ""),
            "aadhar_no": registration.get("aadhar_no", ""),
            "pan_no": registration.get("pan_no", ""),
            "address": registration["address"],
            "pincode": registration.get("pincode", ""),
            "value": registration["value"],
            "survey_no": registration.get("survey_no", ""),
            "rtc_no": registration.get("rtc_no", ""),
            # Flatten location fields for template compatibility
            "village": location.get("village", ""),
            "taluk": location.get("taluk", ""),
            "district": location.get("district", ""),
            "state": location.get("state", ""),
            # Flatten land details for template compatibility
            "land_area": land_details.get("area", ""),
            "land_type": land_details.get("type", ""),
            "description": registration.get("description", ""),
            "registered_at": history[0]["timestamp"],
            "last_updated": latest_block.timestamp,
            "total_transfers": len(history) - 1,
        }

        # Update with latest transfer info if any
        if len(history) > 1:
            latest_data = history[-1]["data"]
            current_state["owner"] = latest_data["new_owner"]
            current_state["customer_key"] = latest_data.get(
                "new_owner_customer_key", ""
            )
            current_state["aadhar_no"] = latest_data.get("new_owner_aadhar", "")
            current_state["pan_no"] = latest_data.get("new_owner_pan", "")
            # Update value with new_property_value (includes stamp duty and registration fees)
            if latest_data.get("new_property_value"):
                current_state["value"] = latest_data["new_property_value"]

        return current_state

    def get_property(self, property_key: str) -> Optional[Dict[str, Any]]:
        """
        Get current state of a property (alias for get_property_current_state).
        Kept for backward compatibility with existing code.
        """
        try:
            return self.get_property_current_state(property_key)
        except ValueError:
            return None

    def get_block_by_key(
        self, property_key: str, block_index: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific block by property key.

        Args:
            property_key: The property's unique identifier
            block_index: Optional specific block index (defaults to latest)

        Returns:
            Block data as dictionary
        """
        if property_key not in self.property_index:
            return None

        indices = self.property_index[property_key]

        if block_index is not None:
            if block_index not in indices:
                raise ValueError(
                    f"Block index {block_index} not found for property '{property_key}'"
                )
            return self.chain[block_index].to_dict()

        # Return latest block for this property
        return self.chain[indices[-1]].to_dict()

    def search_by_owner(self, owner: str) -> List[Dict[str, Any]]:
        """
        Find all properties currently owned by a specific owner (exact match).

        Args:
            owner: Owner's name/ID to search for

        Returns:
            List of property current states
        """
        results = []
        for property_key in self.property_index:
            try:
                state = self.get_property_current_state(property_key)
                if state["owner"].lower() == owner.lower():
                    results.append(state)
            except:
                continue
        return results

    def search_by_owner_details(
        self, customer_key: str, pan: str, aadhar: str
    ) -> List[Dict[str, Any]]:
        """
        Find properties matching owner's Customer Key, PAN, and Aadhaar.
        """
        results = []
        for property_key in self.property_index:
            try:
                state = self.get_property_current_state(property_key)
                if (
                    state["customer_key"] == customer_key
                    and state["pan_no"] == pan.upper()
                    and state["aadhar_no"] == aadhar.replace(" ", "").replace("-", "")
                ):
                    results.append(state)
            except:
                continue
        return results

    def _calculate_fuzzy_score(self, query: str, target: str) -> float:
        """
        Calculate fuzzy matching score between query and target strings.
        Uses a combination of substring matching and character similarity.

        Args:
            query: Search query string
            target: Target string to match against

        Returns:
            Float score between 0 and 100 (higher = better match)
        """
        query = query.lower().strip()
        target = target.lower().strip()

        if not query or not target:
            return 0.0

        # Exact match
        if query == target:
            return 100.0

        # Query is a substring of target (partial match)
        if query in target:
            return 90.0 + (len(query) / len(target)) * 10

        # Target starts with query
        if target.startswith(query):
            return 85.0 + (len(query) / len(target)) * 10

        # Target contains all words from query
        query_words = query.split()
        target_words = target.split()

        if all(any(qw in tw for tw in target_words) for qw in query_words):
            return 80.0

        # Token-based matching
        matching_words = sum(
            1 for qw in query_words if any(qw in tw or tw in qw for tw in target_words)
        )
        if query_words:
            word_score = (matching_words / len(query_words)) * 70
            if word_score > 30:
                return word_score

        # Character-level similarity (Levenshtein-like approach)
        # Calculate common characters ratio
        query_chars = set(query.replace(" ", ""))
        target_chars = set(target.replace(" ", ""))

        if query_chars and target_chars:
            common = len(query_chars.intersection(target_chars))
            total = len(query_chars.union(target_chars))
            char_score = (common / total) * 50

            # Boost if first character matches
            if query[0] == target[0]:
                char_score += 10

            return char_score

        return 0.0

    def unified_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Unified search across all property fields with intelligent matching.
        Searches: owner name, property ID, customer ID, survey number, RTC number,
        aadhar, PAN, village, district, taluk, pincode, address.

        Args:
            query: Search query string

        Returns:
            List of matching properties sorted by relevance
        """
        results = []
        search_query = query.strip().lower()

        if not search_query:
            return results

        # Normalize query for identity document searches (remove spaces/dashes)
        query_normalized = search_query.replace(" ", "").replace("-", "")

        for property_key in self.property_index:
            if property_key == "GENESIS":
                continue

            try:
                state = self.get_property_current_state(property_key)
                best_score = 0.0
                matched_field = ""

                # Define searchable fields with their weights
                searchable_fields = {
                    "property_key": {
                        "value": state.get("property_key", ""),
                        "weight": 1.0,
                        "normalize": False,
                    },
                    "owner": {
                        "value": state.get("owner", ""),
                        "weight": 1.0,
                        "normalize": False,
                        "fuzzy": True,
                    },
                    "customer_key": {
                        "value": state.get("customer_key", ""),
                        "weight": 0.95,
                        "normalize": False,
                    },
                    "survey_no": {
                        "value": state.get("survey_no", ""),
                        "weight": 0.9,
                        "normalize": False,
                    },
                    "rtc_no": {
                        "value": state.get("rtc_no", ""),
                        "weight": 0.9,
                        "normalize": False,
                    },
                    "aadhar_no": {
                        "value": state.get("aadhar_no", ""),
                        "weight": 0.85,
                        "normalize": True,
                    },
                    "pan_no": {
                        "value": state.get("pan_no", ""),
                        "weight": 0.85,
                        "normalize": False,
                    },
                    "village": {
                        "value": state.get("village", ""),
                        "weight": 0.7,
                        "normalize": False,
                    },
                    "district": {
                        "value": state.get("district", ""),
                        "weight": 0.7,
                        "normalize": False,
                    },
                    "taluk": {
                        "value": state.get("taluk", ""),
                        "weight": 0.7,
                        "normalize": False,
                    },
                    "pincode": {
                        "value": state.get("pincode", ""),
                        "weight": 0.8,
                        "normalize": False,
                    },
                    "address": {
                        "value": state.get("address", ""),
                        "weight": 0.6,
                        "normalize": False,
                    },
                }

                for field_name, field_config in searchable_fields.items():
                    field_value = field_config["value"]
                    if not field_value:
                        continue

                    # Normalize if needed (for aadhar)
                    if field_config.get("normalize"):
                        field_value_clean = (
                            field_value.replace(" ", "").replace("-", "").lower()
                        )
                        compare_query = query_normalized
                    else:
                        field_value_clean = field_value.lower()
                        compare_query = search_query

                    score = 0.0

                    # Exact match
                    if compare_query == field_value_clean:
                        score = 100.0
                    # Starts with query
                    elif field_value_clean.startswith(compare_query):
                        score = (
                            90.0 + (len(compare_query) / len(field_value_clean)) * 10
                        )
                    # Contains query
                    elif compare_query in field_value_clean:
                        score = (
                            75.0 + (len(compare_query) / len(field_value_clean)) * 15
                        )
                    # Use fuzzy matching for owner name
                    elif field_config.get("fuzzy"):
                        score = self._calculate_fuzzy_score(search_query, field_value)

                    # Apply field weight
                    weighted_score = score * field_config["weight"]

                    if weighted_score > best_score:
                        best_score = weighted_score
                        matched_field = field_name

                # Include if score is above threshold
                if best_score >= 35.0:
                    state["_match_score"] = round(best_score, 1)
                    state["_matched_field"] = matched_field
                    results.append(state)

            except Exception:
                continue

        # Sort by match score (highest first)
        results.sort(key=lambda x: x.get("_match_score", 0), reverse=True)
        return results

    def is_chain_valid(self) -> bool:
        """Verify the integrity of the blockchain."""
        if not self.chain:
            self._log("Blockchain is empty", "error")
            return False

        if len(self.chain) == 1:
            # Only genesis block
            genesis = self.chain[0]
            if genesis.hash != genesis.calculate_hash():
                self._log("Genesis block hash is invalid", "error")
                return False
            self._log("Blockchain is valid (genesis only)")
            return True

        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if current hash is correct
            calculated_hash = current_block.calculate_hash()
            if current_block.hash != calculated_hash:
                self._log(
                    f"Invalid hash at block {i} ({current_block.property_key})", "error"
                )
                self._log(f"  Stored: {current_block.hash}", "error")
                self._log(f"  Calculated: {calculated_hash}", "error")
                return False

            # Check if previous hash reference is correct
            if current_block.previous_hash != previous_block.hash:
                self._log(
                    f"Invalid chain link at block {i} ({current_block.property_key})",
                    "error",
                )
                self._log(
                    f"  Block {i} previous_hash: {current_block.previous_hash}", "error"
                )
                self._log(f"  Block {i - 1} hash: {previous_block.hash}", "error")
                return False

        self._log("Blockchain is valid")
        return True

    def is_valid(self) -> tuple[bool, str]:
        """
        Validate blockchain integrity (alternative format for compatibility).
        Returns tuple of (is_valid, message).
        """
        if self.is_chain_valid():
            return True, "Blockchain is valid"
        return False, "Blockchain validation failed"

    def validate_with_details(self) -> tuple[bool, str, List[str]]:
        """
        Validate blockchain integrity with detailed error information.
        Returns tuple of (is_valid, summary_message, detailed_logs).
        """
        # Clear previous logs
        self.logs = []

        is_valid = self.is_chain_valid()
        summary = "Blockchain is valid" if is_valid else "Blockchain validation failed"

        # Return validation result, summary, and recent logs
        return is_valid, summary, self.logs[-10:]  # Last 10 log messages

    def get_all_properties(self) -> List[Dict[str, Any]]:
        """Get current state of all registered properties."""
        return [
            self.get_property_current_state(key)
            for key in self.property_index
            if key != "GENESIS"
        ]

    def get_chain_info(self) -> Dict:
        """Get blockchain statistics."""
        return {
            "total_blocks": len(self.chain),
            "total_properties": len([k for k in self.property_index if k != "GENESIS"]),
            "latest_hash": self.get_latest_block().hash,
        }

    def print_chain(self) -> str:
        """Return the entire blockchain as a formatted string."""
        output = []
        output.append("=" * 60)
        output.append("PROPERTY LEDGER BLOCKCHAIN")
        output.append("=" * 60)
        for block in self.chain:
            output.append(f"\nBlock #{block.index}")
            output.append(f"  Timestamp: {block.timestamp}")
            output.append(f"  Property Key: {block.property_key}")
            output.append(f"  Data: {json.dumps(block.data, indent=4)}")
            output.append(f"  Previous Hash: {block.previous_hash[:20]}...")
            output.append(f"  Hash: {block.hash[:20]}...")
            output.append("-" * 60)
        return "\n".join(output)

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using SHA-256 based encryption with base64 encoding."""
        # Create a key from the data itself (deterministic but obfuscated)
        key = hashlib.sha256(b"pawperty_blockchain_key").digest()

        # XOR encryption with the key (repeating key as needed)
        encrypted_bytes = bytearray()
        data_bytes = data.encode("utf-8")

        for i, byte in enumerate(data_bytes):
            encrypted_bytes.append(byte ^ key[i % len(key)])

        # Encode as base64 for safe storage
        return base64.b64encode(encrypted_bytes).decode("utf-8")

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data that was encrypted with _encrypt_data."""
        # Create the same key
        key = hashlib.sha256(b"pawperty_blockchain_key").digest()

        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_data.encode("utf-8"))

        # XOR decryption with the key
        decrypted_bytes = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            decrypted_bytes.append(byte ^ key[i % len(key)])

        return decrypted_bytes.decode("utf-8")

    def _save_blockchain(self) -> bool:
        """Save blockchain to an encrypted JSON file."""
        try:
            # Ensure storage folder exists
            if not os.path.exists(self.STORAGE_FOLDER):
                os.makedirs(self.STORAGE_FOLDER)

            # Prepare blockchain data
            blockchain_data = {
                "chain": [block.to_dict() for block in self.chain],
                "property_index": self.property_index,
                "identity_registry": self.identity_registry,
                "aadhar_to_owner": self.aadhar_to_owner,
                "pan_to_owner": self.pan_to_owner,
                "customer_key_to_owner": self.customer_key_to_owner,
                "survey_to_property": self.survey_to_property,
                "saved_at": datetime.now().isoformat(),
            }

            # Convert to JSON string
            json_data = json.dumps(blockchain_data, indent=2)

            # Encrypt the data
            encrypted_data = self._encrypt_data(json_data)

            # Remove read-only attribute before writing (Windows)
            if os.path.exists(self.STORAGE_FILE):
                try:
                    subprocess.run(
                        ["attrib", "-R", self.STORAGE_FILE],
                        check=False,
                        capture_output=True,
                    )
                except:
                    pass

            # Save to file
            with open(self.STORAGE_FILE, "w") as f:
                f.write(encrypted_data)

            # Make file read-only on Windows
            try:
                subprocess.run(
                    ["attrib", "+R", self.STORAGE_FILE],
                    check=False,
                    capture_output=True,
                )
            except:
                pass  # Silently fail if not on Windows or attrib command not available

            self._log(
                f"Blockchain saved to read-only encrypted file: {self.STORAGE_FILE}"
            )
            
            # Automatically backup to database if available
            try:
                self.backup_to_database(admin_id=1, backup_name=f"Auto-backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as db_err:
                self._log(f"Note: Database backup skipped (this is normal if DB not initialized): {db_err}", "info")
            
            return True

        except Exception as e:
            self._log(f"Error saving blockchain: {e}", "error")
            return False

    def _load_blockchain(self) -> bool:
        """Load blockchain from encrypted JSON file and delete the file after loading."""
        try:
            # Check if file exists
            if not os.path.exists(self.STORAGE_FILE):
                self._log("Storage file does not exist", "error")
                return False

            # Read encrypted data - try text mode first, then binary
            encrypted_data = None
            try:
                with open(self.STORAGE_FILE, "r", encoding="utf-8") as f:
                    encrypted_data = f.read()
                self._log(f"Read {len(encrypted_data)} chars as UTF-8 text")
            except UnicodeDecodeError as ude:
                self._log(f"UTF-8 decode failed: {ude}, trying binary mode")
                # File might be binary, read as binary and decode
                with open(self.STORAGE_FILE, "rb") as f:
                    encrypted_data = f.read().decode("utf-8", errors="replace")
                self._log(f"Read {len(encrypted_data)} chars via binary mode")

            # Decrypt the data
            try:
                json_data = self._decrypt_data(encrypted_data)
                self._log(f"Decrypted to {len(json_data)} chars")
            except Exception as decrypt_err:
                self._log(f"Decryption failed: {decrypt_err}", "error")
                return False

            # Parse JSON
            try:
                blockchain_data = json.loads(json_data)
                self._log(
                    f"Parsed JSON successfully, found {len(blockchain_data.get('chain', []))} blocks"
                )
            except json.JSONDecodeError as json_err:
                self._log(f"JSON parse failed: {json_err}", "error")
                self._log(
                    f"First 100 chars of decrypted data: {json_data[:100]}", "error"
                )
                return False

            # Reconstruct blockchain
            self.chain = []
            for block_dict in blockchain_data["chain"]:
                block = Block(
                    index=block_dict["index"],
                    timestamp=block_dict["timestamp"],
                    data=block_dict["data"],
                    previous_hash=block_dict["previous_hash"],
                    property_key=block_dict["property_key"],
                )
                # Restore the original hash from storage (don't recalculate)
                # With deterministic JSON serialization, this should match calculate_hash()
                block.hash = block_dict["hash"]
                self.chain.append(block)

            # Restore property index
            self.property_index = blockchain_data["property_index"]

            # Restore identity registry
            self.identity_registry = blockchain_data.get("identity_registry", {})
            self.aadhar_to_owner = blockchain_data.get("aadhar_to_owner", {})
            self.pan_to_owner = blockchain_data.get("pan_to_owner", {})
            self.customer_key_to_owner = blockchain_data.get(
                "customer_key_to_owner", {}
            )
            self.survey_to_property = blockchain_data.get("survey_to_property", {})

            # Validate the loaded blockchain
            if self.is_chain_valid():
                # Additional validation: check that property_index references valid block indices
                try:
                    for property_key, indices in self.property_index.items():
                        for idx in indices:
                            if idx >= len(self.chain):
                                self._log(
                                    f"Property {property_key} references invalid block index {idx} (chain has {len(self.chain)} blocks)",
                                    "error",
                                )
                                return False
                    return True
                except Exception as e:
                    self._log(f"Error validating property_index: {e}", "error")
                    return False
            else:
                self._log("Warning: Loaded blockchain failed validation", "error")
                return False

        except Exception as e:
            self._log(f"Error loading blockchain: {e}", "error")
            # Don't delete the file - it might be needed for debugging
            return False

    def get_encrypted_data(self) -> str:
        """Get the encrypted blockchain data as a string for database storage."""
        # Prepare blockchain data
        blockchain_data = {
            "chain": [block.to_dict() for block in self.chain],
            "property_index": self.property_index,
            "identity_registry": self.identity_registry,
            "aadhar_to_owner": self.aadhar_to_owner,
            "pan_to_owner": self.pan_to_owner,
            "customer_key_to_owner": self.customer_key_to_owner,
            "survey_to_property": self.survey_to_property,
            "saved_at": datetime.now().isoformat(),
        }

        # Convert to JSON string
        json_data = json.dumps(blockchain_data, indent=2)

        # Encrypt the data
        encrypted_data = self._encrypt_data(json_data)
        return encrypted_data

    def load_from_encrypted_data(self, encrypted_data: str) -> bool:
        """Load blockchain from encrypted data string (for database restore)."""
        try:
            # Decrypt the data
            json_data = self._decrypt_data(encrypted_data)

            # Parse JSON
            blockchain_data = json.loads(json_data)

            # Reconstruct blockchain
            self.chain = []
            for block_dict in blockchain_data["chain"]:
                block = Block(
                    index=block_dict["index"],
                    timestamp=block_dict["timestamp"],
                    data=block_dict["data"],
                    previous_hash=block_dict["previous_hash"],
                    property_key=block_dict["property_key"],
                )
                # Restore the original hash
                block.hash = block_dict["hash"]
                self.chain.append(block)

            # Restore property index
            self.property_index = blockchain_data["property_index"]

            # Restore identity registry
            self.identity_registry = blockchain_data.get("identity_registry", {})
            self.aadhar_to_owner = blockchain_data.get("aadhar_to_owner", {})
            self.pan_to_owner = blockchain_data.get("pan_to_owner", {})
            self.customer_key_to_owner = blockchain_data.get(
                "customer_key_to_owner", {}
            )
            self.survey_to_property = blockchain_data.get("survey_to_property", {})

            # Validate the loaded blockchain
            if self.is_chain_valid():
                return True
            else:
                self._log("Warning: Loaded blockchain failed validation", "error")
                return False

        except Exception as e:
            self._log(f"Error loading blockchain from encrypted data: {e}", "error")
            return False

    def attempt_recovery_from_encrypted_data(
        self, encrypted_data: str
    ) -> tuple[bool, str]:
        """
        Attempt to recover as much valid data as possible from corrupted backup.
        Returns (success, message) where success indicates if any data was recovered.
        """
        try:
            # Decrypt the data
            json_data = self._decrypt_data(encrypted_data)

            # Parse JSON
            blockchain_data = json.loads(json_data)

            # Try to load blocks one by one, stopping at first invalid block
            valid_blocks = []
            for i, block_dict in enumerate(blockchain_data["chain"]):
                try:
                    block = Block(
                        index=block_dict["index"],
                        timestamp=block_dict["timestamp"],
                        data=block_dict["data"],
                        previous_hash=block_dict["previous_hash"],
                        property_key=block_dict["property_key"],
                    )
                    # Restore the original hash
                    block.hash = block_dict["hash"]

                    # Check if this block is valid by itself
                    if block.hash == block.calculate_hash():
                        valid_blocks.append((block, block_dict))
                    else:
                        self._log(
                            f"Block {i} has invalid hash, stopping recovery", "error"
                        )
                        break
                except Exception as e:
                    self._log(f"Error reconstructing block {i}: {e}", "error")
                    break

            if not valid_blocks:
                return False, "No valid blocks found in backup"

            # Reconstruct with valid blocks
            self.chain = [block for block, _ in valid_blocks]

            # Rebuild metadata based on recovered blocks
            try:
                # Get original metadata
                original_property_index = blockchain_data.get("property_index", {})
                original_identity_registry = blockchain_data.get(
                    "identity_registry", {}
                )
                original_aadhar_to_owner = blockchain_data.get("aadhar_to_owner", {})
                original_pan_to_owner = blockchain_data.get("pan_to_owner", {})
                original_customer_key_to_owner = blockchain_data.get(
                    "customer_key_to_owner", {}
                )
                original_survey_to_property = blockchain_data.get(
                    "survey_to_property", {}
                )

                # Rebuild property_index for recovered blocks
                self.property_index = {}
                property_keys_seen = set()

                for new_index, (block, original_dict) in enumerate(valid_blocks):
                    property_key = block.property_key
                    if property_key not in property_keys_seen:
                        # This is the first block for this property in our recovered chain
                        self.property_index[property_key] = [new_index]
                        property_keys_seen.add(property_key)
                    else:
                        # Add to existing property's indices
                        if property_key in self.property_index:
                            self.property_index[property_key].append(new_index)

                # Restore identity and survey mappings (these should be valid)
                self.identity_registry = original_identity_registry
                self.aadhar_to_owner = original_aadhar_to_owner
                self.pan_to_owner = original_pan_to_owner
                self.customer_key_to_owner = original_customer_key_to_owner
                self.survey_to_property = original_survey_to_property

                self._log(
                    f"Rebuilt property_index with {len(self.property_index)} properties",
                    "info",
                )

            except Exception as e:
                self._log(f"Error rebuilding metadata: {e}", "error")
                # Initialize empty metadata as fallback
                self.property_index = {}
                self.identity_registry = {}
                self.aadhar_to_owner = {}
                self.pan_to_owner = {}
                self.customer_key_to_owner = {}
                self.survey_to_property = {}

            # Validate what we have
            if self.is_chain_valid():
                return True, f"Successfully recovered {len(self.chain)} valid blocks"
            else:
                return (
                    True,
                    f"Recovered {len(self.chain)} blocks but chain validation failed - data may be incomplete",
                )

        except Exception as e:
            self._log(f"Recovery failed: {e}", "error")
        return False, f"Recovery failed: {str(e)}"

    def _auto_restore_from_ipfs(self) -> bool:
        """
        Automatically restore blockchain from Pinata IPFS using CID from CID manager.
        This is called first during initialization for seamless cloud restoration.

        Returns:
            bool: True if restoration was successful
        """
        try:
            # Use CID manager to get the latest CID from multiple sources
            cid = cid_manager.get_latest_cid()

            if not cid:
                # Fallback to checking environment variable directly
                cid = os.environ.get("PINATA_RESTORE_CID", "").strip()
                if cid:
                    self._log(
                        f"Found Pinata CID in environment variable PINATA_RESTORE_CID: {cid}"
                    )

            # Final fallback: Check if CID file exists in project root (for local development)
            if not cid and os.path.exists(self.PINATA_CID_FILE):
                with open(self.PINATA_CID_FILE, "r") as f:
                    cid = f.read().strip()
                if cid:
                    self._log(f"Found Pinata CID in {self.PINATA_CID_FILE}: {cid}")

            if not cid:
                self._log(
                    f"No IPFS CID found from CID manager or fallback methods - skipping IPFS auto-restore"
                )
                return False

            self._log("Attempting to restore blockchain from Pinata IPFS...")

            # Attempt IPFS restoration
            success = self.restore_from_ipfs(cid)

            if success:
                self._log(
                    f"✅ Successfully auto-restored blockchain from Pinata IPFS (CID: {cid})"
                )
                return True
            else:
                self._log(
                    f"❌ Failed to restore from Pinata IPFS (CID: {cid})", "error"
                )
                self._log("Will fall back to other restoration methods...", "error")
                return False

        except Exception as e:
            self._log(f"IPFS auto-restore error: {str(e)}", "error")
            self._log("Will fall back to other restoration methods...", "error")
            return False

    def _auto_restore_from_backup(self) -> bool:
        """
        Automatically restore blockchain from the most recent database backup.
        This is called during initialization if no local blockchain file exists.

        Returns:
            bool: True if restoration was successful
        """
        try:
            # Import database models here to avoid circular imports
            from models import BlockchainBackup, db

            # Get the most recent backup from database
            latest_backup = BlockchainBackup.query.order_by(
                BlockchainBackup.created_at.desc()
            ).first()

            if not latest_backup:
                self._log("No database backups found for auto-restore", "error")
                return False

            self._log(
                f"Found latest backup: {latest_backup.name} (created {latest_backup.created_at})"
            )

            # Try to load from backup data
            success = self.load_from_encrypted_data(latest_backup.backup_data)

            if success:
                self._log(
                    f"✅ Auto-restored blockchain from database backup: {latest_backup.name}"
                )
                self._log(f"   Loaded {len(self.chain)} blocks")

                # Save to local storage so it's persistent for future startups
                if self._save_blockchain():
                    self._log("   Blockchain saved to local storage for future use")
                else:
                    self._log("   Warning: Failed to save to local storage", "error")

                return True
            else:
                self._log(f"Failed to load from backup: {latest_backup.name}", "error")
                return False

        except Exception as e:
            self._log(f"Auto-restore failed: {str(e)}", "error")
            return False

    def save_and_exit(self) -> None:
        """Save blockchain to encrypted storage before exiting."""
        self._save_blockchain()
        
        # Automatically backup to IPFS after saving to disk
        # This ensures persistence even if the server crashes or shutdown hook fails
        if self.PINATA_API_KEY and self.PINATA_SECRET_KEY:
            self._log("Triggering immediate IPFS backup...")
            self.backup_to_ipfs()

    def save_to_file(self, filename: str = None):
        """
        Save blockchain (compatibility method for existing code).
        Uses encrypted storage by default.
        """
        if filename:
            # Ensure folder exists if filename has a directory
            folder = os.path.dirname(filename)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)

            # If specific filename provided, use encrypted storage with that name
            original_file = self.STORAGE_FILE
            self.STORAGE_FILE = filename
            result = self._save_blockchain()
            self.STORAGE_FILE = original_file
            return result
        else:
            return self._save_blockchain()

    @staticmethod
    def load_from_file(filename: str = None) -> "PropertyBlockchain":
        """
        Load blockchain from file (compatibility method for existing code).
        Uses encrypted storage by default.
        """
        blockchain = PropertyBlockchain(verbose=False)
        if filename and filename != blockchain.STORAGE_FILE:
            # If specific filename provided, try to load from it
            original_file = blockchain.STORAGE_FILE
            blockchain.STORAGE_FILE = filename
            blockchain._load_blockchain()
            blockchain.STORAGE_FILE = original_file
        return blockchain

    def to_dict(self) -> List[Dict]:
        """Convert entire blockchain to dictionary format."""
        return [block.to_dict() for block in self.chain]

    def backup_to_ipfs(self) -> Optional[str]:
        """
        Backup blockchain to IPFS using Pinata (FREE decentralized storage).
        Returns the IPFS CID (Content Identifier) if successful.
        """
        if not os.path.exists(self.STORAGE_FILE):
            self._log("No blockchain file found to backup!", "error")
            return None

        try:
            self._log("Starting IPFS backup via Pinata...")
            url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

            # Check if API keys are set
            if (
                not self.PINATA_API_KEY
                or not self.PINATA_SECRET_KEY
                or self.PINATA_API_KEY == "your_pinata_api_key_here"
                or self.PINATA_SECRET_KEY == "your_pinata_secret_key_here"
            ):
                self._log(
                    "ERROR: Pinata API keys not configured! Please set PINATA_API_KEY and PINATA_SECRET_KEY environment variables.",
                    "error",
                )
                return None

            headers = {
                "pinata_api_key": self.PINATA_API_KEY,
                "pinata_secret_api_key": self.PINATA_SECRET_KEY,
            }

            # Add metadata to identify this backup
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            payload = {
                "pinataMetadata": json.dumps(
                    {
                        "name": f"blockchain_backup_{timestamp}",
                        "keyvalues": {
                            "project": "PropertyBlockchain",
                            "blocks": str(len(self.chain)),
                            "timestamp": timestamp,
                        },
                    }
                )
            }

            file_size = os.path.getsize(self.STORAGE_FILE)
            self._log(f"Uploading {file_size} bytes to Pinata...")

            with open(self.STORAGE_FILE, "rb") as file:
                files = {"file": (os.path.basename(self.STORAGE_FILE), file)}
                response = requests.post(
                    url, files=files, headers=headers, data=payload, timeout=60
                )

            self._log(f"Pinata API response status: {response.status_code}")

            if response.status_code == 200:
                cid = response.json()["IpfsHash"]
                self._log(f"✅ Blockchain backed up to IPFS!")
                self._log(f"   CID: {cid}")
                self._log(f"   View at: https://gateway.pinata.cloud/ipfs/{cid}")

                # Save CID using CID manager for persistent storage without database
                metadata = {
                    "blocks_count": len(self.chain),
                    "file_size": file_size,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Get the PREVIOUS CID before saving the new one
                old_cid = cid_manager.get_latest_cid()

                if cid_manager.save_cid(cid, metadata):
                    self._log(f"✅ Saved CID for automatic restoration on next startup")
                    
                    # Clean up old CID to save space (Pinata optimization)
                    if old_cid and old_cid != cid:
                        self._log(f"Cleaning up old backup: {old_cid}")
                        cid_manager.unpin_cid(old_cid)
                else:
                    self._log(f"Warning: Could not save CID via CID manager", "error")

                # Also save to file for local development backup
                try:
                    with open(self.PINATA_CID_FILE, "w") as f:
                        f.write(cid)
                    self._log(f"✅ Saved CID to {self.PINATA_CID_FILE} file as backup")
                except Exception as e:
                    self._log(f"Warning: Could not save CID to file: {e}", "error")

                return cid
            else:
                self._log(
                    f"IPFS backup failed with status {response.status_code}", "error"
                )
                self._log(f"Response: {response.text[:500]}", "error")
                return None

        except Exception as e:
            self._log(f"IPFS backup error: {str(e)}", "error")
            import traceback

            traceback.print_exc()
            return None

    def restore_from_ipfs(self, cid: str) -> bool:
        """
        Restore blockchain from IPFS using a CID.
        Downloads the encrypted file from IPFS, saves it to blocks folder,
        then restores from that saved file.
        WARNING: This will overwrite your current blockchain!

        Args:
            cid: The IPFS Content Identifier from a previous backup
        """
        import re

        try:
            # Ensure storage folder exists
            if not os.path.exists(self.STORAGE_FOLDER):
                os.makedirs(self.STORAGE_FOLDER)

            content = None
            last_error = None

            # The CID might point to a folder containing the file, so try both:
            # 1. Direct CID (if it's the raw file)
            # 2. CID/filename (if it's a folder containing the file)
            urls_to_try = [
                # Try as folder containing the file
                f"https://gateway.pinata.cloud/ipfs/{cid}/blockchain_data.encrypted",
                f"https://ipfs.io/ipfs/{cid}/blockchain_data.encrypted",
                f"https://dweb.link/ipfs/{cid}/blockchain_data.encrypted",
                # Try direct CID with raw format
                f"https://gateway.pinata.cloud/ipfs/{cid}?format=raw",
                f"https://ipfs.io/ipfs/{cid}?format=raw",
                # Try direct CID (might be the raw file itself)
                f"https://gateway.pinata.cloud/ipfs/{cid}",
                f"https://ipfs.io/ipfs/{cid}",
            ]

            for url in urls_to_try:
                try:
                    self._log(f"Trying: {url}")
                    response = requests.get(
                        url,
                        timeout=60,
                        headers={
                            "Accept": "application/octet-stream, */*",
                            "User-Agent": "Mozilla/5.0",
                        },
                    )
                    self._log(
                        f"Status: {response.status_code}, Size: {len(response.content)} bytes"
                    )

                    if response.status_code == 200 and len(response.content) > 1000:
                        temp_content = response.content
                        # Check if valid base64 encrypted data
                        try:
                            text_start = temp_content[:100].decode(
                                "utf-8", errors="strict"
                            )
                            if re.match(r"^[A-Za-z0-9+/=]+", text_start):
                                self._log(
                                    f"✓ Valid encrypted data received! ({len(temp_content)} bytes)"
                                )
                                content = temp_content
                                break
                            elif (
                                "<html" in text_start.lower()
                                or "<!doctype" in text_start.lower()
                            ):
                                self._log(f"HTML returned, trying next...")
                                continue
                        except UnicodeDecodeError:
                            # If size is reasonable, might be valid data
                            if len(temp_content) > 1000:
                                content = temp_content
                                break
                    elif response.status_code == 200:
                        self._log(
                            f"File too small ({len(response.content)} bytes), trying next..."
                        )
                except requests.exceptions.Timeout:
                    self._log(f"Timeout", "error")
                    last_error = "Timeout"
                except Exception as e:
                    self._log(f"Error: {str(e)[:50]}", "error")
                    last_error = str(e)

            if content is None:
                self._log(
                    f"All download methods failed. Last error: {last_error}", "error"
                )
                self._log(
                    "The file might be unpinned or the CID format is incorrect.",
                    "error",
                )
                return False

            self._log(f"Downloaded {len(content)} bytes")

            if len(content) < 1000:
                self._log(
                    f"Downloaded file too small ({len(content)} bytes), not a valid blockchain backup",
                    "error",
                )
                return False

            # Save the downloaded file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            downloaded_file = f"blocks/blockchain_from_ipfs_{timestamp}.encrypted"

            with open(downloaded_file, "wb") as file:
                file.write(content)
            self._log(f"Saved to: {downloaded_file}")

            # Backup current blockchain
            import shutil

            if os.path.exists(self.STORAGE_FILE):
                backup_file = f"blocks/blockchain_pre_ipfs_{timestamp}.encrypted"
                shutil.copy(self.STORAGE_FILE, backup_file)
                self._log(f"Backed up current to: {backup_file}")

            # Copy downloaded file to active storage
            shutil.copy(downloaded_file, self.STORAGE_FILE)
            self._log(f"Copied to active storage")

            # Load blockchain
            if self._load_blockchain():
                self._log(f"✅ Blockchain restored from IPFS!")
                self._log(f"   Loaded {len(self.chain)} blocks")
                return True
            else:
                self._log("Failed to load blockchain", "error")
                self._log(f"Downloaded file saved at: {downloaded_file}", "info")
                self._log(f"Try restoring manually via Local Restore", "info")
                return False

        except Exception as e:
            self._log(f"IPFS restore error: {str(e)}", "error")
            import traceback

            traceback.print_exc()
            return False

    def backup_to_database(self, admin_id: int = 1, backup_name: str = None) -> bool:
        """
        Backup blockchain to PostgreSQL database.
        This provides a faster and more reliable restore than IPFS.
        
        Args:
            admin_id: ID of the admin user creating the backup (default: 1)
            backup_name: Optional custom name for the backup
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Import Flask and database within function to avoid circular imports
            from flask import Flask
            from models import db, BlockchainBackup
            
            self._log("Starting database backup...")
            
            # Check if blockchain file exists
            if not os.path.exists(self.STORAGE_FILE):
                self._log("No blockchain file found to backup!", "error")
                return False
            
            # Read encrypted blockchain data
            with open(self.STORAGE_FILE, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
            
            # Generate backup name if not provided
            if not backup_name:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                backup_name = f"Auto-backup {timestamp}"
            
            # Get filename for reference
            filename = os.path.basename(self.STORAGE_FILE)
            
            # Create database backup entry
            backup = BlockchainBackup(
                name=backup_name,
                filename=filename,
                backup_data=encrypted_data,
                created_by=admin_id
            )
            
            # Save to database
            db.session.add(backup)
            db.session.commit()
            
            backup_id = backup.id
            data_size = len(encrypted_data)
            
            self._log(f"✅ Blockchain backed up to database!")
            self._log(f"   Backup ID: {backup_id}")
            self._log(f"   Name: {backup_name}")
            self._log(f"   Size: {data_size} bytes")
            self._log(f"   Blocks: {len(self.chain)}")
            
            return True
            
        except Exception as e:
            self._log(f"Database backup error: {str(e)}", "error")
            import traceback
            traceback.print_exc()
            return False
    
    def restore_from_database(self, backup_id: int = None) -> bool:
        """
        Restore blockchain from PostgreSQL database.
        If backup_id is not provided, uses the most recent backup.
        
        Args:
            backup_id: Specific backup ID to restore, or None for latest
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from flask import Flask
            from models import db, BlockchainBackup
            
            self._log("Starting database restore...")
            
            # Get backup from database
            if backup_id:
                backup = BlockchainBackup.query.get(backup_id)
                if not backup:
                    self._log(f"Backup ID {backup_id} not found in database!", "error")
                    return False
            else:
                # Get most recent backup
                backup = BlockchainBackup.query.order_by(BlockchainBackup.created_at.desc()).first()
                if not backup:
                    self._log("No backups found in database!", "error")
                    return False
            
            self._log(f"Found backup: {backup.name} (ID: {backup.id})")
            self._log(f"Created: {backup.created_at}")
            
            # Ensure storage folder exists
            if not os.path.exists(self.STORAGE_FOLDER):
                os.makedirs(self.STORAGE_FOLDER)
            
            # Backup current blockchain if it exists
            if os.path.exists(self.STORAGE_FILE):
                import shutil
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"blocks/blockchain_pre_db_restore_{timestamp}.encrypted"
                shutil.copy(self.STORAGE_FILE, backup_file)
                self._log(f"Backed up current to: {backup_file}")
            
            # Write encrypted data to file
            with open(self.STORAGE_FILE, 'w', encoding='utf-8') as f:
                f.write(backup.backup_data)
            
            self._log(f"Wrote {len(backup.backup_data)} bytes to {self.STORAGE_FILE}")
            
            # Load blockchain from the restored file
            if self._load_blockchain():
                self._log(f"✅ Blockchain restored from database!")
                self._log(f"   Loaded {len(self.chain)} blocks")
                self._log(f"   Properties: {len([k for k in self.property_index if k != 'GENESIS'])}")
                return True
            else:
                self._log("Failed to load blockchain after restore", "error")
                return False
                
        except Exception as e:
            self._log(f"Database restore error: {str(e)}", "error")
            import traceback
            traceback.print_exc()
            return False
    
    def _auto_restore_from_database(self) -> bool:
        """
        Automatically restore from database on startup if no local blockchain exists.
        This is called during initialization.
        
        Returns:
            bool: True if restore was successful, False otherwise
        """
        try:
            from models import BlockchainBackup
            
            # Check if there are any backups
            backup_count = BlockchainBackup.query.count()
            if backup_count == 0:
                return False
            
            self._log(f"Found {backup_count} database backup(s)")
            
            # Try to restore from latest backup
            return self.restore_from_database()
            
        except Exception as e:
            self._log(f"Auto-restore from database failed: {str(e)}", "error")
            return False
