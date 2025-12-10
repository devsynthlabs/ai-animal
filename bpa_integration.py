"""
BPA (Bharat Pashudhan App) Integration Module.
Handles API communication with the BPA system.
"""

import requests
import json
import logging
from typing import Optional
from config import Config
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BPAIntegration:
    """Handles integration with Bharat Pashudhan App API."""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """Initialize BPA integration.
        
        Args:
            api_url: BPA API endpoint URL.
            api_key: BPA API authentication key.
        """
        self.api_url = api_url or Config.BPA_API_URL
        self.api_key = api_key or Config.BPA_API_KEY
        self.is_configured = bool(self.api_url and self.api_key)
    
    def submit_classification(self, data: dict) -> dict:
        """Submit ATC classification data to BPA.
        
        Args:
            data: BPA-formatted classification data.
            
        Returns:
            Response dictionary with status and message.
        """
        if not self.is_configured:
            return {
                "success": False,
                "message": "BPA integration not configured. Please set BPA_API_URL and BPA_API_KEY.",
                "data": None
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Data successfully submitted to BPA",
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "message": f"BPA API returned status {response.status_code}",
                    "data": response.text
                }
                
        except requests.exceptions.Timeout:
            logger.error("BPA API request timed out")
            return {
                "success": False,
                "message": "Request to BPA timed out",
                "data": None
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"BPA API request failed: {e}")
            return {
                "success": False,
                "message": f"Failed to connect to BPA: {str(e)}",
                "data": None
            }
    
    def check_connection(self) -> dict:
        """Check if BPA API is reachable.
        
        Returns:
            Dictionary with connection status.
        """
        if not self.is_configured:
            return {
                "connected": False,
                "message": "BPA integration not configured"
            }
        
        try:
            # Try a simple health check (if available)
            response = requests.get(
                self.api_url.replace('/atc', '/health'),
                timeout=10
            )
            return {
                "connected": response.status_code == 200,
                "message": "Connected to BPA" if response.status_code == 200 else "BPA unreachable"
            }
        except:
            return {
                "connected": False,
                "message": "Could not connect to BPA"
            }
    
    def format_submission(self, report: dict, animal_id: str = None, 
                         farmer_id: str = None, location: dict = None) -> dict:
        """Format report for BPA submission with additional metadata.
        
        Args:
            report: ATC report to submit.
            animal_id: Optional unique animal identifier.
            farmer_id: Optional farmer/owner identifier.
            location: Optional location dictionary with lat/lng.
            
        Returns:
            Formatted submission data.
        """
        submission = {
            "submission_timestamp": datetime.now().isoformat(),
            "source": "AI-ATC-System",
            "version": "1.0.0",
            "animal_id": animal_id,
            "farmer_id": farmer_id,
            "location": location,
            "classification_data": report
        }
        
        return submission


# Singleton instance for easy import
bpa_client = BPAIntegration()
