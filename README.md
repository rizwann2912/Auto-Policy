# 🔍 Privacy Policy Reader

## Your Personal Privacy Policy Assistant

This application helps everyday users understand lengthy and complex privacy policies and terms and conditions from various websites. Instead of sifting through pages of legal jargon, users can paste a policy, and the app will provide key insights, highlight important clauses, and detail their rights.

---

## ✨ Features

*   **Intelligent Summarization**: Get concise, easy-to-understand summaries of privacy policies, broken down by key sections like Data Collection, Data Usage, Data Sharing, User Rights, and Data Security.
*   **Fact Extraction**: Automatically identify critical information such as:
    *   Whether email addresses, tracking data, or location data are collected.
    *   If data is shared with third parties.
    *   Data retention periods.
    *   Any mentioned age restrictions.
*   **User Rights Highlight**: Clearly indicates if the policy grants users rights like:
    *   Right to data deletion.
    *   Right to data access.
    *   Data portability.
    *   Opt-out rights.
    *   Right to data correction.
*   **Persistent Policy Library**: Save policies for different websites to a local database (`policies.db`), allowing you to revisit and analyze them later.
*   **Sample Policies**: Load pre-included privacy policies from well-known companies for quick demonstration and analysis.
*   **Hugging Face API Powered**: Leverages advanced NLP models from Hugging Face's Inference API, ensuring powerful analysis without requiring local model downloads:
    *   **Zero-shot classification**: `facebook/bart-large-mnli`
    *   **Summarization**: `facebook/bart-large-cnn`
    *   **Question Answering**: `deepset/roberta-base-squad2`
---

## 🚀 Getting Started

Follow these steps to set up and run the Privacy Policy Reader on your local machine.

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/rizwann2912/Policy-Analyzer.git
    cd Policy-Analyzer
    ```

2.  **Create a virtual environment (recommended)**:
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Hugging Face API Token Setup

This application uses Hugging Face's Inference API. You need an API token to use the NLP models.

1.  **Get your Hugging Face API Token**:
    *   Go to [Hugging Face](https://huggingface.co/) and create a free account if you don't have one.
    *   Navigate to your [settings page](https://huggingface.co/settings/tokens) to generate a new access token. Make sure it has "read" permissions.

2.  **Create a `.env` file**:
    In the root directory of your project (the `Auto-Policy` folder), create a file named `.env`.

3.  **Add your token to `.env`**:
    Open the `.env` file and add the following line, replacing `YOUR_HF_ACCESS_TOKEN` with the token you generated:
    ```
    ACCESS_TOKEN=hf_YOUR_HF_ACCESS_TOKEN
    ```

### Running the Application

1.  **Initialize the database**:
    The application uses a local SQLite database to store saved policies. Run this once to create the database file:
    ```bash
    python src/database.py
    ```
    This will create a `policies.db` file in the root directory.

2.  **Launch the Streamlit app**:
    ```bash
    streamlit run app.py
    ```

    The application will open in your default web browser (usually at `http://localhost:8501`).

---

## 📖 Usage

1.  **Paste a Privacy Policy**: Copy the text of a privacy policy from any website and paste it into the large text area.
2.  **Enter Website Name**: Provide a name for the website (e.g., "Google", "Amazon") in the input field above the text area.
3.  **Analyze**: Click the "🔍 Analyze Policy" button. The application will summarize the policy and extract key information.
    *   The policy will be automatically saved to your "Policy Library" if a website name is provided.
4.  **Save Manually**: If you prefer, you can click the "💾 Save Policy" button to manually save the current policy text.
5.  **Load Saved Policies**: In the left sidebar, under "💾 Your Policy Library", you'll find a list of all previously saved policies. Click on any policy to load it back into the text area for review.
6.  **Load Sample Policies**: Under "📚 Sample Policies" in the sidebar, you can select from a few pre-loaded company policies to quickly see the app's functionality.

---

## 📁 Project Structure

```
Auto-Policy/
├── app.py                  # Main Streamlit application
├── data/
│   ├── companies/          # Contains sample privacy policy text files
│   └── sample_policies/
├── prompts/                # Text files for prompt templates (e.g., summarization)
├── src/
│   ├── comparator.py       # Logic for comparing extracted facts and generating recommendations
│   ├── database.py         # SQLite database operations (save, load policies)
│   ├── extractor.py        # Extracts key facts from privacy policies (uses Hugging Face API)
│   └── summarizer.py       # Summarizes privacy policies (uses Hugging Face API)
├── policies.db             # (Generated) SQLite database file for saved policies
├── .env                    # (User-created) Stores environment variables like Hugging Face API token
├── README.md               # This README file
└── requirements.txt        # Python dependencies
```

---

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements, new features, or bug fixes, please feel free to open an issue or submit a pull request.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
