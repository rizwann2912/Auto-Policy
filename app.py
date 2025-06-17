import streamlit as st
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from summarizer import Policy_Summarizer
from extractor import PolicyExtractor
from comparator import PolicyComparator
from database import init_db, save_policy_to_db, load_policies_from_db

# Page config
st.set_page_config(
    page_title="Privacy Policy Reader",
    page_icon="🔍",
    layout="wide"
)

policy_dir = "data/companies"
available_policies = {
    "Facebook": "facebook.txt",
    "AWS": "aws.txt",
    "OpenAI": "openai.txt",
    "Microsoft": "microsoft.txt",
    "InternShala": 'internshala.txt'
}

# Initialize models (cache them for performance)
@st.cache_resource
def load_models():
    summarizer = Policy_Summarizer()
    extractor = PolicyExtractor()
    comparator = PolicyComparator()
    return summarizer, extractor, comparator

# Initialize database when the app starts
init_db()

def save_policy(website_name, policy_text):
    """Save a policy to the database"""
    save_policy_to_db(website_name, policy_text)

def main():
    st.title("🔍 Privacy Policy Reader")
    st.markdown("""
    ### Your Personal Privacy Policy Assistant
    Paste privacy policies from websites you use to understand what data they collect and how they use it.
    """)
    
    # Load models
    with st.spinner("Loading AI models..."):
        summarizer, extractor, comparator = load_models()

    # Sidebar for sample policies
    st.sidebar.header("📚 Sample Policies")
    selected_company = st.sidebar.selectbox(
        "Load a sample policy:", 
        ["None"] + list(available_policies.keys())
    )

    if selected_company != "None":
        with open(os.path.join(policy_dir, available_policies[selected_company]), "r", encoding="utf-8") as f:
            st.session_state.current_policy = f.read()
            st.session_state.current_website = selected_company
    
    # Sidebar for saved policies (from database)
    st.sidebar.header("💾 Your Policy Library")
    
    # Load saved policies from the database
    saved_policies = load_policies_from_db()
    
    if saved_policies:
        st.sidebar.subheader("Saved Policies")
        for website, data in saved_policies.items():
            if st.sidebar.button(f"📄 {website} (Saved: {data['date']})", key=f"load_{website}"):
                st.session_state.current_policy = data['text']
                st.session_state.current_website = website
    else:
        st.sidebar.info("No policies saved yet. Analyze a policy to save it!")
    
    # Main interface
    st.subheader("📄 Privacy Policy")
    website_name = st.text_input("Website Name:", 
                                 value=st.session_state.get('current_website', ''),
                                 placeholder="e.g., Facebook, Google, etc.")
    policy_text = st.text_area(
        "Paste the privacy policy here:",
        value=st.session_state.get('current_policy', ''),
        height=300,
        placeholder="Copy and paste the privacy policy text here..."
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 Save Policy", type="secondary", use_container_width=True):
            if website_name and policy_text:
                save_policy(website_name, policy_text)
                st.success(f"Policy for {website_name} saved!")
            else:
                st.error("Please enter both website name and policy text!")
    
    with col2:
        analyze_button = st.button("🔍 Analyze Policy", type="primary", use_container_width=True)
    
    if analyze_button:
        if not policy_text.strip():
            st.error("Please enter a privacy policy to analyze!")
            return
        
        # Automatically save the policy if a website name is provided and it's a new policy
        if website_name and policy_text:
            save_policy(website_name, policy_text)

        with st.spinner("Analyzing policy..."):
            # Generate summary
            with st.expander("📝 Policy Summary", expanded=True):
                summary = summarizer.summarize_policy(policy_text)
                st.markdown(summary)
            
            # Extract key information
            extracted_facts = extractor.extract_facts(policy_text)
            
            # Display critical information
            st.subheader("⚠️ Critical Information")
            
            # Create three columns for different types of information
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 📊 Data Collection")
                if extracted_facts.get('collects_emails'):
                    st.warning("This website collects email addresses")
                if extracted_facts.get('uses_tracking'):
                    st.warning("This website uses tracking/analytics")
                if extracted_facts.get('collects_location'):
                    st.warning("This website collects location data")
            
            with col2:
                st.markdown("#### 🤝 Data Sharing")
                if extracted_facts.get('shares_data'):
                    st.error("This website shares data with third parties")
                
                st.markdown("#### ⏳ Data Retention")
                retention = extracted_facts.get('retention_duration', 'unknown')
                if retention != 'unknown':
                    st.info(f"Data is retained for: {retention}")
            
            with col3:
                st.markdown("#### 👤 Your Rights")
                if extracted_facts.get('right_to_delete'):
                    st.success("You have the right to request data deletion")
                if extracted_facts.get('right_to_access'):
                    st.success("You have the right to access your data")
                if extracted_facts.get('data_portability'):
                    st.success("You have the right to export your data")
                if extracted_facts.get('right_to_correction'):
                    st.success("You have the right to correct your data")
            
            # Detailed Analysis
            st.subheader("🔍 Detailed Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Data Collection & Usage")
                for k, v in extracted_facts.items():
                    if k in ['collects_emails', 'uses_tracking', 'collects_location', 'shares_data']:
                        if v is True:
                            st.markdown(f"✅ {k.replace('_', ' ').title()}")
                        elif v is False:
                            st.markdown(f"❌ {k.replace('_', ' ').title()}")
                        elif v != "unknown":
                            st.markdown(f"ℹ️ {k.replace('_', ' ').title()}: {v}")
            
            with col2:
                st.markdown("#### User Rights & Controls")
                for k, v in extracted_facts.items():
                    if k in ['right_to_delete', 'right_to_access', 'data_portability', 'right_to_correction', 'opt_out_rights']:
                        if v is True:
                            st.markdown(f"✅ {k.replace('_', ' ').title()}")
                        elif v is False:
                            st.markdown(f"❌ {k.replace('_', ' ').title()}")
                        elif v != "unknown":
                            st.markdown(f"ℹ️ {k.replace('_', ' ').title()}: {v}")

if __name__ == "__main__":
    main()