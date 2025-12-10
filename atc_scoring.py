"""
ATC (Animal Type Classification) Scoring Module.
Handles scoring logic and validation for cattle and buffalo evaluations.
"""

from config import Config
from typing import Dict, List, Optional
from datetime import datetime
import json


class ATCScorer:
    """Handles ATC scoring calculations and validations."""
    
    def __init__(self):
        """Initialize the ATC scorer with trait definitions."""
        self.traits = Config.ATC_TRAITS
        self.score_min = Config.SCORE_MIN
        self.score_max = Config.SCORE_MAX
    
    def validate_score(self, score: int) -> bool:
        """Validate that a score is within the valid range.
        
        Args:
            score: Score value to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        if score is None:
            return True  # Null scores are valid (trait not visible)
        return self.score_min <= score <= self.score_max
    
    def get_score_description(self, trait_id: str, score: int) -> str:
        """Get a description for a score on a specific trait.
        
        Args:
            trait_id: ID of the trait.
            score: Score value (1-9).
            
        Returns:
            Description of what the score means.
        """
        descriptions = {
            'stature': {
                1: 'Very short/small',
                5: 'Average height',
                9: 'Very tall/large'
            },
            'chest_width': {
                1: 'Very narrow chest',
                5: 'Average chest width',
                9: 'Very wide chest'
            },
            'body_depth': {
                1: 'Very shallow body',
                5: 'Average body depth',
                9: 'Very deep body'
            },
            'rump_angle': {
                1: 'Pins very high (level)',
                5: 'Moderate slope',
                9: 'Pins very low (steep)'
            },
            'rump_width': {
                1: 'Very narrow rump',
                5: 'Average rump width',
                9: 'Very wide rump'
            },
            'rear_legs': {
                1: 'Very straight (post-legged)',
                5: 'Intermediate set',
                9: 'Very sickled'
            },
            'foot_angle': {
                1: 'Very low angle (flat)',
                5: 'Intermediate angle',
                9: 'Very steep angle'
            },
            'body_condition': {
                1: 'Very thin/emaciated',
                5: 'Average condition',
                9: 'Very fat/over-conditioned'
            },
            'fore_udder': {
                1: 'Weak/loose attachment',
                5: 'Moderate attachment',
                9: 'Very strong attachment'
            },
            'rear_udder_height': {
                1: 'Very low attachment',
                5: 'Intermediate height',
                9: 'Very high attachment'
            },
            'udder_depth': {
                1: 'Well below hocks',
                5: 'At hock level',
                9: 'Well above hocks'
            },
            'teat_placement': {
                1: 'Very wide (outside)',
                5: 'Central placement',
                9: 'Very close (inside)'
            },
            'teat_length': {
                1: 'Very short teats',
                5: 'Medium length',
                9: 'Very long teats'
            }
        }
        
        if trait_id not in descriptions:
            return f"Score: {score}"
        
        trait_desc = descriptions[trait_id]
        
        if score in trait_desc:
            return trait_desc[score]
        elif score < 5:
            return f"Below average ({trait_desc[1]} to {trait_desc[5]})"
        else:
            return f"Above average ({trait_desc[5]} to {trait_desc[9]})"
    
    def calculate_overall_grade(self, composite_score: float) -> str:
        """Calculate an overall grade based on composite score.
        
        Args:
            composite_score: Final composite score (1-9 scale).
            
        Returns:
            Grade string (Excellent, Very Good, Good, Average, Fair, Poor).
        """
        if composite_score >= 8:
            return "Excellent"
        elif composite_score >= 7:
            return "Very Good"
        elif composite_score >= 6:
            return "Good Plus"
        elif composite_score >= 5:
            return "Good"
        elif composite_score >= 4:
            return "Average"
        elif composite_score >= 3:
            return "Fair"
        else:
            return "Poor"
    
    def format_report(self, analysis_result: dict) -> dict:
        """Format analysis results into a comprehensive report.
        
        Args:
            analysis_result: Raw analysis result from Gemini analyzer.
            
        Returns:
            Formatted report dictionary.
        """
        report = {
            "report_id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "generated_at": datetime.now().isoformat(),
            "animal_info": {
                "type": analysis_result.get("animal_type", "unknown"),
                "breed": analysis_result.get("breed_guess", "unknown"),
                "sex": analysis_result.get("sex", "unknown")
            },
            "image_assessment": {
                "quality": analysis_result.get("image_quality", "fair"),
                "angle": analysis_result.get("image_angle", "unknown"),
                "body_parts_visible": analysis_result.get("body_parts_visible", {})
            },
            "scores": {
                "structural": self._format_scores(
                    analysis_result.get("structural_scores", {}),
                    "structural"
                ),
                "udder": self._format_scores(
                    analysis_result.get("udder_scores", {}),
                    "udder"
                )
            },
            "composites": analysis_result.get("composite_scores", {}),
            "overall_grade": self.calculate_overall_grade(
                analysis_result.get("composite_scores", {}).get("final_composite", 5)
            ),
            "assessment": analysis_result.get("overall_assessment", ""),
            "recommendations": analysis_result.get("recommendations", [])
        }
        
        return report
    
    def _format_scores(self, scores: dict, category: str) -> List[dict]:
        """Format individual scores with descriptions.
        
        Args:
            scores: Dictionary of trait scores.
            category: Category name (structural or udder).
            
        Returns:
            List of formatted score dictionaries.
        """
        formatted = []
        
        # Get trait definitions for this category
        trait_defs = {t['id']: t for t in self.traits.get(category, [])}
        
        for trait_id, data in scores.items():
            if isinstance(data, dict):
                score = data.get("score")
                notes = data.get("notes", "")
            else:
                score = data
                notes = ""
            
            trait_def = trait_defs.get(trait_id, {"name": trait_id, "description": ""})
            
            formatted.append({
                "trait_id": trait_id,
                "trait_name": trait_def.get("name", trait_id),
                "description": trait_def.get("description", ""),
                "score": score,
                "score_description": self.get_score_description(trait_id, score) if score else "Not assessed",
                "notes": notes
            })
        
        return formatted
    
    def export_for_bpa(self, report: dict) -> dict:
        """Export report in BPA-compatible format.
        
        Args:
            report: Formatted report dictionary.
            
        Returns:
            BPA-compatible data dictionary.
        """
        # Flatten scores for BPA format
        structural_scores = {}
        for score_data in report.get("scores", {}).get("structural", []):
            structural_scores[score_data["trait_id"]] = score_data["score"]
        
        udder_scores = {}
        for score_data in report.get("scores", {}).get("udder", []):
            udder_scores[score_data["trait_id"]] = score_data["score"]
        
        return {
            "report_id": report.get("report_id"),
            "timestamp": report.get("generated_at"),
            "animal_type": report.get("animal_info", {}).get("type"),
            "breed": report.get("animal_info", {}).get("breed"),
            "sex": report.get("animal_info", {}).get("sex"),
            "structural_scores": structural_scores,
            "udder_scores": udder_scores,
            "structural_composite": report.get("composites", {}).get("structural_composite"),
            "udder_composite": report.get("composites", {}).get("udder_composite"),
            "final_composite": report.get("composites", {}).get("final_composite"),
            "overall_grade": report.get("overall_grade"),
            "assessment": report.get("assessment"),
            "recommendations": report.get("recommendations")
        }
