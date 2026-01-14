"""
CID Manager for Render Deployment
Manages IPFS CID storage and retrieval without database dependency
Uses Render API to update environment variables and Pinata metadata for persistence
"""

import base64
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests


class CIDManager:
    """
    Manages CID storage and retrieval using multiple methods:
    1. Render environment variables (via API)
    2. Pinata metadata search
    3. GitHub Gist (as backup)
    4. Local file (for development)
    """

    def __init__(self):
        # Render API configuration
        self.render_api_key = os.environ.get("RENDER_API_KEY", "")
        self.render_service_id = os.environ.get("RENDER_SERVICE_ID", "")

        # Pinata configuration
        self.pinata_api_key = os.environ.get("PINATA_API_KEY", "")
        self.pinata_secret_key = os.environ.get("PINATA_SECRET_KEY", "")

        # GitHub Gist configuration (optional backup)
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        self.gist_id = os.environ.get("GITHUB_GIST_ID", "")

        # Local file for development
        self.local_cid_file = "latest_cid.txt"
        self.backup_cid_file = ".render_cid_backup.json"

    def save_cid(self, cid: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Save CID using multiple methods for redundancy

        Args:
            cid: The IPFS Content Identifier to save
            metadata: Additional metadata (blocks count, timestamp, etc.)

        Returns:
            bool: True if at least one save method succeeded
        """
        success_count = 0
        metadata = metadata or {}
        metadata.update(
            {
                "cid": cid,
                "timestamp": datetime.now().isoformat(),
                "source": "PawParties-Blockchain",
            }
        )

        # Method 1: Update Render environment variable
        if self._update_render_env(cid):
            print(f"✅ CID saved to Render environment variable")
            success_count += 1

        # Method 2: Save to Pinata metadata (tag the upload)
        if self._save_to_pinata_metadata(cid, metadata):
            print(f"✅ CID tagged in Pinata metadata")
            success_count += 1

        # Method 3: Save to GitHub Gist
        if self._save_to_gist(cid, metadata):
            print(f"✅ CID saved to GitHub Gist")
            success_count += 1

        # Method 4: Save to local file (always do this)
        self._save_to_local_file(cid, metadata)
        print(f"✅ CID saved to local file")
        success_count += 1

        # Method 5: Save to backup JSON file with history
        self._save_to_backup_file(cid, metadata)

        return success_count > 0

    def get_latest_cid(self) -> Optional[str]:
        """
        Retrieve the latest CID using multiple methods

        Returns:
            str: The latest CID if found, None otherwise
        """
        # Priority 1: Check Render environment variable
        cid = os.environ.get("PINATA_LATEST_CID", "").strip()
        if cid:
            print(f"Found CID in Render environment: {cid}")
            return cid

        # Priority 2: Search Pinata for latest backup
        cid = self._get_from_pinata_metadata()
        if cid:
            print(f"Found CID in Pinata metadata: {cid}")
            return cid

        # Priority 3: Check GitHub Gist
        cid = self._get_from_gist()
        if cid:
            print(f"Found CID in GitHub Gist: {cid}")
            return cid

        # Priority 4: Check local backup file
        cid = self._get_from_backup_file()
        if cid:
            print(f"Found CID in backup file: {cid}")
            return cid

        # Priority 5: Check local file
        cid = self._get_from_local_file()
        if cid:
            print(f"Found CID in local file: {cid}")
            return cid

        return None

    def _update_render_env(self, cid: str) -> bool:
        """Update Render environment variable via API"""
        if not (self.render_api_key and self.render_service_id):
            print("⚠️ Render API credentials not configured")
            return False

        try:
            url = (
                f"https://api.render.com/v1/services/{self.render_service_id}/env-vars"
            )
            headers = {
                "Authorization": f"Bearer {self.render_api_key}",
                "Content-Type": "application/json",
            }

            # First, try to update existing variable
            env_vars_response = requests.get(url, headers=headers)
            if env_vars_response.status_code == 200:
                env_vars = env_vars_response.json()

                # Check if PINATA_LATEST_CID exists
                cid_var_exists = False
                for env_var in env_vars:
                    if env_var.get("key") == "PINATA_LATEST_CID":
                        cid_var_exists = True
                        var_id = env_var.get("id")
                        # Update existing variable
                        update_url = f"{url}/{var_id}"
                        update_data = {"value": cid}
                        update_response = requests.patch(
                            update_url, json=update_data, headers=headers
                        )
                        if update_response.status_code == 200:
                            return True
                        break

                # If variable doesn't exist, create it
                if not cid_var_exists:
                    create_data = [{"key": "PINATA_LATEST_CID", "value": cid}]
                    create_response = requests.post(
                        url, json=create_data, headers=headers
                    )
                    if create_response.status_code in [200, 201]:
                        return True

            return False
        except Exception as e:
            print(f"Error updating Render env: {e}")
            return False

    def _save_to_pinata_metadata(self, cid: str, metadata: Dict[str, Any]) -> bool:
        """Save CID to Pinata by updating pin metadata"""
        if not (self.pinata_api_key and self.pinata_secret_key):
            return False

        try:
            url = f"https://api.pinata.cloud/pinning/hashMetadata"
            headers = {
                "pinata_api_key": self.pinata_api_key,
                "pinata_secret_api_key": self.pinata_secret_key,
                "Content-Type": "application/json",
            }

            # Update the metadata of the pinned file
            update_data = {
                "ipfsPinHash": cid,
                "name": f"PawParties_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "keyvalues": {
                    "latest": "true",
                    "timestamp": metadata.get("timestamp", ""),
                    "blocks": str(metadata.get("blocks_count", 0)),
                    "type": "blockchain_backup",
                    "project": "PawParties",
                },
            }

            response = requests.put(url, json=update_data, headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating Pinata metadata: {e}")
            return False

    def _get_from_pinata_metadata(self) -> Optional[str]:
        """Search Pinata for the latest backup by metadata"""
        if not (self.pinata_api_key and self.pinata_secret_key):
            return None

        try:
            url = "https://api.pinata.cloud/data/pinList"
            headers = {
                "pinata_api_key": self.pinata_api_key,
                "pinata_secret_api_key": self.pinata_secret_key,
            }

            # Search for pins with our metadata
            params = {
                "metadata[keyvalues]": json.dumps(
                    {
                        "type": {"value": "blockchain_backup", "op": "eq"},
                        "project": {"value": "PawParties", "op": "eq"},
                    }
                ),
                "pageLimit": 10,
                "pageOffset": 0,
            }

            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                rows = data.get("rows", [])

                # Sort by date_pinned to get the latest
                if rows:
                    sorted_rows = sorted(
                        rows, key=lambda x: x.get("date_pinned", ""), reverse=True
                    )
                    latest = sorted_rows[0]
                    return latest.get("ipfs_pin_hash")

            return None
        except Exception as e:
            print(f"Error searching Pinata: {e}")
            return None

    def _save_to_gist(self, cid: str, metadata: Dict[str, Any]) -> bool:
        """Save CID to GitHub Gist"""
        if not (self.github_token and self.gist_id):
            return False

        try:
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            content = {
                "cid": cid,
                "metadata": metadata,
                "updated_at": datetime.now().isoformat(),
            }

            data = {
                "files": {
                    "pawparties_latest_cid.json": {
                        "content": json.dumps(content, indent=2)
                    }
                }
            }

            response = requests.patch(url, json=data, headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating Gist: {e}")
            return False

    def _get_from_gist(self) -> Optional[str]:
        """Get CID from GitHub Gist"""
        if not (self.github_token and self.gist_id):
            return None

        try:
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                file_content = (
                    data.get("files", {})
                    .get("pawparties_latest_cid.json", {})
                    .get("content", "")
                )
                if file_content:
                    content = json.loads(file_content)
                    return content.get("cid")

            return None
        except Exception as e:
            print(f"Error reading Gist: {e}")
            return None

    def _save_to_local_file(self, cid: str, metadata: Dict[str, Any]) -> None:
        """Save CID to local file"""
        try:
            with open(self.local_cid_file, "w") as f:
                f.write(cid)
        except Exception as e:
            print(f"Error saving to local file: {e}")

    def _get_from_local_file(self) -> Optional[str]:
        """Get CID from local file"""
        try:
            if os.path.exists(self.local_cid_file):
                with open(self.local_cid_file, "r") as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error reading local file: {e}")
        return None

    def _save_to_backup_file(self, cid: str, metadata: Dict[str, Any]) -> None:
        """Save CID to backup JSON file with history"""
        try:
            history = []
            if os.path.exists(self.backup_cid_file):
                try:
                    with open(self.backup_cid_file, "r") as f:
                        data = json.load(f)
                        history = data.get("history", [])
                except:
                    pass

            # Add new entry
            history.append(
                {
                    "cid": cid,
                    "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                    "blocks_count": metadata.get("blocks_count", 0),
                }
            )

            # Keep only last 10 entries
            history = history[-10:]

            backup_data = {
                "latest_cid": cid,
                "last_updated": datetime.now().isoformat(),
                "history": history,
            }

            with open(self.backup_cid_file, "w") as f:
                json.dump(backup_data, f, indent=2)
        except Exception as e:
            print(f"Error saving backup file: {e}")

    def _get_from_backup_file(self) -> Optional[str]:
        """Get CID from backup JSON file"""
        try:
            if os.path.exists(self.backup_cid_file):
                with open(self.backup_cid_file, "r") as f:
                    data = json.load(f)
                    return data.get("latest_cid")
        except Exception as e:
            print(f"Error reading backup file: {e}")
        return None

    def get_cid_history(self) -> list:
        """Get history of CIDs from backup file"""
        try:
            if os.path.exists(self.backup_cid_file):
                with open(self.backup_cid_file, "r") as f:
                    data = json.load(f)
                    return data.get("history", [])
        except:
            pass
        return []


# Singleton instance
cid_manager = CIDManager()
