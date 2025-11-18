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
from zoning_lookup import get_zoning_info, get_nearby_zoning, ZoningInfo, NearbyZoning
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
        include_zoning: bool = True,
        radius_miles: float = 0.5,
        months_back: int = 12
    ) -> dict:
        """
        Get comprehensive analysis combining schools, crime, and zoning data

        Args:
            address: Street address in Athens-Clarke County
            question: User's question about the area
            include_schools: Whether to include school analysis
            include_crime: Whether to include crime analysis
            include_zoning: Whether to include zoning information
            radius_miles: Search radius for crime data (default: 0.5 miles)
            months_back: Crime history period in months (default: 12)

        Returns:
            Dictionary with school_info, crime_analysis, zoning_info, and synthesis
        """
        result = {
            'address': address,
            'school_info': None,
            'crime_analysis': None,
            'zoning_info': None,
            'nearby_zoning': None,
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

            # Get zoning data if requested
            if include_zoning:
                try:
                    # Use nearby zoning analysis for comprehensive insights
                    nearby_zoning = get_nearby_zoning(address, radius_meters=250)
                    if nearby_zoning and nearby_zoning.current_parcel:
                        # Store the basic zoning info for backward compatibility
                        result['zoning_info'] = nearby_zoning.current_parcel
                        # Also store the nearby analysis
                        result['nearby_zoning'] = nearby_zoning
                    else:
                        # Fallback to basic zoning if nearby analysis fails
                        result['zoning_info'] = get_zoning_info(address)
                except Exception as e:
                    # Zoning errors are non-critical
                    print(f"Zoning lookup error: {str(e)}")

            # Generate synthesis if we have data
            if result['school_info'] or result['crime_analysis'] or result['zoning_info']:
                synthesis = self._synthesize_insights(
                    address,
                    question,
                    result['school_info'],
                    result['crime_analysis'],
                    result['zoning_info'],
                    result.get('nearby_zoning')
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
        school_info: Optional[CompleteSchoolInfo],
        crime_analysis: Optional[CrimeAnalysis],
        zoning_info: Optional[ZoningInfo],
        nearby_zoning: Optional[NearbyZoning] = None
    ) -> str:
        """
        Synthesize insights across schools, crime, and zoning data

        Args:
            address: The address being analyzed
            question: User's original question
            school_info: School assignment and performance data (optional)
            crime_analysis: Crime statistics and safety analysis (optional)
            zoning_info: Zoning and land use information (optional)
            nearby_zoning: Nearby zoning analysis with concerns (optional)

        Returns:
            Synthesized response from Claude
        """
        # Format school data summary
        school_summary = ""
        if school_info:
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
        crime_summary = ""
        if crime_analysis:
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

        # Format zoning data summary
        zoning_summary = ""
        if zoning_info:
            zoning_summary = f"""
ZONING & LAND USE:

Current Zoning: {zoning_info.current_zoning}
- {zoning_info.current_zoning_description}

Future Land Use: {zoning_info.future_land_use}
- {zoning_info.future_land_use_description}

Property Size: {zoning_info.acres:.2f} acres ({int(zoning_info.acres * 43560)} square feet)
"""
            if zoning_info.split_zoned:
                zoning_summary += "\n⚠️  Property has split zoning\n"

            if zoning_info.future_changed:
                zoning_summary += "📝 Future land use plan has been updated/changed\n"

            # Add enhanced nearby zoning analysis if available
            if nearby_zoning:
                zoning_summary += f"""
NEIGHBORHOOD ZONING ANALYSIS (250m radius):
- Total nearby parcels: {nearby_zoning.total_nearby_parcels}
- Unique zoning types: {len(nearby_zoning.unique_zones)}
- Zone diversity score: {nearby_zoning.zone_diversity_score:.2f} (0.0=uniform, 1.0=highly diverse)
"""
                # Diversity interpretation
                if nearby_zoning.zone_diversity_score < 0.03:
                    zoning_summary += "  → Low diversity: Uniform, stable neighborhood character\n"
                elif nearby_zoning.zone_diversity_score < 0.06:
                    zoning_summary += "  → Moderate diversity: Mixed-use neighborhood\n"
                else:
                    zoning_summary += "  → High diversity: Transitional or evolving area\n"

                # Pattern flags
                if nearby_zoning.residential_only:
                    zoning_summary += "- Neighborhood character: Residential only\n"
                if nearby_zoning.commercial_nearby:
                    zoning_summary += "- Commercial/mixed-use parcels present nearby\n"
                if nearby_zoning.industrial_nearby:
                    zoning_summary += "- ⚠️  Industrial zoning nearby\n"

                # Concerns
                if nearby_zoning.potential_concerns:
                    zoning_summary += "\nPotential Zoning Concerns:\n"
                    for concern in nearby_zoning.potential_concerns:
                        zoning_summary += f"  • {concern}\n"
            elif zoning_info.nearby_zones:
                zoning_summary += f"\nNearby Zoning: {', '.join(zoning_info.nearby_zones)}\n"

        # Create synthesis prompt
        system_prompt = """You are a knowledgeable local real estate advisor having a conversation with a friend who's considering moving to this address. They trust your judgment and want your honest, thoughtful perspective."""

        user_prompt = f"""
Address: {address}
Their question: {question}

Available data:
{school_summary}

{crime_summary}

{zoning_summary}

Please provide a warm, conversational analysis in this structure:

THE BOTTOM LINE UP FRONT
[2-3 paragraphs giving your honest take. Start with a clear answer to their question. What's your gut feeling about this place for them? What are the most important tradeoffs? Be direct but friendly.]

WHAT I LOVE ABOUT THIS AREA
[3-5 paragraphs exploring the genuine strengths. Use specific data points but tell stories. Help them visualize living here. What would make someone happy here?]

WHAT GIVES ME PAUSE
[2-4 paragraphs about legitimate concerns. Be honest about downsides. Use data to back up concerns but explain what they mean in real life. No sugar-coating, but no fear-mongering either.]

THE SCHOOLS STORY
[2-3 paragraphs about the educational picture. Don't just cite CCRPI scores - explain what the numbers mean for their kids' actual experience. Talk about the school communities, diversity, resources, trajectory.]

THE SAFETY PICTURE
[2-3 paragraphs putting crime data in context. A college area with bar fights is different from random violence. Explain what the numbers actually mean for daily life. Compare to Athens overall.]

THE ZONING SITUATION
[1-2 paragraphs about what the zoning tells us. Will the neighborhood stay residential? Any future development concerns? What does the zoning pattern say about neighborhood character?]

WHO THRIVES HERE
[1-2 paragraphs describing the type of person/family who would genuinely love this location. Be specific about lifestyle, priorities, personality.]

WHO MIGHT STRUGGLE HERE
[1-2 paragraphs about who this ISN'T right for. What type of person would be unhappy? What dealbreakers exist?]

BEFORE YOU DECIDE
Here's what I'd encourage you to do:
- [5-7 specific, actionable investigation steps]
- [Include visiting times, people to talk to, things to observe]
- [Suggest nearby alternatives if this isn't quite right]

MY HONEST RECOMMENDATION
[2-3 paragraphs with your final take. Given what they're looking for, is this the right move? What would you do if you were in their shoes? End with a clear yes, no, or "it depends on..." with specific conditions.]

Tone guidelines:
- Write like you're talking to a friend over coffee, not writing a formal report
- Use "you" and "your" - make it personal
- Be specific with numbers but explain what they mean in human terms
- Show nuance - few places are all good or all bad
- Share insights, not just data recitation
- Be honest about both positives and concerns
- Use conversational phrases: "Here's what strikes me...", "What gives me pause is...", "Here's the thing..."
- Occasional parentheticals for extra context (like this!)
- Help them make a wise decision, not just gather information

Base everything on the data provided. When you reference specific numbers, cite them. But interpret the data - don't just report it.
"""

        # Call Claude API
        import anthropic

        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
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
- Zoning Data: Athens-Clarke County Planning Department GIS
- This analysis is for informational purposes only. Always verify independently and visit the neighborhood in person.
- For zoning questions, contact ACC Planning Department at (706) 613-3515
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
