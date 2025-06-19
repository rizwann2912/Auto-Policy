import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class PolicyExtractor:
    """
    Extracts key information from privacy policies focusing on user-relevant details.
    Uses Hugging Face API for NLP tasks.
    """
    
    def __init__(self):
        print("\n=== Initializing Policy Extractor ===")
        self.api_url = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}

    def _query_api(self, model, payload):
        """Generic method to query Hugging Face API"""
        try:
            response = requests.post(
                f"{self.api_url}/{model}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error: {str(e)}")
            return None

    def extract_facts(self, text):
        """
        Main method to extract user-relevant facts from privacy policy text.
        """
        print("\n=== Starting Fact Extraction ===")
        print(f"Input text length: {len(text)} characters")
        
        # Basic keyword extraction
        print("\n--- Starting Keyword Extraction ---")
        basic_facts = self.keyword_extraction(text)
        print("✅ Completed keyword extraction")

        # NLP extraction using API
        print("\n--- Starting NLP Extraction (API) ---")
        try:
            nlp_facts = self.nlp_extraction(text)
            basic_facts.update(nlp_facts)
            print("✅ Completed NLP extraction")
        except Exception as e:
            print(f'❌ NLP extraction failed: {str(e)}')

        # Extract user rights
        print("\n--- Starting User Rights Extraction ---")
        try:
            rights_facts = self.extract_user_rights(text)
            basic_facts.update(rights_facts)
            print("✅ Completed user rights extraction")
        except Exception as e:
            print(f'❌ User rights extraction failed: {str(e)}')

        # Extract retention duration (prioritize QA, fallback to keyword)
        print("\n--- Starting Retention Extraction ---")
        initial_retention = basic_facts.get('retention_duration', 'unknown') # Get keyword-based retention
        try:
            qa_retention = self.qa_retention_extraction(text)
            # Use QA result if it's not 'Not found' or 'Error'
            if qa_retention not in ["Not found (QA API)", "Error (QA API)"]:
                basic_facts['retention_duration'] = qa_retention
                print("✅ Completed retention extraction (QA model used)")
            else:
                basic_facts['retention_duration'] = initial_retention # Fallback to keyword
                print("✅ Completed retention extraction (Keyword fallback used)")
        except Exception as e:
            print(f'❌ Retention extraction failed: {str(e)} - falling back to keyword')
            basic_facts['retention_duration'] = initial_retention # Ensure fallback on error

        return basic_facts
    
    def keyword_extraction(self, text):
        """Extracts facts using keyword matching and regex patterns."""
        text_lower = text.lower()
        facts = {}

        # Data Collection
        email_keywords = ['email', 'e-mail', 'email address', 'contact information']
        facts['collects_emails'] = any(keyword in text_lower for keyword in email_keywords)

        tracking_keywords = ['analytics', 'tracking', 'cookies', 'google analytics', 'facebook pixel']
        facts['uses_tracking'] = any(keyword in text_lower for keyword in tracking_keywords)

        # Data Retention
        retention_patterns = [
            r'(\d+)\s*(year|month|day)s?',
            r'(indefinitely|permanently)',
            r'until.*?(delete|remove)',
            r'as long as (necessary|needed)',
            r'as required by law',
            r'for the duration of your (account|relationship)'
        ]
        
        retention_duration = 'unknown'
        for pattern in retention_patterns:
            match = re.search(pattern, text_lower)
            if match:
                retention_duration = match.group(0)
                break
        facts['retention_duration'] = retention_duration

        # Data Sharing
        sharing_keywords = ['third party', 'third-party', 'share', 'sharing', 'partners']
        no_sharing_keywords = ['do not share', 'not share', 'no sharing']

        facts['shares_data'] = any(keyword in text_lower for keyword in sharing_keywords)
        if any(keyword in text_lower for keyword in no_sharing_keywords):
            facts['shares_data'] = False

        # Age Restrictions
        age_patterns = [
            r'(\d+)\s*years?\s*old',
            r'age\s*of\s*(\d+)',
            r'minimum\s*age\s*(\d+)'
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                facts['minimum_age'] = match.group(1)
                break

        # Location Data
        location_keywords = ['location', 'gps', 'geolocation', 'ip address', 'country']
        facts['collects_location'] = any(keyword in text_lower for keyword in location_keywords)

        return facts
    
    def extract_user_rights(self, text):
        """Extracts information about user rights from the policy."""
        text_lower = text.lower()
        rights = {}

        # Right to Delete
        delete_keywords = ['right to delete', 'right to erasure', 'delete your data', 'remove your data']
        rights['right_to_delete'] = any(keyword in text_lower for keyword in delete_keywords)

        # Right to Access
        access_keywords = ['right to access', 'access your data', 'view your data', 'download your data']
        rights['right_to_access'] = any(keyword in text_lower for keyword in access_keywords)

        # Data Portability
        portability_keywords = ['data portability', 'export your data', 'transfer your data']
        rights['data_portability'] = any(keyword in text_lower for keyword in portability_keywords)

        # Opt-out Rights
        optout_keywords = ['opt out', 'opt-out', 'unsubscribe', 'withdraw consent']
        rights['opt_out_rights'] = any(keyword in text_lower for keyword in optout_keywords)

        # Data Correction
        correction_keywords = ['correct your data', 'update your data', 'modify your data']
        rights['right_to_correction'] = any(keyword in text_lower for keyword in correction_keywords)

        return rights

    def nlp_extraction(self, text):
        """Uses Hugging Face API for zero-shot classification to extract facts."""
        categories = {
            'collects_emails': ["collects email addresses", "does not collect emails"],
            'uses_tracking': ["uses tracking tools", "no tracking or analytics"],
            'shares_data': ["shares data with third parties", "does not share user data"],
            'right_to_delete': ["users can delete their data", "users cannot delete their data"],
            'right_to_access': ["users can access their data", "users cannot access their data"],
            'data_portability': ["users can export their data", "users cannot export their data"]
        }

        results = {}
        
        for key, labels in categories.items():
            try:
                payload = {
                    "inputs": text,
                    "parameters": {
                        "candidate_labels": labels,
                        "multi_label": False
                    }
                }
                
                result = self._query_api("facebook/bart-large-mnli", payload)
                
                if result and 'labels' in result and 'scores' in result:
                    most_likely = result['labels'][0]
                    results[key] = most_likely == labels[0]
                else:
                    print(f"❌ Invalid API response for {key}")
                    results[key] = None
                    
            except Exception as e:
                print(f"❌ Error classifying {key}: {str(e)}")
                results[key] = None

        return results

    def qa_retention_extraction(self, text):
        """
        Extracts data retention duration using a Question Answering model via Hugging Face API.
        """
        print("\n--- QA Retention Extraction (API) ---")
        question = "How long is user data retained?"
        try:
            result = self._query_api("deepset/roberta-base-squad2", {
                "inputs": {
                    "question": question,
                    "context": text
                }
            })
            print(f"QA Retention Raw Result: {result}")
            
            if isinstance(result, dict) and 'answer' in result and result['score'] > 0.01:
                return result['answer']
            else:
                return "Not found (QA API)"
        except Exception as e:
            print(f"❌ Error in QA Retention Extraction (API): {str(e)}")
            return "Error (QA API)"