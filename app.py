import streamlit as st
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from summarizer import Policy_Summarizer
from extractor import PolicyExtractor
from comparator import PolicyComparator

# Page config
st.set_page_config(
    page_title="AutoPolicy Analyzer",
    page_icon="🔍",
    layout="wide"
)

# Initialize models (cache them for performance)
@st.cache_resource
def load_models():
    summarizer = Policy_Summarizer()
    extractor = PolicyExtractor()
    comparator = PolicyComparator()
    return summarizer, extractor, comparator

severity_styles = {
    "high": {
        "color": "#fff",        # white font
        "bg": "#8B0000",        # dark red background
        "icon": "🚨"
    },
    "medium": {
        "color": "#B8860B",     # dark yellow
        "bg": "#FFFACD",        # light yellow
        "icon": "⚠️"
    },
    "low": {
        "color": "#4682B4",     # steel blue
        "bg": "#E0FFFF",        # light blue
        "icon": "ℹ️"
    }
}

def chunk_text(text, max_tokens=900):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunk = " ".join(words[i:i+max_tokens])
        chunks.append(chunk)
    return chunks

def summarize_policy(self, policy_text):
    try:
        with open("prompts/summarization.txt", "r") as f:
            prompt_template = f.read().strip()

        input_text = f"{prompt_template}\n\n{policy_text}"
        chunks = chunk_text(input_text, max_tokens=900)  # 900 to be safe

        summaries = []
        for chunk in chunks:
            summary = self.summarizer(
                chunk,
                max_length=150,
                min_length=60,
                do_sample=False
            )
            summaries.append(summary[0]['summary_text'])

        # Optionally, summarize the combined summary
        combined_summary = " ".join(summaries)
        if len(summaries) > 1:
            final_summary = self.summarizer(
                combined_summary,
                max_length=150,
                min_length=60,
                do_sample=False
            )[0]['summary_text']
        else:
            final_summary = combined_summary

        return self._format_as_bullets(final_summary)

    except Exception as e:
        return f"Error generating summary: {str(e)}"

def main():
    st.title("🔍 AutoPolicy: Smart Policy Analyzer")
    st.markdown("*Powered by Hugging Face Transformers*")
    
    # Load models
    with st.spinner("Loading AI models..."):
        summarizer, extractor, comparator = load_models()
    
    # Sidebar for sample policies
    st.sidebar.header("📋 Sample Policies")
    if st.sidebar.button("Load Startup Policy"):
        sample_policy = """Our startup collects user email addresses for login. We also use Google Analytics to track page views and user behavior. We retain user data for up to 1 year.

We do not collect any financial or health-related data. Users may contact us to request data deletion.

We do not share user data with third parties unless legally required."""
        st.session_state.policy_text = sample_policy
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📄 Privacy Policy")
        policy_text = st.text_area(
            "Paste your privacy policy here:",
            value=st.session_state.get('policy_text', ''),
            height=300,
            placeholder="Enter your privacy policy text..."
        )
    
    with col2:
        st.subheader("✅ Your Claims")
        email = st.checkbox("We collect user emails")
        tracking = st.checkbox("We use analytics/tracking")
        retention = st.selectbox(
            "Data retention period:",
            ["Not specified", "3 months", "6 months", "1 year", "2+ years"]
        )
        sharing = st.checkbox("We share data with third parties")
    
    # Analysis button
    if st.button("🔍 Analyze Policy", type="primary"):
        if not policy_text.strip():
            st.error("Please enter a privacy policy to analyze!")
            return
        
        with st.spinner("Analyzing policy..."):
            # Generate summary
            with st.expander("📝 Policy Summary", expanded=True):
                summary = summarizer.summarize_policy(policy_text)
                st.markdown(summary)
            
            # Extract facts
            extracted_facts = extractor.extract_facts(policy_text)
            
            # User claims
            user_claims = {
                "collects_emails": email,
                "uses_tracking": tracking,
                "retains_data_duration": retention,
                "shares_data": sharing
            }
            
            # Find mismatches with detailed analysis
            mismatches = comparator.find_mismatches(extracted_facts, user_claims)
            
            # Generate summary report
            report = comparator.generate_summary_report(mismatches)
            
            # Display results in tabs
            tab1, tab2, tab3 = st.tabs(["🔍 Analysis", "⚠️ Mismatches", "📋 Recommendations"])
            
            with tab1:
                st.markdown("<h2>🤖 What AI Found</h2>", unsafe_allow_html=True)
                st.markdown("<ul style='font-size: 18px;'>", unsafe_allow_html=True)
                for k, v in extracted_facts.items():
                    color = "#8B0000" if v is True else "#4682B4" if v is False else "#FFA500" if v == "unknown" else "#222"
                    st.markdown(
                        f"<li><b>{k.replace('_', ' ').title()}:</b> <span style='color:{color};'>{v}</span></li>",
                        unsafe_allow_html=True
                    )
                st.markdown("</ul>", unsafe_allow_html=True)

                st.markdown("<h2>👤 Your Claims</h2>", unsafe_allow_html=True)
                st.markdown("<ul style='font-size: 18px;'>", unsafe_allow_html=True)
                for k, v in user_claims.items():
                    color = "#8B0000" if v is True else "#4682B4" if v is False else "#FFA500" if v == "Not specified" else "#222"
                    st.markdown(
                        f"<li><b>{k.replace('_', ' ').title()}:</b> <span style='color:{color};'>{v}</span></li>",
                        unsafe_allow_html=True
                    )
                st.markdown("</ul>", unsafe_allow_html=True)
            
            with tab2:
                if mismatches:
                    st.error(f"Found {len(mismatches)} potential mismatches!")
                    
                    # Group mismatches by severity
                    severity_groups = {"high": [], "medium": [], "low": []}
                    for key, mismatch in mismatches.items():
                        severity = mismatch.get("severity", "medium")
                        severity_groups[severity].append((key, mismatch))
                    
                    # Display mismatches by severity
                    for severity in ["high", "medium", "low"]:
                        if severity_groups[severity]:
                            style = severity_styles[severity]
                            st.markdown(
                                f"<h3 style='color:{style['color']};'>{style['icon']} {severity.title()} Severity Issues</h3>",
                                unsafe_allow_html=True
                            )
                            for key, mismatch in severity_groups[severity]:
                                st.markdown(
                                    f'''
                                    <div style='background-color:{style['bg']};padding:16px;border-radius:8px;margin-bottom:16px;'>
                                        <b style='color:{style['color']};'>{mismatch.get('field_description', key.replace('_', ' ').title())}:</b><br>
                                        <ul>
                                            <li><b>Policy says:</b> <code>{mismatch['policy_value']}</code></li>
                                            <li><b>You claim:</b> <code>{mismatch['user_value']}</code></li>
                                        </ul>
                                        <i>{mismatch['explanation']}</i>
                                    </div>
                                    ''',
                                    unsafe_allow_html=True
                                )
                else:
                    st.success("✅ No mismatches found! Your claims align with your policy.")
            
            with tab3:
                if mismatches:
                    st.subheader("📋 Recommendations")
                    recommendations = comparator._generate_recommendations(mismatches)
                    for rec in recommendations:
                        st.write(f"• {rec}")
                else:
                    st.success("✅ Your policy is well-aligned with your claims!")

if __name__ == "__main__":
    main()