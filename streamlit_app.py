#!/usr/bin/env python3
"""
Athens Home Buyer Research Assistant - Web Interface
Streamlit web app for comprehensive neighborhood research (schools + crime/safety)
"""

import streamlit as st
import os
from school_info import get_school_info, format_complete_report
from ai_school_assistant import SchoolAIAssistant
from crime_analysis import analyze_crime_near_address, format_analysis_report
from unified_ai_assistant import UnifiedAIAssistant
from crime_visualizations import (
    create_category_chart_data,
    create_trend_chart_data,
    create_comparison_chart_data,
    create_safety_score_html,
    create_comparison_html,
    format_crime_stats_table,
    get_safety_color,
    get_category_colors
)

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
st.markdown('<p class="subtitle">AI-powered school & safety research for Athens-Clarke County, Georgia</p>', unsafe_allow_html=True)

# Disclaimer
st.markdown("""
<div class="disclaimer">
    ⚠️ <strong>Disclaimer:</strong> Data from public sources (Clarke County Schools, Georgia GOSA, Athens-Clarke Police).
    Always verify important information independently and visit neighborhoods in person.
    School zones, performance data, and crime statistics can change over time.
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
if 'unified_assistant' not in st.session_state:
    try:
        st.session_state.unified_assistant = UnifiedAIAssistant(api_key=api_key)
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
        placeholder="e.g., Is this a good area for families with young kids?",
        height=100,
        help="Ask about schools, safety, or overall neighborhood suitability"
    )

# Analysis options
st.markdown("#### 📊 Include in Analysis:")
col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 2])

with col_opt1:
    include_schools = st.checkbox("🎓 School Information", value=True, help="Include school assignments and performance data")

with col_opt2:
    include_crime = st.checkbox("🛡️ Crime & Safety Analysis", value=True, help="Include crime statistics and safety score")

with col_opt3:
    if include_schools and include_crime:
        st.info("💡 AI will synthesize insights across both schools and safety")
    elif include_schools:
        st.info("🎓 Showing school information only")
    elif include_crime:
        st.info("🛡️ Showing crime/safety information only")

# Search button
search_button = st.button("🔍 Search", use_container_width=True)

# Example questions
with st.expander("💡 Example Questions"):
    st.markdown("""
    **Sample Addresses:**
    - 150 Hancock Avenue, Athens, GA 30601 (downtown/UGA area)
    - 220 College Station Road, Athens, GA 30602 (suburban residential)
    - 1000 Jennings Mill Road, Athens, GA 30606 (southeast Athens)

    **Sample Questions (Schools Only):**
    - What are the test scores at this address?
    - How good are the schools?
    - What's the graduation rate at the high school?

    **Sample Questions (Safety Only):**
    - How safe is this neighborhood?
    - What types of crimes occur here?
    - Is crime increasing or decreasing?

    **Sample Questions (Comprehensive):**
    - Is this a good area for families with young kids?
    - What are the pros and cons of this neighborhood?
    - Should I buy a house here?
    - Is this suitable for raising a family?
    """)

# Process search
if search_button:
    if not address_input or not address_input.strip():
        st.warning("⚠️ Please enter an address")
    elif not question_input or not question_input.strip():
        st.warning("⚠️ Please enter a question")
    elif not include_schools and not include_crime:
        st.warning("⚠️ Please select at least one analysis type (Schools or Crime/Safety)")
    else:
        # Add Athens, GA if not present
        full_address = address_input
        if 'athens' not in address_input.lower():
            full_address = f"{address_input}, Athens, GA"

        # Show loading state
        loading_msg = "🔍 Analyzing"
        if include_schools and include_crime:
            loading_msg += " schools and crime data"
        elif include_schools:
            loading_msg += " school data"
        else:
            loading_msg += " crime data"
        loading_msg += f" for: {full_address}..."

        with st.spinner(loading_msg):
            try:
                # Get comprehensive analysis
                result = st.session_state.unified_assistant.get_comprehensive_analysis(
                    address=full_address,
                    question=question_input,
                    include_schools=include_schools,
                    include_crime=include_crime,
                    radius_miles=0.5,
                    months_back=12
                )

                if result['error']:
                    st.error(f"❌ {result['error']}")

                # Display results
                st.success(f"✓ Analysis Complete: {full_address}")

                # Show school summary if included
                if include_schools and result['school_info']:
                    st.markdown("### 🎓 School Assignments")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Elementary", result['school_info'].elementary)
                    with col2:
                        st.metric("Middle", result['school_info'].middle)
                    with col3:
                        st.metric("High", result['school_info'].high)

                # Show crime summary if included
                if include_crime and result['crime_analysis']:
                    crime = result['crime_analysis']

                    # Color-coded header based on safety score
                    safety_color = get_safety_color(crime.safety_score.score)
                    st.markdown(f"""
                    <div style="background-color: {safety_color}20; border-left: 4px solid {safety_color}; padding: 1em; border-radius: 0.5em; margin: 1em 0;">
                        <h3 style="color: {safety_color}; margin: 0;">🛡️ Crime & Safety Analysis</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    # Safety gauge and key metrics
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        # Safety score visual
                        safety_html = create_safety_score_html(crime.safety_score.score, crime.safety_score.level)
                        st.markdown(safety_html, unsafe_allow_html=True)

                    with col2:
                        # Key statistics table
                        stats_table = format_crime_stats_table(crime)

                        # Overview
                        st.markdown("**Overview:**")
                        for key, value in stats_table['Overview'].items():
                            st.markdown(f"• {key}: **{value}**")

                        # Most common crime
                        st.markdown(f"• Most Common: **{crime.statistics.most_common_crime}** ({crime.statistics.most_common_count} incidents)")

                    st.markdown("")  # Spacing

                    # Charts in tabs for better mobile experience
                    tab1, tab2, tab3 = st.tabs(["📊 By Category", "📈 Trends", "⚖️ Comparison"])

                    with tab1:
                        category_data = create_category_chart_data(crime)
                        st.bar_chart(category_data, color=list(get_category_colors().values()))

                        # Show percentages below chart
                        col_a, col_b, col_c, col_d = st.columns(4)
                        with col_a:
                            st.metric("Violent", f"{crime.statistics.violent_percentage:.1f}%")
                        with col_b:
                            st.metric("Property", f"{crime.statistics.property_percentage:.1f}%")
                        with col_c:
                            st.metric("Traffic", f"{crime.statistics.traffic_percentage:.1f}%")
                        with col_d:
                            st.metric("Other", f"{crime.statistics.other_percentage:.1f}%")

                    with tab2:
                        trend_data = create_trend_chart_data(crime)
                        st.bar_chart(trend_data)

                        # Show trend details
                        trend_color = "green" if crime.trends.trend == "decreasing" else "red" if crime.trends.trend == "increasing" else "gray"
                        trend_symbol = "📉" if crime.trends.trend == "decreasing" else "📈" if crime.trends.trend == "increasing" else "➡️"

                        st.markdown(f"""
                        <div style="text-align: center; padding: 1em; background: {trend_color}20; border-radius: 0.5em; margin-top: 1em;">
                            <div style="font-size: 1.5em;">{trend_symbol}</div>
                            <div style="font-weight: 600; color: {trend_color};">
                                {crime.trends.trend.title()}: {crime.trends.change_percentage:+.1f}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with tab3:
                        comparison_html = create_comparison_html(crime)
                        if comparison_html:
                            st.markdown(comparison_html, unsafe_allow_html=True)
                        else:
                            st.info("Comparison data not available")

                st.divider()

                # Display AI synthesis (if both included) or individual responses
                st.markdown("### 🤖 AI Analysis")

                if include_schools and include_crime and result['synthesis']:
                    # Show comprehensive synthesis
                    st.markdown(f'<div class="response-box">{result["synthesis"]}</div>', unsafe_allow_html=True)

                else:
                    # Show individual responses
                    if include_schools and result['school_response']:
                        st.markdown("#### 🎓 School Analysis")
                        st.markdown(f'<div class="response-box">{result["school_response"]}</div>', unsafe_allow_html=True)

                    if include_crime and result['crime_response']:
                        st.markdown("#### 🛡️ Crime & Safety Analysis")
                        st.markdown(f'<div class="response-box">{result["crime_response"]}</div>', unsafe_allow_html=True)

                # Data sources
                with st.expander("📚 Data Sources & Verification"):
                    sources_text = ""

                    if include_schools:
                        sources_text += """
**School Data:**
- Assignments: Clarke County Schools Official Street Index (2024-25)
- Performance: Georgia Governor's Office of Student Achievement (GOSA 2023-24)
- Verify: [clarke.k12.ga.us/page/school-attendance-zones](https://www.clarke.k12.ga.us/page/school-attendance-zones)
"""

                    if include_crime:
                        sources_text += """
**Crime & Safety Data:**
- Source: Athens-Clarke County Police Department
- Coverage: Last 12 months within 0.5 mile radius
- View crime map: [Athens-Clarke Crime Map](https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime)
"""

                    sources_text += """
**Important Notes:**
- All data from official public sources
- School zones and crime patterns can change over time
- This is for research purposes only - always verify independently
- Visit neighborhoods in person and talk to local residents
"""

                    st.markdown(sources_text)

                # Option to see raw data
                with st.expander("📊 View Complete Raw Data"):
                    if include_schools and result['school_info']:
                        st.markdown("**School Data:**")
                        st.text(format_complete_report(result['school_info']))

                    if include_crime and result['crime_analysis']:
                        st.markdown("**Crime Data:**")
                        st.text(format_analysis_report(result['crime_analysis']))

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Footer
st.markdown("""
<div class="footer">
    <p><strong>Athens Home Buyer Research Assistant (Beta)</strong></p>
    <p>Powered by Claude AI • Data from Clarke County Schools, Georgia GOSA, & Athens-Clarke Police</p>
    <p>Not affiliated with Clarke County School District, Georgia DOE, or Athens-Clarke County Government</p>
    <p>For research and informational purposes only • Always verify independently</p>
</div>
""", unsafe_allow_html=True)
