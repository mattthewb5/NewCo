#!/usr/bin/env python3
"""
Athens Home Buyer Research Assistant - Web Interface
Streamlit web app for natural language school research
"""

import streamlit as st
import os
from school_info import get_school_info, format_complete_report
from ai_school_assistant import SchoolAIAssistant

# Page configuration
st.set_page_config(
    page_title="Athens Home Buyer Research Assistant",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        text-align: center;
        color: #1e3a8a;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 0.2em;
    }

    .subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.2em;
        margin-bottom: 2em;
    }

    /* Input section styling */
    .stTextInput > label {
        font-weight: 600;
        color: #334155;
    }

    .stTextArea > label {
        font-weight: 600;
        color: #334155;
    }

    /* Button styling */
    .stButton > button {
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        padding: 0.75em 2em;
        border-radius: 0.5em;
        border: none;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: #1d4ed8;
    }

    /* Response box styling */
    .response-box {
        background-color: #f8fafc;
        border-left: 4px solid #2563eb;
        padding: 1.5em;
        margin: 1em 0;
        border-radius: 0.5em;
    }

    /* Disclaimer styling */
    .disclaimer {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1em;
        margin: 2em 0;
        border-radius: 0.5em;
        font-size: 0.9em;
    }

    /* Info box */
    .info-box {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 1em;
        margin: 1em 0;
        border-radius: 0.5em;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85em;
        margin-top: 3em;
        padding-top: 2em;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-title">🏡 Athens Home Buyer Research Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-powered school information for Athens-Clarke County, Georgia</p>', unsafe_allow_html=True)

# Disclaimer
st.markdown("""
<div class="disclaimer">
    ⚠️ <strong>Disclaimer:</strong> Data from public sources (Clarke County Schools, Georgia GOSA).
    Always verify important information independently with Clarke County School District.
    School zones and performance data can change year-to-year.
</div>
""", unsafe_allow_html=True)

# Check for API key
api_key = os.environ.get('ANTHROPIC_API_KEY')

if not api_key:
    st.markdown("""
    <div class="info-box">
        ℹ️ <strong>Setup Required:</strong> To use AI features, set your ANTHROPIC_API_KEY environment variable.<br>
        Get your API key at: <a href="https://console.anthropic.com/" target="_blank">console.anthropic.com</a><br><br>
        <code>export ANTHROPIC_API_KEY='your-api-key-here'</code><br>
        <code>streamlit run streamlit_app.py</code>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Initialize session state
if 'assistant' not in st.session_state:
    try:
        st.session_state.assistant = SchoolAIAssistant(api_key=api_key)
        st.session_state.api_ready = True
    except Exception as e:
        st.session_state.api_ready = False
        st.error(f"❌ Error initializing AI assistant: {str(e)}")
        st.stop()

# Main input area
col1, col2 = st.columns([1, 1])

with col1:
    address_input = st.text_input(
        "📍 Property Address",
        placeholder="e.g., 150 Hancock Avenue, Athens, GA 30601",
        help="Enter a street address in Athens-Clarke County, GA"
    )

with col2:
    question_input = st.text_area(
        "❓ Your Question",
        placeholder="e.g., How good are the schools at this address?",
        height=100,
        help="Ask anything about the schools, test scores, or school quality"
    )

# Search button
search_button = st.button("🔍 Search", use_container_width=True)

# Example questions
with st.expander("💡 Example Questions"):
    st.markdown("""
    **Sample Addresses:**
    - 150 Hancock Avenue, Athens, GA 30601
    - 585 Reese Street, Athens, GA 30601
    - 195 Hoyt Street, Athens, GA 30601

    **Sample Questions:**
    - What are the test scores at this address?
    - How good are the schools?
    - Tell me about school quality for this property
    - What's the graduation rate at the high school?
    - What are the demographics of these schools?
    """)

# Process search
if search_button:
    if not address_input or not address_input.strip():
        st.warning("⚠️ Please enter an address")
    elif not question_input or not question_input.strip():
        st.warning("⚠️ Please enter a question")
    else:
        # Add Athens, GA if not present
        full_address = address_input
        if 'athens' not in address_input.lower():
            full_address = f"{address_input}, Athens, GA"

        # Show loading state
        with st.spinner(f"🔍 Looking up school data for: {full_address}..."):
            try:
                # First verify the address exists
                info = get_school_info(full_address)

                if not info:
                    st.error("❌ Address not found in Athens-Clarke County street index")
                    st.info("""
                    **Possible reasons:**
                    - Street is not in Athens-Clarke County
                    - Street name not recognized (try different abbreviation)
                    - Typo in street name

                    **Tips:**
                    - Try 'Street' instead of 'St', or vice versa
                    - Include full street name
                    - Make sure the address is in Athens-Clarke County, GA
                    """)
                else:
                    # Show basic school assignment
                    st.success(f"✓ Found: {full_address}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Elementary", info.elementary)
                    with col2:
                        st.metric("Middle", info.middle)
                    with col3:
                        st.metric("High", info.high)

                    st.divider()

                    # Get AI response
                    with st.spinner("🤖 Analyzing with AI..."):
                        try:
                            response = st.session_state.assistant.ask_claude_about_schools(
                                full_address,
                                question_input
                            )

                            # Display AI response
                            st.markdown("### 🤖 AI Analysis")
                            st.markdown(f'<div class="response-box">{response}</div>', unsafe_allow_html=True)

                            # Data sources
                            with st.expander("📚 Data Sources & Verification"):
                                st.markdown("""
                                **School Assignments:**
                                - Source: Clarke County Schools Official Street Index (2024-25)
                                - Verify: [clarke.k12.ga.us/page/school-attendance-zones](https://www.clarke.k12.ga.us/page/school-attendance-zones)

                                **Performance Data:**
                                - Source: Georgia Governor's Office of Student Achievement (GOSA)
                                - Data Year: 2023-24 School Year
                                - Verify: [gosa.georgia.gov/dashboards-data-report-card/downloadable-data](https://gosa.georgia.gov/dashboards-data-report-card/downloadable-data)

                                **Note:** School zones and performance data can change year-to-year. Always verify with the district.
                                """)

                            # Option to see raw data
                            with st.expander("📊 View Complete Raw Data"):
                                st.text(format_complete_report(info))

                        except Exception as e:
                            st.error(f"❌ Error getting AI response: {str(e)}")
                            st.info("Falling back to basic data display...")
                            st.text(format_complete_report(info))

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("""
<div class="footer">
    <p><strong>Athens Home Buyer Research Assistant (Beta)</strong></p>
    <p>Powered by Claude AI • Data from Clarke County Schools & Georgia GOSA</p>
    <p>Not affiliated with Clarke County School District or Georgia Department of Education</p>
    <p>For research and informational purposes only</p>
</div>
""", unsafe_allow_html=True)
