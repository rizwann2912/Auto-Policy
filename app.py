import streamlit as st
import sys
import os
from datetime import datetime

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

    # New: Sidebar for Recent Reports
    st.sidebar.header("📈 Recent Reports")
    if 'recent_reports' not in st.session_state:
        st.session_state.recent_reports = []

    if st.session_state.recent_reports:
        for i, report_entry in enumerate(st.session_state.recent_reports):
            if st.sidebar.button(f"📄 {report_entry['website_name']} ({report_entry['date']})", key=f"recent_report_{i}"):
                st.session_state.current_policy = report_entry['policy_text']
                st.session_state.current_website = report_entry['website_name']
                st.session_state.analysis_to_display = report_entry['full_analysis']
                st.rerun()
    else:
        st.sidebar.info("No recent reports. Analyze a policy to see it here!")

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
    
    st.markdown("<hr style='height:1px;border:none;color:#333;background-color:#333;' />", unsafe_allow_html=True)

    if st.button("🔄 Reset/Clear Input", use_container_width=True):
        st.session_state.current_policy = ""
        st.session_state.current_website = ""
        if 'analysis_to_display' in st.session_state:
            del st.session_state.analysis_to_display
        st.rerun()

    if analyze_button:
        if not policy_text.strip():
            st.error("Please enter a privacy policy to analyze!")
            return
        
        # Automatically save the policy to DB if a website name is provided (persistent save)
        if website_name and policy_text:
            save_policy(website_name, policy_text)

        with st.spinner("Analyzing policy(May take 30 seconds for large files as we are using small model)..."):
            # Generate summary
            summary = summarizer.summarize_policy(policy_text)
            
            # Extract key information
            extracted_facts = extractor.extract_facts(policy_text)

            # Store full analysis results in session state for re-display
            full_analysis_results = {
                'summary': summary,
                'extracted_facts': extracted_facts
            }
            st.session_state.analysis_to_display = full_analysis_results

            # Add to recent reports (temporary, session-based)
            if 'recent_reports' not in st.session_state:
                st.session_state.recent_reports = []

            # Add to the beginning of the list for most recent at top
            st.session_state.recent_reports.insert(0, {
                'website_name': website_name if website_name else "Unnamed Policy",
                'date': datetime.now().strftime("%H:%M:%S"), # Use HH:MM:SS for brevity
                'policy_text': policy_text, 
                'full_analysis': full_analysis_results 
            })
            # Limit recent reports to a reasonable number, e.g., 5
            st.session_state.recent_reports = st.session_state.recent_reports[:5]

    # Display analysis results if available in session state
    if 'analysis_to_display' in st.session_state:
        display_results = st.session_state.analysis_to_display
        extracted_facts_display = display_results['extracted_facts']

        with st.expander("📝 Policy Summary", expanded=True):
            st.markdown(display_results['summary'])
            
        # Display critical information
        st.subheader("⚠️ Critical Information")
        
        # Create three columns for different types of information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📊 Data Collection")
            if extracted_facts_display.get('collects_emails'):
                st.warning("This website collects email addresses")
            if extracted_facts_display.get('uses_tracking'):
                st.warning("This website uses tracking/analytics")
            if extracted_facts_display.get('collects_location'):
                st.warning("This website collects location data")
        
        with col2:
            st.markdown("#### 🤝 Data Sharing")
            if extracted_facts_display.get('shares_data'):
                st.error("This website shares data with third parties")
            
            st.markdown("#### ⏳ Data Retention")
            retention = extracted_facts_display.get('retention_duration', 'unknown')
            display_retention = retention if retention != 'unknown' else 'not mentioned in policy'
            st.markdown(f"<div style='background-color:#B22222;padding:10px;border-radius:5px;color:#FFFFFF;'><b>Data is retained for:</b> {display_retention}</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("#### 👤 Your Rights")
            if extracted_facts_display.get('right_to_delete'):
                st.success("You have the right to request data deletion")
            if extracted_facts_display.get('right_to_access'):
                st.success("You have the right to access your data")
            if extracted_facts_display.get('data_portability'):
                st.success("You have the right to export your data")
            if extracted_facts_display.get('right_to_correction'):
                st.success("You have the right to correct your data")
        
        # Detailed Analysis
        st.subheader("🔍 Detailed Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Data Collection & Usage")
            for k, v in extracted_facts_display.items():
                if k in ['collects_emails', 'uses_tracking', 'collects_location', 'shares_data']:
                    if v is True:
                        st.markdown(f"✅ {k.replace('_', ' ').title()}")
                    elif v is False:
                        st.markdown(f"❌ {k.replace('_', ' ').title()}")
                    elif v != "unknown":
                        st.markdown(f"ℹ️ {k.replace('_', ' ').title()}: {v}")
        
        with col2:
            st.markdown("#### User Rights & Controls")
            for k, v in extracted_facts_display.items():
                if k in ['right_to_delete', 'right_to_access', 'data_portability', 'right_to_correction', 'opt_out_rights']:
                    if v is True:
                        st.markdown(f"✅ {k.replace('_', ' ').title()}")
                    elif v is False:
                        st.markdown(f"❌ {k.replace('_', ' ').title()}")
                    elif v != "unknown":
                        st.markdown(f"ℹ️ {k.replace('_', ' ').title()}: {v}")

if __name__ == "__main__":
    main()