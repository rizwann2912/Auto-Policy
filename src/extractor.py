import re
from transformers import pipeline

class PolicyExtractor:
    
    def __init__(self):
        self.classifier = pipeline(
                                   "zero-shot-classification",
                                   model='facebook/bart-large-mnli')
        
    def extract_facts(self,text):
    # basic keyword extraction using regex
        basic_facts = self.keyword_extraction(text)

        # extraction using nlp
        try:
            nlp_facts = self.nlp_extarction(text)
            basic_facts.update(nlp_facts)
        except: 
            print('Using keyword extraction as nlp extraction failed')
            pass

        return basic_facts
    
    def keyword_extraction(self,text):
        text_lower = text.lower()

        email_keywords = ['email','e-mail','email address','contact information']
        collects_email = any([keyword in text_lower for keyword in email_keywords])

        tracking_keywords = ['analytics','tracking','cookies','googel analytics','facebook pixel']
        uses_tracking = any(keyword in text_lower for keyword in tracking_keywords)

        # retention detection

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

        # Third party sharing detection
        sharing_keywords = ['third party','third-party','share','sharing','partners']
        no_sharing_keywords = ['do not share','not share','no sharing']

        shares_data = any(keyword in text_lower for keyword in sharing_keywords)
        if any(keyword in text_lower for keyword in no_sharing_keywords):
            shares_data = False

        return {
            'collects emails':collects_email,
            "uses_tracking":uses_tracking,
            'retention_duration':retention_duration,
            'shares_data': shares_data
        }
    

    def nlp_extraction(self,text):
        '''
        Extraction using zero-shot-classification
        '''
        email_labels = ["collects email addresses", "does not collect emails"]
        tracking_labels = ["uses tracking tools", "no tracking or analytics"]
        sharing_labels = ["shares data with third parties", "does not share user data"]

        results = {}

        email_result = self.classifier(text,email_labels)
        results['collects_emails'] = email_result['labels'][0]=='collects email addresses'

        tracking_results = self.classifier(text,tracking_labels)
        results['uses_tarcking'] = tracking_results['labels'][0]=='uses tracking tools'

        sharing_results = self.classifier(text,sharing_labels)
        results['shares_data'] = sharing_results['labels'][0]=='shares data with third parties'

        return results