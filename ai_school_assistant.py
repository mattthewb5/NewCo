#!/usr/bin/env python3
"""
AI-Powered School Information Assistant
Uses Claude API to answer natural language questions about school data
"""

import os
from typing import Optional
from anthropic import Anthropic
from school_info import get_school_info, CompleteSchoolInfo


class SchoolAIAssistant:
    """AI assistant for answering questions about school data"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI assistant

        Args:
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')

        if not self.api_key:
            raise ValueError(
                "API key required. Either pass api_key parameter or set ANTHROPIC_API_KEY environment variable.\n"
                "Get your API key at: https://console.anthropic.com/"
            )

        self.client = Anthropic(api_key=self.api_key)

    def _format_school_data(self, info: CompleteSchoolInfo) -> str:
        """Format school information into a readable text for Claude"""
        lines = []

        lines.append(f"ADDRESS: {info.address}")
        lines.append("")
        lines.append("SCHOOL ASSIGNMENTS:")
        lines.append(f"- Elementary: {info.elementary}")
        lines.append(f"- Middle: {info.middle}")
        lines.append(f"- High: {info.high}")

        if info.street_matched:
            lines.append(f"\nMatched street: {info.street_matched}")
            if info.parameters_matched:
                lines.append(f"Parameters: {info.parameters_matched}")

        # Add performance data for each school
        if info.elementary_performance:
            lines.append(f"\n{info.elementary.upper()} - PERFORMANCE DATA:")
            perf = info.elementary_performance

            if perf.test_scores:
                lines.append("  Test Scores (Georgia Milestones):")
                for score in perf.test_scores:
                    lines.append(f"    - {score.subject}: {score.total_proficient_pct:.1f}% proficient or above ({score.num_tested} students tested)")

            if perf.demographics:
                d = perf.demographics
                lines.append(f"  Demographics:")
                if d.total_enrollment:
                    lines.append(f"    - Total Enrollment: {d.total_enrollment}")
                lines.append(f"    - Economically Disadvantaged: {d.pct_economically_disadvantaged:.1f}%")
                lines.append(f"    - English Learners: {d.pct_english_learners:.1f}%")
                lines.append(f"    - Students with Disabilities: {d.pct_students_with_disabilities:.1f}%")
                lines.append(f"    - Racial Composition:")
                lines.append(f"      White: {d.pct_white:.1f}%, Black: {d.pct_black:.1f}%, Hispanic: {d.pct_hispanic:.1f}%, Asian: {d.pct_asian:.1f}%")

            if perf.achievements:
                lines.append(f"  Notable Achievements:")
                for achievement in perf.achievements:
                    lines.append(f"    - {achievement}")

            if perf.concerns:
                lines.append(f"  Areas for Improvement:")
                for concern in perf.concerns:
                    lines.append(f"    - {concern}")

        if info.middle_performance:
            lines.append(f"\n{info.middle.upper()} - PERFORMANCE DATA:")
            perf = info.middle_performance

            if perf.test_scores:
                lines.append("  Test Scores (Georgia Milestones):")
                for score in perf.test_scores:
                    lines.append(f"    - {score.subject}: {score.total_proficient_pct:.1f}% proficient or above ({score.num_tested} students tested)")

            if perf.demographics:
                d = perf.demographics
                lines.append(f"  Demographics:")
                lines.append(f"    - Economically Disadvantaged: {d.pct_economically_disadvantaged:.1f}%")

        if info.high_performance:
            lines.append(f"\n{info.high.upper()} - PERFORMANCE DATA:")
            perf = info.high_performance

            if perf.test_scores:
                lines.append("  Test Scores (Georgia Milestones End-of-Course):")
                for score in perf.test_scores:
                    lines.append(f"    - {score.subject}: {score.total_proficient_pct:.1f}% proficient or above ({score.num_tested} students tested)")

            if perf.graduation_rate:
                lines.append(f"  Graduation Rate: {perf.graduation_rate:.1f}%")

            if perf.avg_sat_score and perf.avg_sat_score > 0:
                lines.append(f"  Average SAT Score: {perf.avg_sat_score}")

            if perf.demographics:
                d = perf.demographics
                lines.append(f"  Demographics:")
                lines.append(f"    - Economically Disadvantaged: {d.pct_economically_disadvantaged:.1f}%")

        return "\n".join(lines)

    def ask_claude_about_schools(self, address: str, question: str) -> str:
        """
        Ask Claude a natural language question about schools at an address

        Args:
            address: Full address (e.g., "150 Hancock Avenue, Athens, GA 30601")
            question: Natural language question (e.g., "How good are the schools?")

        Returns:
            Claude's natural language response

        Raises:
            ValueError: If address not found or API error
        """
        # Get school information
        print(f"🔍 Looking up school data for: {address}")
        info = get_school_info(address)

        if not info:
            return f"I couldn't find school information for the address '{address}'. This address may not be in Athens-Clarke County, GA, or the street name may not be recognized. Please verify the address and try again."

        # Format the data
        school_data = self._format_school_data(info)

        # Create prompt for Claude
        system_prompt = """You are a helpful school information assistant for Athens-Clarke County, Georgia. You provide clear, honest, and balanced answers about school assignments and performance data.

When analyzing school performance:
- Be objective and data-driven
- Provide context (e.g., compare to averages when relevant)
- Consider multiple factors: test scores, demographics, graduation rates, etc.
- Be honest about both strengths and challenges
- Remember that school quality involves many factors beyond test scores
- Encourage parents to visit schools and verify information with the district

Data is from the 2023-24 school year (test scores, demographics) and official Clarke County Schools street index."""

        user_prompt = f"""Here is the school information for an address in Athens-Clarke County:

{school_data}

User's question: {question}

Please provide a helpful, balanced answer based on the data above. Be specific and reference the actual numbers when relevant."""

        # Call Claude API
        try:
            print("🤖 Asking Claude AI...")
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response = message.content[0].text
            return response

        except Exception as e:
            raise ValueError(f"Error calling Claude API: {str(e)}")


def ask_claude_about_schools(address: str, question: str, api_key: Optional[str] = None) -> str:
    """
    Convenience function to ask Claude about schools (creates assistant instance)

    Args:
        address: Full address
        question: Natural language question
        api_key: Optional API key (uses ANTHROPIC_API_KEY env var if not provided)

    Returns:
        Claude's response
    """
    assistant = SchoolAIAssistant(api_key=api_key)
    return assistant.ask_claude_about_schools(address, question)


if __name__ == "__main__":
    import sys

    # Test examples
    test_cases = [
        ("150 Hancock Avenue, Athens, GA 30601", "What are the test scores at this address?"),
        ("585 Reese Street, Athens, GA 30601", "Are the schools good near this address?"),
        ("195 Hoyt Street, Athens, GA 30601", "Tell me about school quality for this address"),
    ]

    # Check if API key is available
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("=" * 80)
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("=" * 80)
        print("\nTo use this feature, you need an Anthropic API key.")
        print("\n1. Get your API key at: https://console.anthropic.com/")
        print("2. Set it as an environment variable:")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nOr pass it directly:")
        print("   python3 ai_school_assistant.py")
        print()
        sys.exit(1)

    print("=" * 80)
    print("AI SCHOOL ASSISTANT - TEST SUITE")
    print("=" * 80)
    print()

    for i, (address, question) in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/3")
        print(f"{'=' * 80}")
        print(f"\n📍 Address: {address}")
        print(f"❓ Question: {question}")
        print()

        try:
            response = ask_claude_about_schools(address, question)
            print("🤖 Claude's Response:")
            print("-" * 80)
            print(response)
            print()
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

    print("=" * 80)
    print("All tests complete!")
    print("=" * 80)
