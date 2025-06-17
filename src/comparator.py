# src/comparator.py
import re
from typing import Dict, Any, List, Tuple

class PolicyComparator:
    """
    Enhanced comparator that finds mismatches between extracted policy facts
    and user claims with detailed analysis and confidence scoring.
    """
    
    def __init__(self):
        self.mismatch_explanations = {
            "collects_emails": {
                "description": "Email Collection",
                "policy_true_user_false": "Your policy mentions collecting emails, but you claim you don't.",
                "policy_false_user_true": "You claim to collect emails, but your policy doesn't mention this.",
            },
            "uses_tracking": {
                "description": "Analytics/Tracking Usage", 
                "policy_true_user_false": "Your policy mentions using tracking/analytics, but you claim you don't.",
                "policy_false_user_true": "You claim to use tracking/analytics, but your policy doesn't mention this.",
            },
            "shares_data": {
                "description": "Third-Party Data Sharing",
                "policy_true_user_false": "Your policy mentions sharing data with third parties, but you claim you don't.",
                "policy_false_user_true": "You claim to share data with third parties, but your policy doesn't mention this.",
            },
            "retains_data_duration": {
                "description": "Data Retention Period",
                "different_periods": "There's a mismatch in data retention periods between your policy and claims.",
            }
        }
    
    def find_mismatches(self, extracted_facts: Dict[str, Any], user_claims: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Compare extracted facts with user claims and identify mismatches.
        
        Args:
            extracted_facts: Facts extracted from the privacy policy
            user_claims: Claims made by the user about their practices
            
        Returns:
            Dictionary of mismatches with detailed explanations
        """
        mismatches = {}
        
        # Check each field for mismatches
        for key in user_claims.keys():
            if key in extracted_facts:
                mismatch_info = self._compare_field(
                    key, 
                    extracted_facts[key], 
                    user_claims[key]
                )
                
                if mismatch_info:
                    mismatches[key] = mismatch_info
        
        return mismatches
    
    def _compare_field(self, field_name: str, policy_value: Any, user_value: Any) -> Dict[str, Any]:
        """
        Compare a specific field between policy and user claims.
        
        Returns:
            Dictionary with mismatch details if found, None if no mismatch
        """
        
        # Handle data retention duration specially (more complex comparison)
        if field_name == "retains_data_duration":
            return self._compare_retention_duration(policy_value, user_value)
        
        # Handle boolean fields (emails, tracking, sharing)
        elif isinstance(user_value, bool):
            return self._compare_boolean_field(field_name, policy_value, user_value)
        
        # Handle other field types
        else:
            if policy_value != user_value:
                return {
                    "policy_value": policy_value,
                    "user_value": user_value,
                    "severity": "medium",
                    "explanation": f"Mismatch detected in {field_name.replace('_', ' ')}"
                }
        
        return None
    
    def _compare_boolean_field(self, field_name: str, policy_value: Any, user_value: bool) -> Dict[str, Any]:
        """Compare boolean fields like email collection, tracking usage, etc."""
        
        # Convert policy value to boolean if needed
        policy_bool = self._convert_to_boolean(policy_value)
        
        if policy_bool != user_value:
            explanation_key = f"policy_{str(policy_bool).lower()}_user_{str(user_value).lower()}"
            
            explanation = self.mismatch_explanations.get(field_name, {}).get(
                explanation_key, 
                f"Mismatch in {field_name.replace('_', ' ')}"
            )
            
            severity = self._calculate_severity(field_name, policy_bool, user_value)
            
            return {
                "policy_value": policy_value,
                "user_value": user_value,
                "policy_boolean": policy_bool,
                "user_boolean": user_value,
                "severity": severity,
                "explanation": explanation,
                "field_description": self.mismatch_explanations.get(field_name, {}).get("description", field_name)
            }
        
        return None
    
    def _compare_retention_duration(self, policy_value: str, user_value: str) -> Dict[str, Any]:
        """Special handling for data retention duration comparison."""
        
        # Normalize both values
        policy_months = self._parse_duration_to_months(policy_value)
        user_months = self._parse_duration_to_months(user_value)
        
        # Skip comparison if either value is unknown/unclear
        if policy_months == -1 or user_months == -1:
            if policy_value.lower() != user_value.lower():
                return {
                    "policy_value": policy_value,
                    "user_value": user_value,
                    "severity": "low",
                    "explanation": "Unable to accurately compare retention periods - one or both values are unclear",
                    "field_description": "Data Retention Period"
                }
            return None
        
        # Compare normalized values
        if abs(policy_months - user_months) > 1:  # Allow 1 month tolerance
            severity = "high" if abs(policy_months - user_months) > 6 else "medium"
            
            return {
                "policy_value": policy_value,
                "user_value": user_value,
                "policy_months": policy_months,
                "user_months": user_months,
                "difference_months": abs(policy_months - user_months),
                "severity": severity,
                "explanation": f"Significant difference in retention periods: policy says {policy_value}, you claim {user_value}",
                "field_description": "Data Retention Period"
            }
        
        return None
    
    def _convert_to_boolean(self, value: Any) -> bool:
        """Convert various value types to boolean."""
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() not in ['false', 'no', 'none', '', 'unknown']
        else:
            return bool(value)
    
    def _parse_duration_to_months(self, duration_str: str) -> int:
        """
        Parse duration string to months for comparison.
        Returns -1 if unable to parse.
        """
        if not isinstance(duration_str, str):
            return -1
        
        duration_lower = duration_str.lower().strip()
        
        # Handle common cases
        duration_mapping = {
            "not specified": -1,
            "not sure": -1,
            "unknown": -1,
            "indefinitely": 9999,
            "permanently": 9999,
            "1 month": 1,
            "3 months": 3,
            "6 months": 6,
            "1 year": 12,
            "2+ years": 24,
            "2 years": 24,
            "3 years": 36
        }
        
        if duration_lower in duration_mapping:
            return duration_mapping[duration_lower]
        
        # Try to extract numbers with regex
        # Match patterns like "12 months", "1 year", "2 years"
        patterns = [
            (r'(\d+)\s*months?', 1),          # "12 months" -> 12
            (r'(\d+)\s*years?', 12),          # "2 years" -> 24
            (r'(\d+)\s*days?', 1/30),         # "30 days" -> 1 month
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, duration_lower)
            if match:
                number = int(match.group(1))
                return int(number * multiplier)
        
        return -1  # Unable to parse
    
    def _calculate_severity(self, field_name: str, policy_value: bool, user_value: bool) -> str:
        """Calculate severity of mismatch based on field type and values."""
        
        # High severity cases
        if field_name == "shares_data":
            # Claiming not to share when policy says you do is serious
            if policy_value and not user_value:
                return "high"
            # Claiming to share when policy says you don't is also serious  
            elif not policy_value and user_value:
                return "high"
        
        elif field_name == "collects_emails":
            # Not mentioning email collection when you do it is serious
            if policy_value and not user_value:
                return "high"
            # Claiming to collect when policy doesn't mention it is medium
            elif not policy_value and user_value:
                return "medium"
        
        elif field_name == "uses_tracking":
            # Not disclosing tracking usage is serious
            if policy_value and not user_value:
                return "high"
            # Claiming tracking when policy doesn't mention it is medium
            elif not policy_value and user_value:
                return "medium"
        
        return "medium"  # Default severity
    
    def generate_summary_report(self, mismatches: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate a summary report of all mismatches."""
        
        if not mismatches:
            return {
                "total_mismatches": 0,
                "severity_breakdown": {"high": 0, "medium": 0, "low": 0},
                "overall_risk": "low",
                "summary": "No mismatches detected. Your claims align well with your privacy policy.",
                "recommendations": []
            }
        
        # Count mismatches by severity
        severity_count = {"high": 0, "medium": 0, "low": 0}
        for mismatch in mismatches.values():
            severity = mismatch.get("severity", "medium")
            severity_count[severity] += 1
        
        # Determine overall risk
        if severity_count["high"] > 0:
            overall_risk = "high"
        elif severity_count["medium"] > 2:
            overall_risk = "high"
        elif severity_count["medium"] > 0:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(mismatches)
        
        # Create summary message
        total = len(mismatches)
        summary = f"Found {total} mismatch{'es' if total > 1 else ''} between your claims and privacy policy."
        
        if severity_count["high"] > 0:
            summary += f" {severity_count['high']} require immediate attention."
        
        return {
            "total_mismatches": total,
            "severity_breakdown": severity_count,
            "overall_risk": overall_risk,
            "summary": summary,
            "recommendations": recommendations
        }
    
    def _generate_recommendations(self, mismatches: Dict[str, Dict]) -> List[str]:
        """Generate specific recommendations based on mismatches found."""
        
        recommendations = []
        
        for field_name, mismatch in mismatches.items():
            severity = mismatch.get("severity", "medium")
            
            if field_name == "collects_emails":
                if severity == "high":
                    recommendations.append("🔴 Update your privacy policy to clearly state email collection practices")
                else:
                    recommendations.append("🟡 Clarify email collection details in your privacy policy")
            
            elif field_name == "uses_tracking":
                if severity == "high":
                    recommendations.append("🔴 Add tracking/analytics disclosure to your privacy policy")
                else:
                    recommendations.append("🟡 Consider adding more details about your analytics usage")
            
            elif field_name == "shares_data":
                if severity == "high":
                    recommendations.append("🔴 Critical: Fix data sharing discrepancy immediately - this is a compliance risk")
                else:
                    recommendations.append("🟡 Clarify third-party data sharing practices")
            
            elif field_name == "retains_data_duration":
                recommendations.append("🟡 Align data retention periods between your policy and actual practices")
        
        # Add general recommendations
        if len(mismatches) > 2:
            recommendations.append("📋 Consider a comprehensive policy review with a legal expert")
        
        recommendations.append("✅ Update your privacy policy to reflect your actual data practices")
        
        return recommendations


# Convenience function to maintain compatibility with original code
def find_mismatches(extracted_facts: Dict[str, Any], user_claims: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Wrapper function to maintain compatibility with existing code.
    """
    comparator = PolicyComparator()
    return comparator.find_mismatches(extracted_facts, user_claims)