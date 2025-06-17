# src/comparator.py
import re
from typing import Dict, Any, List, Tuple

class PolicyComparator:
    """
    Comparator that analyzes privacy policies from a user's perspective,
    highlighting important rights and potential concerns.
    """
    
    def __init__(self):
        self.mismatch_explanations = {
            "collects_emails": {
                "description": "Email Collection",
                "policy_true_user_false": "The policy mentions collecting emails, but you indicated it doesn't.",
                "policy_false_user_true": "You indicated email collection, but the policy doesn't mention this.",
            },
            "uses_tracking": {
                "description": "Analytics/Tracking Usage", 
                "policy_true_user_false": "The policy mentions using tracking/analytics, but you indicated it doesn't.",
                "policy_false_user_true": "You indicated tracking usage, but the policy doesn't mention this.",
            },
            "shares_data": {
                "description": "Third-Party Data Sharing",
                "policy_true_user_false": "The policy mentions sharing data with third parties, but you indicated it doesn't.",
                "policy_false_user_true": "You indicated data sharing, but the policy doesn't mention this.",
            },
            "right_to_delete": {
                "description": "Right to Delete Data",
                "policy_true_user_false": "The policy mentions data deletion rights, but you indicated it doesn't.",
                "policy_false_user_true": "You indicated deletion rights, but the policy doesn't mention this.",
            },
            "right_to_access": {
                "description": "Right to Access Data",
                "policy_true_user_false": "The policy mentions data access rights, but you indicated it doesn't.",
                "policy_false_user_true": "You indicated access rights, but the policy doesn't mention this.",
            },
            "data_portability": {
                "description": "Data Portability",
                "policy_true_user_false": "The policy mentions data portability, but you indicated it doesn't.",
                "policy_false_user_true": "You indicated data portability, but the policy doesn't mention this.",
            }
        }
    
    def find_mismatches(self, extracted_facts: Dict[str, Any], user_claims: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Compare extracted facts with user claims and identify mismatches.
        Focuses on user rights and data handling practices.
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
        """Compare a specific field between policy and user claims."""
        
        # Handle data retention duration specially
        if field_name == "retains_data_duration":
            return self._compare_retention_duration(policy_value, user_value)
        
        # Handle boolean fields
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
        """Calculate severity based on user impact."""
        # High severity for user rights
        if field_name in ['right_to_delete', 'right_to_access', 'data_portability']:
            return 'high'
        
        # Medium severity for data collection and sharing
        if field_name in ['collects_emails', 'uses_tracking', 'shares_data']:
            return 'medium'
        
        # Low severity for other fields
        return 'low'
    
    def generate_summary_report(self, mismatches: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate a user-focused summary report."""
        report = {
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        for key, mismatch in mismatches.items():
            if mismatch['severity'] == 'high':
                report['critical_issues'].append({
                    "issue": mismatch['field_description'],
                    "explanation": mismatch['explanation']
                })
            elif mismatch['severity'] == 'medium':
                report['warnings'].append({
                    "issue": mismatch['field_description'],
                    "explanation": mismatch['explanation']
                })
        
        report['recommendations'] = self._generate_recommendations(mismatches)
        
        return report
    
    def _generate_recommendations(self, mismatches: Dict[str, Dict]) -> List[str]:
        """Generate user-focused recommendations."""
        recommendations = []
        
        for key, mismatch in mismatches.items():
            if key == 'right_to_delete' and not mismatch['policy_boolean']:
                recommendations.append("Consider requesting clarification about your right to delete your data")
            
            elif key == 'right_to_access' and not mismatch['policy_boolean']:
                recommendations.append("Ask about how you can access your personal data")
            
            elif key == 'data_portability' and not mismatch['policy_boolean']:
                recommendations.append("Inquire about options to export your data if needed")
            
            elif key == 'shares_data' and mismatch['policy_boolean']:
                recommendations.append("Review which third parties receive your data and for what purposes")
            
            elif key == 'uses_tracking' and mismatch['policy_boolean']:
                recommendations.append("Consider using privacy tools to limit tracking")
        
        return recommendations


# Convenience function to maintain compatibility with original code
def find_mismatches(extracted_facts: Dict[str, Any], user_claims: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Wrapper function to maintain compatibility with existing code.
    """
    comparator = PolicyComparator()
    return comparator.find_mismatches(extracted_facts, user_claims)