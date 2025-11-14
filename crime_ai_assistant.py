#!/usr/bin/env python3
"""
AI-powered crime information assistant using Claude API
Answers natural language questions about crime data for Athens-Clarke County addresses
"""

import os
from typing import Optional
from anthropic import Anthropic
from crime_analysis import analyze_crime_near_address, CrimeAnalysis


class CrimeAIAssistant:
    """AI assistant for answering questions about crime data"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the crime AI assistant

        Args:
            api_key: Anthropic API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it as an environment variable or pass it to the constructor."
            )
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"

    def _format_crime_data(self, analysis: CrimeAnalysis) -> str:
        """
        Format crime analysis into a clear text summary for Claude

        Args:
            analysis: CrimeAnalysis object

        Returns:
            Formatted string with all crime data
        """
        stats = analysis.statistics
        trends = analysis.trends
        safety = analysis.safety_score

        lines = []

        # Address and search parameters
        lines.append(f"ADDRESS: {analysis.address}")
        lines.append(f"Search Radius: {analysis.radius_miles} miles")
        lines.append(f"Time Period: {analysis.time_period_months} months")
        lines.append("")

        # Overall statistics
        lines.append("OVERALL STATISTICS:")
        lines.append(f"- Total Crimes: {stats.total_crimes}")
        lines.append(f"- Crimes per Month: {stats.crimes_per_month:.1f}")
        lines.append(f"- Most Common Crime: {stats.most_common_crime} ({stats.most_common_count} incidents)")
        lines.append("")

        # Crime categories
        lines.append("CRIME BREAKDOWN BY CATEGORY:")
        lines.append(f"- Violent Crimes: {stats.violent_count} ({stats.violent_percentage}% of total)")
        lines.append(f"  Examples: Assault, robbery, homicide, kidnapping, sexual assault")
        lines.append(f"- Property Crimes: {stats.property_count} ({stats.property_percentage}% of total)")
        lines.append(f"  Examples: Burglary, larceny, theft, vandalism, fraud, forgery")
        lines.append(f"- Traffic Offenses: {stats.traffic_count} ({stats.traffic_percentage}% of total)")
        lines.append(f"  Examples: DUI, driving violations")
        lines.append(f"- Other: {stats.other_count} ({stats.other_percentage}% of total)")
        lines.append(f"  Examples: Drug violations, liquor laws, disorderly conduct, trespassing")
        lines.append("")

        # Top crimes in each category
        lines.append("TOP CRIMES BY CATEGORY:")
        for category_name, category_label in [
            ('violent', 'VIOLENT CRIMES'),
            ('property', 'PROPERTY CRIMES'),
            ('traffic', 'TRAFFIC OFFENSES'),
            ('other', 'OTHER')
        ]:
            category_crimes = analysis.category_breakdown[category_name]
            if category_crimes:
                from collections import defaultdict
                crime_counts = defaultdict(int)
                for crime in category_crimes:
                    crime_counts[crime.crime_type] += 1

                lines.append(f"{category_label}:")
                top_crimes = sorted(crime_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                for crime_type, count in top_crimes:
                    lines.append(f"  - {crime_type}: {count}")
                lines.append("")

        # Trend analysis
        lines.append("CRIME TRENDS (Last 6 months vs. Previous 6 months):")
        lines.append(f"- Recent Period (last 6 months): {trends.recent_count} crimes")
        lines.append(f"- Previous Period (6-12 months ago): {trends.previous_count} crimes")
        lines.append(f"- Change: {trends.change_count:+d} crimes ({trends.change_percentage:+.1f}%)")
        lines.append(f"- Trend: {trends.trend_description}")
        lines.append("")

        # Safety score
        lines.append("SAFETY SCORE:")
        lines.append(f"- Score: {safety.score} out of 5 (5 = safest)")
        lines.append(f"- Level: {safety.level}")
        lines.append(f"- Explanation: {safety.explanation}")
        lines.append("")

        # Data sources and limitations
        lines.append("DATA SOURCES:")
        lines.append(f"- Source: Athens-Clarke County Police Department via ArcGIS REST API")
        lines.append(f"- Time Period: Last {analysis.time_period_months} months of reported crimes")
        lines.append(f"- Search Area: Within {analysis.radius_miles} miles of the address")
        lines.append("")

        lines.append("DATA LIMITATIONS:")
        lines.append("- Shows only REPORTED crimes that appear in public police data")
        lines.append("- Does not include all crimes (some may be unreported or excluded for privacy)")
        lines.append("- Crime locations may be approximate for privacy protection")
        lines.append("- Past crime data does not predict future crime")

        return "\n".join(lines)

    def answer_crime_question(self, address: str, question: str,
                             radius_miles: float = 0.5,
                             months_back: int = 12) -> str:
        """
        Answer a natural language question about crime near an address

        Args:
            address: Street address in Athens-Clarke County
            question: User's question about crime/safety
            radius_miles: Search radius in miles (default: 0.5)
            months_back: How many months of history (default: 12)

        Returns:
            Claude's natural language response

        Raises:
            ValueError: If address is invalid or API key is missing
            RuntimeError: If crime data cannot be retrieved
        """
        # Get crime analysis
        print(f"📊 Analyzing crime data for {address}...")
        analysis = analyze_crime_near_address(address, radius_miles, months_back)

        if not analysis:
            raise RuntimeError(
                f"Could not retrieve crime data for {address}. "
                "Please check the address is in Athens-Clarke County, GA."
            )

        # Format data for Claude
        crime_data = self._format_crime_data(analysis)

        # Create system prompt
        system_prompt = """You are a helpful and balanced real estate research assistant specializing in crime and safety information for Athens-Clarke County, Georgia.

CRITICAL INSTRUCTIONS FOR ACCURATE AND BALANCED RESPONSES:

1. ANSWER BASED ONLY ON PROVIDED DATA:
   - Use only the crime statistics provided below
   - Do NOT speculate or make up information
   - If the data doesn't answer the question, say so

2. ALWAYS CITE SPECIFIC STATISTICS:
   - Use exact numbers (e.g., "15 property crimes in the last 12 months")
   - Reference percentages (e.g., "17.2% of crimes were violent")
   - Quote the crime trend (e.g., "crime decreased by 37.7%")

3. BE BALANCED AND FACT-BASED:
   - Do NOT exaggerate danger or use fear-mongering language
   - Do NOT downplay legitimate concerns
   - Present facts objectively and let the user decide
   - Acknowledge both positive and negative aspects

4. NOTE DATA LIMITATIONS:
   - Always mention "based on the last X months of reported crimes"
   - Note that this shows only reported crimes, not all crimes
   - Remind users that past crime doesn't predict future crime
   - Suggest visiting the neighborhood in person

5. PROVIDE CONTEXT:
   - Compare violent vs. property crime percentages
   - Note crime trends (increasing, decreasing, stable)
   - Mention the safety score and what it means
   - Reference the most common crime types

6. IF ASKED FOR RECOMMENDATIONS:
   - Focus on facts, not opinions
   - Suggest additional research (visit neighborhood, talk to residents)
   - Mention that crime is just one factor in choosing a home
   - Recommend checking with Athens-Clarke County Police for more info

7. BE HELPFUL AND PROFESSIONAL:
   - Answer the specific question asked
   - Provide relevant details without overwhelming the user
   - Use clear, accessible language
   - Show empathy for home buyers' legitimate concerns"""

        # Create user prompt
        user_prompt = f"""Please answer this question about crime and safety for a property in Athens-Clarke County, Georgia.

QUESTION: {question}

CRIME DATA:
{crime_data}

Please provide a clear, balanced, fact-based answer that:
1. Cites specific statistics from the data above
2. Notes that this is based on the last {months_back} months of reported crimes
3. Acknowledges both positive and negative aspects
4. Helps the user make an informed decision

Remember: Be helpful, honest, and balanced. Don't exaggerate or minimize concerns."""

        # Call Claude API
        print(f"🤖 Asking Claude AI to analyze the question...")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            response = message.content[0].text
            return response

        except Exception as e:
            raise RuntimeError(f"Error calling Claude API: {str(e)}")


def main():
    """Test the crime AI assistant with sample questions"""

    # Test questions for 150 Hancock Avenue
    test_address = "150 Hancock Avenue, Athens, GA 30601"
    test_questions = [
        "How safe is this neighborhood?",
        "Should I be worried about crime here?",
        "What types of crimes happen near this address?",
        "Is crime getting better or worse?"
    ]

    print("=" * 80)
    print("CRIME AI ASSISTANT TEST")
    print("=" * 80)
    print(f"\nTesting with address: {test_address}")
    print(f"Using 0.5 mile radius, 12 months of data\n")

    # Initialize assistant
    try:
        assistant = CrimeAIAssistant()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease set your ANTHROPIC_API_KEY environment variable:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    # Test each question
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"QUESTION {i}: {question}")
        print(f"{'='*80}\n")

        try:
            answer = assistant.answer_crime_question(
                address=test_address,
                question=question,
                radius_miles=0.5,
                months_back=12
            )

            print("ANSWER:")
            print(answer)
            print()

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n")

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
