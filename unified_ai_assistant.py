#!/usr/bin/env python3
"""
Unified AI Assistant for Athens Home Buyer Research
Combines school and crime analysis for comprehensive neighborhood insights
"""

import os
from typing import Optional
from datetime import datetime
from school_info import get_school_info, CompleteSchoolInfo
from crime_analysis import analyze_crime_near_address, CrimeAnalysis
from ai_school_assistant import SchoolAIAssistant
from crime_ai_assistant import CrimeAIAssistant


class UnifiedAIAssistant:
    """
    Unified assistant that provides comprehensive neighborhood analysis
    combining schools, crime, and synthesized insights
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize unified assistant

        Args:
            api_key: Anthropic API key (will use ANTHROPIC_API_KEY env var if not provided)
        """
        if api_key is None:
            api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set environment variable.")

        self.api_key = api_key
        self.school_assistant = SchoolAIAssistant(api_key=api_key)
        self.crime_assistant = CrimeAIAssistant(api_key=api_key)

    def get_comprehensive_analysis(
        self,
        address: str,
        question: str,
        include_schools: bool = True,
        include_crime: bool = True,
        radius_miles: float = 0.5,
        months_back: int = 12
    ) -> dict:
        """
        Get comprehensive analysis combining schools and crime data

        Args:
            address: Street address in Athens-Clarke County
            question: User's question about the area
            include_schools: Whether to include school analysis
            include_crime: Whether to include crime analysis
            radius_miles: Search radius for crime data (default: 0.5 miles)
            months_back: Crime history period in months (default: 12)

        Returns:
            Dictionary with school_info, crime_analysis, and synthesis
        """
        result = {
            'address': address,
            'school_info': None,
            'crime_analysis': None,
            'school_response': None,
            'crime_response': None,
            'synthesis': None,
            'error': None
        }

        try:
            # Get school data if requested
            if include_schools:
                try:
                    school_info = get_school_info(address)
                    result['school_info'] = school_info

                    if school_info:
                        school_response = self.school_assistant.ask_claude_about_schools(
                            address, question
                        )
                        result['school_response'] = school_response
                except Exception as e:
                    result['error'] = f"School lookup error: {str(e)}"

            # Get crime data if requested
            if include_crime:
                try:
                    crime_analysis = analyze_crime_near_address(
                        address,
                        radius_miles=radius_miles,
                        months_back=months_back
                    )
                    result['crime_analysis'] = crime_analysis

                    if crime_analysis:
                        crime_response = self.crime_assistant.answer_crime_question(
                            address, question, radius_miles=radius_miles, months_back=months_back
                        )
                        result['crime_response'] = crime_response
                except Exception as e:
                    # Crime errors are less critical - address might not geocode
                    result['error'] = f"Crime analysis error: {str(e)}"

            # Generate synthesis if we have both types of data
            if include_schools and include_crime and result['school_info'] and result['crime_analysis']:
                synthesis = self._synthesize_insights(
                    address, question, result['school_info'], result['crime_analysis']
                )
                result['synthesis'] = synthesis

            return result

        except Exception as e:
            result['error'] = f"Analysis error: {str(e)}"
            return result

    def _synthesize_insights(
        self,
        address: str,
        question: str,
        school_info: CompleteSchoolInfo,
        crime_analysis: CrimeAnalysis
    ) -> str:
        """
        Synthesize insights across schools and crime data

        Args:
            address: The address being analyzed
            question: User's original question
            school_info: School assignment and performance data
            crime_analysis: Crime statistics and safety analysis

        Returns:
            Synthesized response from Claude
        """
        # Format school data summary
        school_summary = f"""
SCHOOL ASSIGNMENTS:
- Elementary: {school_info.elementary}
- Middle: {school_info.middle}
- High: {school_info.high}

SCHOOL PERFORMANCE (where available):
"""
        if school_info.elementary_data:
            elem = school_info.elementary_data
            school_summary += f"""
Elementary School ({school_info.elementary}):
- CCRPI Score: {elem.ccrpi_score}/100
- Content Mastery: {elem.content_mastery_score}/100
- Literacy: {getattr(elem, 'literacy', 'N/A')}%
- Math: {getattr(elem, 'math', 'N/A')}%
"""

        if school_info.middle_data:
            mid = school_info.middle_data
            school_summary += f"""
Middle School ({school_info.middle}):
- CCRPI Score: {mid.ccrpi_score}/100
- Content Mastery: {mid.content_mastery_score}/100
- Literacy: {getattr(mid, 'literacy', 'N/A')}%
- Math: {getattr(mid, 'math', 'N/A')}%
"""

        if school_info.high_data:
            high = school_info.high_data
            school_summary += f"""
High School ({school_info.high}):
- CCRPI Score: {high.ccrpi_score}/100
- Graduation Rate: {high.graduation_rate}%
- Content Mastery: {high.content_mastery_score}/100
"""

        # Format crime data summary
        crime_summary = f"""
CRIME & SAFETY ANALYSIS (last {crime_analysis.time_period_months} months, {crime_analysis.radius_miles} mile radius):

Safety Score: {crime_analysis.safety_score.score}/100 ({crime_analysis.safety_score.level})

Crime Statistics:
- Total Crimes: {crime_analysis.statistics.total_crimes}
- Crimes per Month: {crime_analysis.statistics.crimes_per_month:.1f}
- Violent Crimes: {crime_analysis.statistics.violent_count} ({crime_analysis.statistics.violent_percentage:.1f}%)
- Property Crimes: {crime_analysis.statistics.property_count} ({crime_analysis.statistics.property_percentage:.1f}%)

Crime Trends:
- Recent (last 6 months): {crime_analysis.trends.recent_count} crimes
- Previous (6-12 months ago): {crime_analysis.trends.previous_count} crimes
- Trend: {crime_analysis.trends.trend_description}
"""

        if crime_analysis.comparison:
            comp = crime_analysis.comparison
            crime_summary += f"""
Comparison to Athens Average:
- This Area: {comp.area_crime_count} crimes
- Athens Average: {comp.athens_average:.0f} crimes
- {comp.comparison_text}
- Assessment: {comp.relative_ranking}
"""

        # Create synthesis prompt
        system_prompt = """You are an expert real estate analyst specializing in comprehensive neighborhood assessment.
You help home buyers make informed decisions by synthesizing information about schools and crime/safety.

Your task is to provide a balanced, honest assessment that considers both schools and safety together.
Be direct about pros and cons. Don't sugarcoat issues but also don't exaggerate concerns."""

        user_prompt = f"""Based on the data below, please answer this question about the property:

QUESTION: {question}

ADDRESS: {address}

{school_summary}

{crime_summary}

Please provide a comprehensive response that:

1. DIRECTLY ANSWERS THE QUESTION with a clear summary (2-3 sentences)
   - Synthesize both school quality AND safety
   - Be honest about tradeoffs if they exist

2. KEY INSIGHTS (bullet points)
   - School strengths/weaknesses
   - Safety strengths/concerns
   - Overall suitability for the user's needs

3. IMPORTANT CONSIDERATIONS
   - Any red flags or major concerns
   - Notable advantages
   - Context for the user to understand

4. RECOMMENDATION
   - Clear guidance based on the data
   - Suggestions for what to investigate further
   - Whether this area aligns with their apparent priorities

Be balanced, factual, and helpful. Use specific data points from both school and crime analyses.
"""

        # Call Claude API
        import anthropic

        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response = message.content[0].text

            # Add data source footer
            today = datetime.now().strftime('%Y-%m-%d')
            footer = f"""

---

**Data Sources & Verification:**
- School Data: Clarke County Schools (2024-25) & Georgia GOSA (2023-24)
- Crime Data: Athens-Clarke County Police Department (current as of {today})
- This analysis is for informational purposes only. Always verify independently and visit the neighborhood in person.
"""

            return response + footer

        except Exception as e:
            return f"Error generating synthesis: {str(e)}"


def main():
    """Test unified assistant"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python unified_ai_assistant.py <address> [question]")
        print('Example: python unified_ai_assistant.py "150 Hancock Avenue, Athens, GA" "Is this good for families?"')
        sys.exit(1)

    address = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "Is this a good neighborhood?"

    print("=" * 80)
    print("UNIFIED AI ASSISTANT TEST")
    print("=" * 80)
    print(f"Address: {address}")
    print(f"Question: {question}")
    print()

    assistant = UnifiedAIAssistant()

    result = assistant.get_comprehensive_analysis(
        address=address,
        question=question,
        include_schools=True,
        include_crime=True
    )

    if result['error']:
        print(f"❌ Error: {result['error']}")

    if result['synthesis']:
        print("\n" + "=" * 80)
        print("COMPREHENSIVE ANALYSIS")
        print("=" * 80)
        print(result['synthesis'])


if __name__ == "__main__":
    main()
