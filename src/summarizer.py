from transformers import pipeline
import torch
import os 
from dotenv import load_dotenv
import requests

load_dotenv()

class Policy_Summarizer:
    def __init__(self):
        self.summarizer = None
        try:
            # Force CPU mode to avoid torch class issues
            self.summarizer = pipeline(
                "summarization",
                model='facebook/bart-large-cnn',
                device=-1,  # Force CPU
                framework="pt"  # Explicitly use PyTorch
            )
            print("Successfully initialized summarizer on CPU")
        except Exception as e:
            print(f"Error initializing summarizer: {str(e)}")
            # Try alternative initialization
            try:
                import torch
                torch.set_num_threads(4)  # Limit CPU threads
                self.summarizer = pipeline(
                    "summarization",
                    model='facebook/bart-large-cnn',
                    device=-1,
                    framework="pt"
                )
                print("Successfully initialized summarizer with alternative settings")
            except Exception as e2:
                print(f"Failed to initialize summarizer: {str(e2)}")
                raise Exception("Could not initialize summarizer model")

    def chunk_text(self, text, max_tokens=400):
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_tokens):
            chunk = " ".join(words[i:i+max_tokens])
            chunks.append(chunk)
        return chunks

    def summarize_with_api(self, policy_text):
        API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}

        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()
        
        output = query({
            "inputs": policy_text[:1000],  # Limit input length
            "parameters": {"max_length": 150, "min_length": 50}
        })
        
        if isinstance(output, list) and len(output) > 0:
            return output[0].get('summary_text', 'Unable to generate summary')
        return "Error: Unable to generate summary"

    def summarize_policy(self, policy_text):
        print("Starting summarization process (Hugging Face API)...")
        print(f"Input text length: {len(policy_text)} characters")
        try:
            with open("prompts/summarization.txt", "r") as f:
                prompt_template = f.read().strip()

            input_text = f"{prompt_template}\n\n{policy_text}"
            chunks = self.chunk_text(input_text, max_tokens=400)

            summaries = []
            for i, chunk in enumerate(chunks):
                print(f"Chunk {i} length: {len(chunk.split())} words")
                try:
                    summary_text = self.summarize_with_api(chunk)
                    if summary_text and not summary_text.startswith("Error"):
                        summaries.append(summary_text)
                    else:
                        print(f"Warning: No summary generated for chunk {i}. Skipping.")
                except Exception as e:
                    print(f"Error summarizing chunk {i} via API: {e}")
                    continue

            if not summaries:
                return "Error: No summary could be generated. Try with a shorter or different text."

            combined_summary = " ".join(summaries)
            if len(summaries) > 1:
                try:
                    final_summary = self.summarize_with_api(combined_summary)
                    if final_summary and not final_summary.startswith("Error"):
                        final_summary_text = final_summary
                    else:
                        final_summary_text = combined_summary
                except Exception as e:
                    print(f"Error in final summarization via API: {e}")
                    final_summary_text = combined_summary
            else:
                final_summary_text = combined_summary

            return self._format_as_bullets(final_summary_text)

        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def _format_as_bullets(self, text):
        sentences = [s.strip() for s in text.split('. ') if s.strip()]
        bullets = []
        for sentence in sentences[:5]:
            # Ensure each bullet ends with a period
            if not sentence.endswith('.'):
                sentence += '.'
            bullets.append(f'- {sentence}')
        return '\n'.join(bullets)