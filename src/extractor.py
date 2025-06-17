import re
import requests # Added for API calls
import os # Added for environment variables
from dotenv import load_dotenv # Assuming you use dotenv for ACCESS_TOKEN

load_dotenv() # Load environment variables

from transformers import pipeline

class PolicyExtractor:
    """
    Extracts key information from privacy policies using both keyword matching and NLP.
    """
    
    def __init__(self):
        print("\n=== Initializing Policy Extractor ===")
        self.classifier = None
        # self.qa_pipeline will not be initialized locally as we use API

        try:
            print("Attempting to load zero-shot classification model...")
            self.classifier = pipeline(
                "zero-shot-classification",
                model='facebook/bart-large-mnli',
                device=-1  # Force CPU to avoid torch issues
            )
            print("✅ Successfully initialized zero-shot classifier")
        except Exception as e:
            print(f"❌ Error initializing zero-shot classifier: {str(e)}")

        # No local QA pipeline initialization here as we're using the API

    def _query_qa_api(self, question: str, context: str):
        API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
        headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}

        payload = {
            "inputs": {
                "question": question,
                "context": context
            }
        }
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        return response.json()

    def extract_facts(self, text):
        """
        Main method to extract facts from privacy policy text.
        Combines results from both keyword and NLP extraction.
        
        Args:
            text (str): The privacy policy text to analyze
            
        Returns:
            dict: Dictionary containing extracted facts
        """
        print("\n=== Starting Fact Extraction ===")
        print(f"Input text length: {len(text)} characters")
        
        # Always do keyword extraction as it's reliable
        print("\n--- Starting Keyword Extraction ---")
        basic_facts = self.keyword_extraction(text)
        print("✅ Completed keyword extraction")
        print(f"Keyword extraction results: {basic_facts}")

        # Try NLP extraction if available
        if self.classifier is not None:
            print("\n--- Starting NLP Extraction (Zero-shot) ---")
            try:
                nlp_facts = self.nlp_extraction(text)
                basic_facts.update(nlp_facts)
                print("✅ Completed zero-shot NLP extraction")
            except Exception as e:
                print(f'❌ Zero-shot NLP extraction failed: {str(e)}')
        else:
            print('⚠️ Zero-shot NLP extraction not available')

        # Try Zero-Shot Retention Extraction
        if self.classifier is not None:
            print("\n--- Starting NLP Retention Extraction (Zero-shot) ---")
            try:
                retention_zero_shot = self.nlp_retention_extraction(text)
                basic_facts['retention_nlp_zeroshot'] = retention_zero_shot
                print(f"Zero-shot Retention: {retention_zero_shot}")
                print("✅ Completed zero-shot retention extraction")
            except Exception as e:
                print(f'❌ Zero-shot Retention extraction failed: {str(e)}')
                basic_facts['retention_nlp_zeroshot'] = "Error"
        else:
            print('⚠️ Zero-shot Retention extraction not available')

        # Try QA Retention Extraction using API
        print("\n--- Starting QA Retention Extraction (API) ---")
        try:
            retention_qa = self.qa_retention_extraction(text)
            basic_facts['retention_nlp_qa'] = retention_qa
            print(f"QA Retention: {retention_qa}")
            print("✅ Completed QA retention extraction (API)")
        except Exception as e:
            print(f'❌ QA Retention extraction failed (API): {str(e)}')
            basic_facts['retention_nlp_qa'] = "Error"
        
        print("\n=== Final Combined Results ===")
        print(f"Combined facts: {basic_facts}")
        return basic_facts
    
    def keyword_extraction(self, text):
        """
        Extracts facts using keyword matching and regex patterns.
        
        Args:
            text (str): The privacy policy text
            
        Returns:
            dict: Dictionary of extracted facts
        """
        text_lower = text.lower()
        facts = {}

        # Email collection detection
        email_keywords = ['email', 'e-mail', 'email address', 'contact information']
        facts['collects_emails'] = any(keyword in text_lower for keyword in email_keywords)

        # Tracking/analytics detection
        tracking_keywords = ['analytics', 'tracking', 'cookies', 'google analytics', 'facebook pixel']
        facts['uses_tracking'] = any(keyword in text_lower for keyword in tracking_keywords)

        # Data retention detection (keeping original regex for comparison)
        retention_patterns = [
            r'(\d+)\s*(year|month|day)s?',
            r'(indefinitely|permanently)',
            r'until.*?(delete|remove)'
        ]
        
        retention_duration = 'unknown'
        for pattern in retention_patterns:
            match = re.search(pattern, text_lower)
            if match:
                retention_duration = match.group(0)
                break
        facts['retention_duration'] = retention_duration

        # Third-party sharing detection
        sharing_keywords = ['third party', 'third-party', 'share', 'sharing', 'partners']
        no_sharing_keywords = ['do not share', 'not share', 'no sharing']

        facts['shares_data'] = any(keyword in text_lower for keyword in sharing_keywords)
        if any(keyword in text_lower for keyword in no_sharing_keywords):
            facts['shares_data'] = False

        return facts
    
    def nlp_extraction(self, text):
        """
        Uses zero-shot classification to extract facts from the policy.
        
        Args:
            text (str): The privacy policy text
            
        Returns:
            dict: Dictionary of extracted facts using NLP
        """
        if self.classifier is None:
            print("❌ Classifier not initialized, skipping NLP extraction")
            return {}

        print("\n--- NLP Classification Process ---")
        # Define the categories we want to classify
        categories = {
            'collects_emails': ["collects email addresses", "does not collect emails"],
            'uses_tracking': ["uses tracking tools", "no tracking or analytics"],
            'shares_data': ["shares data with third parties", "does not share user data"]
        }

        results = {}
        
        # Classify each category
        for key, labels in categories.items():
            try:
                print(f"\nClassifying: {key}")
                print(f"Labels: {labels}")
                
                result = self.classifier(text, labels)
                print(f"Raw classification result: {result}")
                
                # Get the most likely label
                most_likely = result['labels'][0]
                confidence = result['scores'][0]
                
                print(f"Most likely label: {most_likely}")
                print(f"Confidence: {confidence:.2f}")
                
                # Convert to boolean based on the positive label
                results[key] = most_likely == labels[0]
                print(f"Final classification for {key}: {results[key]}")
                
            except Exception as e:
                print(f"❌ Error classifying {key}: {str(e)}")
                results[key] = None

        print("\n--- NLP Extraction Summary ---")
        print(f"Final NLP results: {results}")
        return results

    def nlp_retention_extraction(self, text):
        """
        Extracts data retention duration using zero-shot classification.
        """
        if self.classifier is None:
            return "N/A (Classifier not initialized)"
        
        print("\n--- Zero-Shot Retention Classification ---")
        # Define candidate labels for retention duration
        # More specific labels can be added based on common policy terms
        retention_labels = [
            "retains data indefinitely",
            "retains data for 1 year",
            "retains data for 6 months",
            "retains data for 3 months",
            "retains data for 30 days",
            "retains data for less than 30 days",
            "does not specify data retention period"
        ]
        
        try:
            result = self.classifier(text, retention_labels, multi_label=False)
            print(f"Zero-Shot Retention Raw Result: {result}")
            return result['labels'][0]  # Return the most likely label
        except Exception as e:
            print(f"❌ Error in Zero-Shot Retention Classification: {str(e)}")
            return "Error (Zero-Shot)"

    def qa_retention_extraction(self, text):
        """
        Extracts data retention duration using a Question Answering model via Hugging Face API.
        """
        print("\n--- QA Retention Extraction (API) ---")
        question = "How long is user data retained?"
        try:
            # Use the new API querying method
            result = self._query_qa_api(question=question, context=text)
            print(f"QA Retention Raw Result: {result}")
            
            # The API result is usually a dictionary with 'answer' and 'score'
            # Check for confident answers
            if isinstance(result, dict) and 'answer' in result and result['score'] > 0.1:
                return result['answer']
            else:
                return "Not found (QA API)"
        except Exception as e:
            print(f"❌ Error in QA Retention Extraction (API): {str(e)}")
            return "Error (QA API)"