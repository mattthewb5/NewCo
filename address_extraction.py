#!/usr/bin/env python3
"""
Extract address from natural language queries
"""

import re
from typing import Optional, Tuple


def extract_address_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract address and question from a natural language query

    Examples:
        "Is 150 Hancock Ave a good area for families?"
        -> address: "150 Hancock Ave", question: "Is this a good area for families?"

        "What are the schools like at 1398 W Hancock Avenue, Athens, GA 30606?"
        -> address: "1398 W Hancock Avenue, Athens, GA 30606", question: "What are the schools like?"

    Args:
        query: User's natural language input

    Returns:
        Tuple of (address, question) or (None, None) if no address found
    """
    if not query or not query.strip():
        return (None, None)

    query = query.strip()

    # Common patterns for addresses in Athens
    # Pattern 1: Number + Street Name + optional suffix + optional city/state/zip
    # e.g., "150 Hancock Ave", "1398 W Hancock Avenue, Athens, GA 30606"
    address_patterns = [
        # Full address with city, state, zip
        r'(\d+\s+[NSEW]?\s*[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl)\s*[NSEW]?\s*,?\s*(?:Athens|athens)\s*,?\s*(?:GA|Georgia|ga)\s*\d{5})',

        # Address with city but no zip
        r'(\d+\s+[NSEW]?\s*[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl)\s*[NSEW]?\s*,?\s*(?:Athens|athens))',

        # Just street address, no city
        r'(\d+\s+[NSEW]?\s*[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl)\s*[NSEW]?)',

        # Simpler pattern - number + words ending in common suffix
        r'(\d+\s+[A-Za-z\s]+(?:Avenue|Ave|Street|St|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Boulevard|Blvd))',
    ]

    extracted_address = None

    for pattern in address_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            extracted_address = match.group(1).strip()
            # Clean up the address
            extracted_address = re.sub(r'\s+', ' ', extracted_address)  # Remove extra spaces
            break

    if not extracted_address:
        return (None, None)

    # Extract the question by removing the address
    question = query.replace(extracted_address, 'this address').strip()

    # Clean up question
    question = re.sub(r'^[,\.\?!\s]+', '', question)  # Remove leading punctuation
    question = re.sub(r'[,\.\?!\s]+$', '', question)  # Remove trailing punctuation

    # Clean up common artifacts
    question = re.sub(r'\s+at\s+this address\b', ' at this address', question, flags=re.IGNORECASE)
    question = re.sub(r'\bat\s+this address\b', 'for this address', question, flags=re.IGNORECASE)
    question = re.sub(r'\bfor\s+this address\b', 'for this address', question, flags=re.IGNORECASE)

    # If question is empty or too short, provide default
    if not question or len(question) < 5:
        question = "Tell me about this area"

    # Ensure question ends with ?
    if not question.endswith('?'):
        question += '?'

    return (extracted_address, question)


def test_extraction():
    """Test the extraction function"""
    test_cases = [
        "Is 150 Hancock Ave a good area for families?",
        "What are the schools like at 1398 W Hancock Avenue, Athens, GA 30606?",
        "How safe is 220 College Station Road",
        "1000 Jennings Mill Road - is this good for kids?",
        "Tell me about crime at 585 Reese Street, Athens, GA",
        "150 Hancock Avenue Athens GA 30601",
        "Is 1398 Hancock Avenue W, Athens, GA 30606 a good neighborhood?",
    ]

    print("=" * 80)
    print("ADDRESS EXTRACTION TEST")
    print("=" * 80)
    print()

    for test in test_cases:
        address, question = extract_address_from_query(test)
        print(f"Input:    {test}")
        print(f"Address:  {address}")
        print(f"Question: {question}")
        print("-" * 80)
        print()


if __name__ == "__main__":
    test_extraction()
