"""
Fingerprint profile management module to store and retrieve consistent fingerprints.
This module allows for creating, storing, and reusing browser fingerprints
to maintain consistency across sessions.
"""
import os
import json
import random
import string
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger
from app.utils.fingerprint_injection import FingerprintGenerator

# Default directory for storing fingerprint profiles
DEFAULT_PROFILES_DIR = Path(__file__).parent.parent / "data" / "fingerprint_profiles"

class FingerprintProfileManager:
    """
    Manages fingerprint profiles for consistent browser fingerprinting
    
    This class handles the creation, storage, and retrieval of browser
    fingerprint profiles to ensure consistent fingerprints across sessions.
    """
    
    def __init__(self, profiles_dir: Optional[str] = None):
        """
        Initialize the profile manager
        
        Args:
            profiles_dir: Directory to store fingerprint profiles
        """
        self.profiles_dir = Path(profiles_dir) if profiles_dir else DEFAULT_PROFILES_DIR
        self._ensure_profile_dir_exists()
        self.generator = FingerprintGenerator()
    
    def _ensure_profile_dir_exists(self):
        """Ensure the profiles directory exists"""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_profile_id(self, length: int = 8) -> str:
        """
        Generate a unique profile ID
        
        Args:
            length: Length of the ID
            
        Returns:
            str: Unique profile ID
        """
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def create_profile(self, 
                      name: Optional[str] = None,
                      browser_type: Optional[str] = None,
                      os_type: Optional[str] = None,
                      device_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new fingerprint profile
        
        Args:
            name: Optional name for the profile
            browser_type: Type of browser to emulate
            os_type: Type of OS to emulate
            device_type: Type of device to emulate
            
        Returns:
            Dict: The created fingerprint profile
        """
        # Generate fingerprint
        fingerprint = self.generator.generate_fingerprint(
            browser_type=browser_type,
            os_type=os_type,
            device_type=device_type
        )
        
        # Create profile metadata
        profile_id = self._generate_profile_id()
        profile_name = name or f"{fingerprint['browser']['type']}_{fingerprint['os']['type']}_{profile_id}"
        
        # Create full profile with metadata
        profile = {
            "id": profile_id,
            "name": profile_name,
            "created_at": None,  # Will be set when saved
            "last_used": None,   # Will be set when used
            "fingerprint": fingerprint
        }
        
        # Save the profile
        self.save_profile(profile)
        
        return profile
    
    def save_profile(self, profile: Dict[str, Any]) -> bool:
        """
        Save a fingerprint profile to disk
        
        Args:
            profile: The profile to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update timestamps
            from datetime import datetime
            now = datetime.now().isoformat()
            
            if not profile.get("created_at"):
                profile["created_at"] = now
            
            # Get profile ID
            profile_id = profile.get("id")
            if not profile_id:
                profile_id = self._generate_profile_id()
                profile["id"] = profile_id
            
            # Save to file
            profile_path = self.profiles_dir / f"{profile_id}.json"
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
            
            logger.debug(f"Saved fingerprint profile: {profile_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save fingerprint profile: {e}")
            return False
    
    def load_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a fingerprint profile from disk
        
        Args:
            profile_id: ID of the profile to load
            
        Returns:
            Dict: The loaded profile or None if not found
        """
        try:
            profile_path = self.profiles_dir / f"{profile_id}.json"
            
            if not profile_path.exists():
                logger.warning(f"Profile not found: {profile_id}")
                return None
            
            with open(profile_path, 'r') as f:
                profile = json.load(f)
            
            # Update last used timestamp
            from datetime import datetime
            profile["last_used"] = datetime.now().isoformat()
            
            # Save the updated profile
            self.save_profile(profile)
            
            logger.debug(f"Loaded fingerprint profile: {profile_id}")
            return profile
        
        except Exception as e:
            logger.error(f"Failed to load fingerprint profile: {e}")
            return None
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all available fingerprint profiles
        
        Returns:
            List: List of profile metadata
        """
        profiles = []
        
        try:
            for profile_file in self.profiles_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r') as f:
                        profile = json.load(f)
                    
                    # Add basic metadata to the list
                    profiles.append({
                        "id": profile.get("id"),
                        "name": profile.get("name"),
                        "created_at": profile.get("created_at"),
                        "last_used": profile.get("last_used"),
                        "browser_type": profile.get("fingerprint", {}).get("browser", {}).get("type"),
                        "os_type": profile.get("fingerprint", {}).get("os", {}).get("type")
                    })
                except Exception as e:
                    logger.warning(f"Failed to read profile {profile_file.name}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
        
        return profiles
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a fingerprint profile
        
        Args:
            profile_id: ID of the profile to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            profile_path = self.profiles_dir / f"{profile_id}.json"
            
            if not profile_path.exists():
                logger.warning(f"Profile not found for deletion: {profile_id}")
                return False
            
            # Delete the file
            profile_path.unlink()
            logger.debug(f"Deleted fingerprint profile: {profile_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete profile {profile_id}: {e}")
            return False
    
    def get_random_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get a random fingerprint profile from available profiles
        
        Returns:
            Dict: A random profile or None if no profiles exist
        """
        profiles = self.list_profiles()
        
        if not profiles:
            logger.warning("No profiles available, creating one")
            return self.create_profile()
        
        # Select random profile
        random_profile_meta = random.choice(profiles)
        profile_id = random_profile_meta.get("id")
        
        if not profile_id:
            logger.warning("Invalid profile metadata")
            return None
        
        # Load the full profile
        return self.load_profile(profile_id)

# Global instance for easy access
profile_manager = FingerprintProfileManager()

def get_profile_manager() -> FingerprintProfileManager:
    """
    Get the global profile manager instance
    
    Returns:
        FingerprintProfileManager: The global profile manager
    """
    return profile_manager

def get_or_create_profile(profile_id: Optional[str] = None, 
                        browser_type: Optional[str] = None,
                        os_type: Optional[str] = None,
                        device_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a profile by ID or create a new one if not found
    
    Args:
        profile_id: ID of the profile to load
        browser_type: Browser type if creating new profile
        os_type: OS type if creating new profile
        device_type: Device type if creating new profile
        
    Returns:
        Dict: The loaded or created profile
    """
    manager = get_profile_manager()
    
    if profile_id:
        # Try to load existing profile
        profile = manager.load_profile(profile_id)
        if profile:
            return profile
    
    # Create new profile
    return manager.create_profile(
        browser_type=browser_type,
        os_type=os_type,
        device_type=device_type
    )

def save_current_fingerprint(fingerprint: Dict[str, Any], name: Optional[str] = None) -> str:
    """
    Save the current fingerprint as a profile
    
    Args:
        fingerprint: The fingerprint to save
        name: Optional name for the profile
        
    Returns:
        str: ID of the saved profile
    """
    manager = get_profile_manager()
    
    # Create profile with metadata
    profile_id = manager._generate_profile_id()
    profile_name = name or f"{fingerprint['browser']['type']}_{fingerprint['os']['type']}_{profile_id}"
    
    profile = {
        "id": profile_id,
        "name": profile_name,
        "fingerprint": fingerprint
    }
    
    # Save profile
    manager.save_profile(profile)
    
    return profile_id 