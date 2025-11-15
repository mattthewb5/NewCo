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
from address_extraction import extract_address_from_query
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

# About the Data - Expandable Information Section
with st.expander("📖 About the Data - Sources, Updates & Limitations"):
    st.markdown("""
    ### 📚 Data Sources

    This tool combines data from three official sources:

    **School Information:**
    - **School Assignments**: Clarke County School District Official Street Index (2024-25 school year)
    - **School Performance**: Georgia Governor's Office of Student Achievement (GOSA) - 2023-24 data
    - **Metrics**: CCRPI scores, Content Mastery, Literacy/Math proficiency, Graduation rates
    - **Verify**: [clarke.k12.ga.us/page/school-attendance-zones](https://www.clarke.k12.ga.us/page/school-attendance-zones)

    **Crime & Safety Information:**
    - **Source**: Athens-Clarke County Police Department Official Database
    - **Coverage**: Last 12 months of reported incidents
    - **Search Radius**: 0.5 miles from address (configurable)
    - **Categories**: Violent, Property, Traffic, and Other offenses
    - **Verify**: [Athens-Clarke Crime Map](https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime)

    ---

    ### 🔄 Update Frequency

    - **School Assignments**: Updated annually (current: 2024-25 school year)
    - **School Performance**: Updated annually after state assessment (current: 2023-24 data)
    - **Crime Data**:
      - Individual address queries: Cached for 24 hours
      - Athens baseline comparison: Refreshed weekly
      - Source database: Updated regularly by Athens-Clarke PD
    - **AI Analysis**: Generated in real-time using Claude 3 Haiku

    ---

    ### ⚠️ Important Limitations

    **What This Tool DOES Provide:**
    - ✓ School assignments for a specific address
    - ✓ School performance metrics from official state data
    - ✓ Crime statistics within a radius of the address
    - ✓ Safety trends and comparisons to Athens average
    - ✓ AI-synthesized insights combining schools and safety

    **What This Tool DOES NOT Provide:**
    - ✗ Home prices or property values
    - ✗ Traffic patterns or commute times
    - ✗ Parks, recreation, or walkability scores
    - ✗ Restaurants, shopping, or amenities
    - ✗ Future development plans
    - ✗ Community "feel" or culture
    - ✗ Unreported crimes or private security incidents
    - ✗ Crimes on UGA campus (separate jurisdiction)

    **Always Remember:**
    - This is for **research purposes only**
    - School zones can change - verify with the district
    - Crime patterns evolve - data is historical
    - Visit neighborhoods in person
    - Talk to local residents and realtors
    - Consider your specific needs and priorities

    ---

    ### 🎯 How the Safety Score Works

    The 1-100 safety score is calculated using a transparent algorithm:

    1. **Start at 100** (perfect score)
    2. **Crime Density Deduction** (0 to -50 points):
       - Based on crimes per month within 0.5 mile radius
       - More crimes = larger deduction
    3. **Violent Crime Percentage** (0 to -25 points):
       - Higher percentage of violent crimes = larger deduction
    4. **Trend Adjustment** (-15 to +5 points):
       - Crime decreasing = bonus points
       - Crime increasing = deduction
    5. **Final Score**: Clipped to range [1-100]

    **Score Ranges:**
    - 80-100: Very Safe (Green)
    - 60-79: Safe (Light Green)
    - 40-59: Moderate (Yellow/Orange)
    - 20-39: Concerning (Red)
    - 1-19: High Risk (Dark Red)

    This scale is designed for expansion to other U.S. cities with varying crime levels.

    ---

    ### 🤖 About the AI

    - **Model**: Claude 3 Haiku by Anthropic
    - **Purpose**: Synthesizes data from multiple sources and answers questions in plain English
    - **What it does**: Combines school performance data and crime statistics to provide contextual insights
    - **What it doesn't do**: Make up information, predict the future, or provide legal/financial advice
    - **Citations**: All AI responses reference specific data points and sources

    ---

    ### 📬 Contact & Feedback

    **This is a demo/research tool** built to showcase AI-powered neighborhood research capabilities.

    - **Not affiliated with**: Clarke County School District, Georgia Department of Education, or Athens-Clarke County Government
    - **Data accuracy**: We strive for accuracy but cannot guarantee completeness - always verify independently
    - **Questions about school zones**: Contact Clarke County Schools directly
    - **Questions about crime data**: Contact Athens-Clarke County Police Department
    - **Technical questions or feedback about this tool**: Submit issues at the project repository

    ---

    ### 🛡️ Privacy & Usage

    - **No data collection**: We do not store your queries or search history
    - **No personal information**: No login or personal data required
    - **Public data only**: All information comes from publicly available sources
    - **API usage**: Queries are sent to Anthropic's Claude API for analysis (see their privacy policy)

    **Ethical Use:**
    This tool should be used to help people make informed decisions about where to live. It should not be used to:
    - Discriminate against or stigmatize neighborhoods
    - Make decisions solely based on historical crime data without context
    - Replace professional advice (real estate, legal, financial)
    - Spread misinformation or unsupported claims

    ---

    **Last Updated**: November 2024 | **Geographic Coverage**: Athens-Clarke County, Georgia only
    """)

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

# Main input area - Single conversational text box
st.markdown("### 💬 Ask me about any Athens property")

user_query = st.text_area(
    "",
    placeholder="Example: Is 150 Hancock Avenue a good area for families with young kids?\n\nOr try: What are the schools like at 1398 W Hancock Ave, Athens, GA 30606?",
    height=100,
    label_visibility="collapsed",
    help="Type your question about any property in Athens. Include the street address in your question, and I'll analyze schools and safety data for you."
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
with st.expander("💡 Example Queries - Click to Copy"):
    st.markdown("""
    Just type naturally! Include the address in your question, and I'll figure out what you want to know.

    **Try these examples:**

    📍 **General Questions:**
    - `Is 150 Hancock Avenue a good area for families with young kids?`
    - `What are the pros and cons of living at 220 College Station Road, Athens, GA?`
    - `Tell me about 1398 W Hancock Avenue, Athens, GA 30606`

    🎓 **School-Focused:**
    - `What are the schools like at 1000 Jennings Mill Road?`
    - `How good are the test scores at 585 Reese Street, Athens, GA?`

    🛡️ **Safety-Focused:**
    - `How safe is the neighborhood around 195 Hoyt Street?`
    - `What's the crime situation at 150 Hancock Ave Athens GA?`

    💡 **Tip:** You can ask about any property address in Athens-Clarke County, Georgia!
    """)

# Process search
if search_button:
    if not user_query or not user_query.strip():
        st.warning("""
        ⚠️ **Please enter your question**

        **Example:**
        - Is 150 Hancock Avenue a good area for families with young kids?
        - What are the schools like at 1398 W Hancock Ave, Athens, GA 30606?
        - How safe is 220 College Station Road?
        """)
    elif not include_schools and not include_crime:
        st.warning("⚠️ **Please select at least one analysis type**\n\nCheck the box for:\n- 🎓 School Information (for school assignments and performance)\n- 🛡️ Crime & Safety Analysis (for crime statistics and trends)\n- Or both for a comprehensive analysis!")
    else:
        # Extract address and question from user query
        address_input, question_input = extract_address_from_query(user_query)

        if not address_input:
            st.error("""
            📍 **Couldn't find an address in your question**

            Please include a street address in Athens, GA. For example:
            - Is **150 Hancock Avenue** a good area for families?
            - What are the schools like at **1398 W Hancock Ave, Athens, GA 30606**?
            - How safe is **220 College Station Road**?

            Make sure to include a street number and street name!
            """)
        else:
            # Show what was extracted
            with st.expander("🔍 What I understood"):
                st.markdown(f"**Address:** {address_input}")
                st.markdown(f"**Question:** {question_input}")

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
                        error_msg = result['error']

                        # Provide helpful error messages based on error type
                        if "outside" in error_msg.lower() or "not in athens" in error_msg.lower():
                            st.error("""
                            🌍 **Address Outside Athens-Clarke County**

                            This tool currently only works for addresses within Athens-Clarke County, Georgia.

                            **What you can do:**
                            - Try a different address within Athens city limits
                            - Check if you spelled the street name correctly
                            - Make sure you're not searching in Watkinsville, Bogart, or other nearby towns

                            **Sample Athens addresses to try:**
                            - 150 Hancock Avenue, Athens, GA 30601 (downtown)
                            - 220 College Station Road, Athens, GA 30602 (suburban)
                            - 1000 Jennings Mill Road, Athens, GA 30606 (southeast)
                            """)
                        elif "not found" in error_msg.lower() or "geocod" in error_msg.lower():
                            st.error("""
                            📍 **Address Not Found**

                            We couldn't locate that address. This might happen if:
                            - The address has a typo or misspelling
                            - It's a very new address not yet in mapping databases
                            - The street name format is unusual

                            **What you can do:**
                            - Double-check the spelling of the street name
                            - Try using the full format: "123 Main Street, Athens, GA 30601"
                            - Verify the address exists on Google Maps first
                            - Try a nearby address on the same street
                            """)
                        elif "school" in error_msg.lower():
                            st.error(f"""
                            🎓 **School Data Issue**

                            {error_msg}

                            **What you can do:**
                            - The address might be outside Athens-Clarke County school district
                            - School zone data is from 2024-25 - new construction may not be included yet
                            - Try unchecking "School Information" and searching with just Crime/Safety data
                            - Contact Clarke County Schools directly at (706) 546-7721 for official zone information
                            """)
                        elif "crime" in error_msg.lower() or "api" in error_msg.lower():
                            st.error(f"""
                            🛡️ **Crime Data Issue**

                            {error_msg}

                            **What you can do:**
                            - The crime database might be temporarily unavailable
                            - Try again in a few moments
                            - Try unchecking "Crime & Safety Analysis" and searching with just School Information
                            - You can view the Athens crime map directly: [Athens-Clarke Crime Map](https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime)
                            """)
                        else:
                            st.error(f"""
                            ❌ **Something Went Wrong**

                            {error_msg}

                            **What you can do:**
                            - Check that your address is within Athens-Clarke County, GA
                            - Try a different address format
                            - Verify the address exists on Google Maps
                            - If the problem persists, try one of our demo addresses:
                              - 150 Hancock Avenue, Athens, GA 30601
                              - 220 College Station Road, Athens, GA 30602
                            """)

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
                            # Get colors in the same order as DataFrame columns
                            colors = get_category_colors()
                            color_list = [colors['Violent'], colors['Property'], colors['Traffic'], colors['Other']]
                            st.bar_chart(category_data, color=color_list)

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
                    error_str = str(e)
                    st.error(f"""
                    ❌ **Unexpected Error**

                    {error_str}

                    **What you can do:**
                    - Verify your address is in Athens-Clarke County, GA
                    - Try a simpler address format (e.g., "150 Hancock Avenue, Athens, GA")
                    - Check if the address exists on Google Maps
                    - Try selecting only one analysis type (Schools OR Crime)
                    - Test with a known working address: 150 Hancock Avenue, Athens, GA 30601

                    If the problem continues, this might be a temporary system issue. Try again in a few minutes.
                    """)

                    # Show technical details in expander for debugging
                    with st.expander("🔧 Technical Details (for debugging)"):
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
