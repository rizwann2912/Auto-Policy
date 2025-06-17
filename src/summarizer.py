import os 
from dotenv import load_dotenv
import requests

load_dotenv()

class Policy_Summarizer:
    """
    Summarizes privacy policies using Hugging Face API.
    Provides section-specific summaries focusing on user-relevant information.
    """
    
    def __init__(self):
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

    def summarize_with_api(self, text, max_length=150, min_length=50):
        """Summarize text using Hugging Face API"""
        payload = {
            "inputs": text[:1000],
            "parameters": {
                "max_length": max_length,
                "min_length": min_length,
                "do_sample": False
            }
        }
        
        result = self._query_api("facebook/bart-large-cnn", payload)
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('summary_text', 'Unable to generate summary')
        return "Error: Unable to generate summary"

    def summarize_policy(self, policy_text):
        """Generate a comprehensive summary of the privacy policy focusing on user-relevant information."""
        print("Starting summarization process...")
        print(f"Input text length: {len(policy_text)} characters")
        
        try:
            # Generate section-specific summaries
            sections = {
                "Data Collection": self._extract_section(policy_text, ["collect", "collection", "data we collect", "information we collect"]),
                "Data Usage": self._extract_section(policy_text, ["use", "usage", "how we use", "purpose"]),
                "Data Sharing": self._extract_section(policy_text, ["share", "sharing", "third party", "third-party"]),
                "User Rights": self._extract_section(policy_text, ["rights", "access", "delete", "portability", "control"]),
                "Data Security": self._extract_section(policy_text, ["security", "protect", "safeguard", "encrypt"])
            }
            
            summaries = []
            for section_name, section_text in sections.items():
                if section_text:
                    try:
                        summary = self.summarize_with_api(
                            section_text,
                            max_length=100,
                            min_length=30
                        )
                        if summary and not summary.startswith("Error"):
                            summaries.append(f"### {section_name}\n{summary}")
                    except Exception as e:
                        print(f"Error summarizing {section_name}: {e}")
                        continue
            
            if not summaries:
                return "Error: No summary could be generated. Try with a shorter or different text."
            
            # Generate overall summary
            try:
                overall_summary = self.summarize_with_api(
                    policy_text,
                    max_length=150,
                    min_length=50
                )
                if overall_summary and not overall_summary.startswith("Error"):
                    summaries.insert(0, f"### Overall Summary\n{overall_summary}")
            except Exception as e:
                print(f"Error generating overall summary: {e}")
            
            return "\n\n".join(summaries)

        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def _extract_section(self, text, keywords):
        """Extract relevant section of text based on keywords."""
        sentences = text.split('. ')
        section_sentences = []
        
        for sentence in sentences:
            if any(keyword.lower() in sentence.lower() for keyword in keywords):
                section_sentences.append(sentence)
        
        return '. '.join(section_sentences) if section_sentences else ""
    
    def _format_as_bullets(self, text):
        """Format text as bullet points."""
        sentences = [s.strip() for s in text.split('. ') if s.strip()]
        bullets = []
        for sentence in sentences:
            if not sentence.endswith('.'):
                sentence += '.'
            bullets.append(f'- {sentence}')
        return '\n'.join(bullets)