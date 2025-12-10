"""
Gemini Vision API Analyzer for Animal Type Classification.
This module handles image analysis using Google's Gemini Vision API.
"""

import google.generativeai as genai
from PIL import Image
import json
import os
from config import Config


class GeminiAnalyzer:
    """Analyzes animal images using Gemini Vision API."""
    
    def __init__(self, api_key: str = None):
        """Initialize the Gemini analyzer.
        
        Args:
            api_key: Gemini API key. If not provided, uses environment variable.
        """
        self.api_key = api_key or Config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY in .env file.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    def analyze_image(self, image_path: str) -> dict:
        """Analyze an animal image and return ATC scores.
        
        Args:
            image_path: Path to the animal image.
            
        Returns:
            Dictionary containing analysis results and ATC scores.
        """
        # Load and validate image
        image = Image.open(image_path)
        
        # Create the analysis prompt
        prompt = self._create_analysis_prompt()
        
        # Send to Gemini for analysis
        response = self.model.generate_content([prompt, image])
        
        # Parse the response
        result = self._parse_response(response.text)
        
        return result
    
    def _create_analysis_prompt(self) -> str:
        """Create the analysis prompt for Gemini."""
        return """You are an expert animal type classifier (ATC) for cattle and buffalo evaluation. 
Analyze this image and provide a detailed assessment.

IMPORTANT: Respond ONLY with a valid JSON object, no other text.

Analyze the animal in the image and provide scores on a 1-9 scale for each trait.
Score 5 is average/intermediate, 1 is one extreme, 9 is the other extreme.

Return this exact JSON structure:
{
    "animal_detected": true/false,
    "animal_type": "cattle" or "buffalo" or "unknown",
    "breed_guess": "best guess of breed",
    "sex": "male" or "female" or "unknown",
    "image_quality": "good" or "fair" or "poor",
    "image_angle": "side" or "rear" or "front" or "three-quarter",
    "body_parts_visible": {
        "head": true/false,
        "withers": true/false,
        "chest": true/false,
        "barrel": true/false,
        "rump": true/false,
        "legs": true/false,
        "udder": true/false,
        "tail": true/false
    },
    "structural_scores": {
        "stature": {"score": 1-9, "notes": "assessment notes"},
        "chest_width": {"score": 1-9, "notes": "assessment notes"},
        "body_depth": {"score": 1-9, "notes": "assessment notes"},
        "rump_angle": {"score": 1-9, "notes": "assessment notes"},
        "rump_width": {"score": 1-9, "notes": "assessment notes"},
        "rear_legs": {"score": 1-9, "notes": "assessment notes"},
        "foot_angle": {"score": 1-9, "notes": "assessment notes"},
        "body_condition": {"score": 1-9, "notes": "assessment notes"}
    },
    "udder_scores": {
        "fore_udder": {"score": 1-9 or null, "notes": "assessment notes or 'not visible'"},
        "rear_udder_height": {"score": 1-9 or null, "notes": "assessment notes or 'not visible'"},
        "udder_depth": {"score": 1-9 or null, "notes": "assessment notes or 'not visible'"},
        "teat_placement": {"score": 1-9 or null, "notes": "assessment notes or 'not visible'"},
        "teat_length": {"score": 1-9 or null, "notes": "assessment notes or 'not visible'"}
    },
    "overall_score": 1-9,
    "overall_assessment": "Brief overall assessment of the animal's conformation",
    "recommendations": ["list of recommendations for improvement or breeding considerations"]
}

If no animal is detected, set animal_detected to false and provide empty/null values for other fields.
If a trait cannot be assessed from the image angle, set its score to null with appropriate notes.
"""

    def _parse_response(self, response_text: str) -> dict:
        """Parse the Gemini response into a structured result.
        
        Args:
            response_text: Raw text response from Gemini.
            
        Returns:
            Parsed dictionary with analysis results.
        """
        try:
            # Clean up the response (remove markdown code blocks if present)
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            
            # Validate and ensure all required fields exist
            result = self._validate_result(result)
            
            return result
            
        except json.JSONDecodeError as e:
            # Return error response if parsing fails
            return {
                "error": True,
                "message": f"Failed to parse AI response: {str(e)}",
                "raw_response": response_text
            }
    
    def _validate_result(self, result: dict) -> dict:
        """Validate and clean up the result dictionary.
        
        Args:
            result: Raw parsed result.
            
        Returns:
            Validated result dictionary.
        """
        # Ensure required fields exist
        defaults = {
            "animal_detected": False,
            "animal_type": "unknown",
            "breed_guess": "unknown",
            "sex": "unknown",
            "image_quality": "fair",
            "image_angle": "unknown",
            "body_parts_visible": {},
            "structural_scores": {},
            "udder_scores": {},
            "overall_score": 5,
            "overall_assessment": "",
            "recommendations": []
        }
        
        for key, default in defaults.items():
            if key not in result:
                result[key] = default
        
        # Calculate composite scores
        result["composite_scores"] = self._calculate_composite_scores(result)
        
        return result
    
    def _calculate_composite_scores(self, result: dict) -> dict:
        """Calculate composite scores from individual trait scores.
        
        Args:
            result: Analysis result dictionary.
            
        Returns:
            Dictionary of composite scores.
        """
        structural = result.get("structural_scores", {})
        udder = result.get("udder_scores", {})
        
        # Calculate structural composite
        structural_scores = []
        for trait, data in structural.items():
            if isinstance(data, dict) and data.get("score") is not None:
                structural_scores.append(data["score"])
        
        structural_avg = sum(structural_scores) / len(structural_scores) if structural_scores else 5
        
        # Calculate udder composite
        udder_scores = []
        for trait, data in udder.items():
            if isinstance(data, dict) and data.get("score") is not None:
                udder_scores.append(data["score"])
        
        udder_avg = sum(udder_scores) / len(udder_scores) if udder_scores else None
        
        # Calculate final composite
        if udder_avg is not None:
            final = (structural_avg * 0.6) + (udder_avg * 0.4)
        else:
            final = structural_avg
        
        return {
            "structural_composite": round(structural_avg, 2),
            "udder_composite": round(udder_avg, 2) if udder_avg else None,
            "final_composite": round(final, 2)
        }
