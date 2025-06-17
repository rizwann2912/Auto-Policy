from transformers import pipeline
import torch
class Policy_Summarizer:
    def __init__(self):
        self.summarizer = pipeline(
            "summarization",
            model= 'facebook/bart-large-cnn',
            device=0 if torch.cuda_is_available() else -1
        )

    def summarize_policy(self,policy_text):

        with open("prompts/summarization.txt", "r") as f:
            prompt_template = f.read()

        try:
            summary = self.summarizer(
                policy_text,
                max_length=150,
                min_length = 50,
                do_sample = False
            )

            summary_text = summary[0]['summary_text']
        
            formatted_summary = self._format_as_bullets(summary_text)

        except Exception as e:
            return f"Error generating summary: {str(e)}"
        
    
    def _format_as_bullets(self,text):

        sentences = text.split('. ')
        bullets = []

        for sentence in (sentences[:5]):
            if sentence.strip():
                bullets.append(f'• {sentence.strip()}')
        return '\n'.join(bullets)
    
