"""
test_maritime_validator.py
The Good Neighbor Guard — Veracore Phase 6
Run with: python test_maritime_validator.py
"""

from maritime_validator import validate_maritime_claim, format_verdict_for_output

TESTS = [
    # Should be FALSE + cultural bias flag
    "The Titanic was the deadliest peacetime maritime disaster in history.",
    # Should be FALSE
    "The Titanic is the deadliest maritime disaster.",
    # Should be TRUE
    "MV Doña Paz was the deadliest peacetime maritime disaster.",
    # Should be FALSE
    "The Titanic caused the most deaths at sea in peacetime.",
    # Should NOT trigger (not a ranking claim)
    "The Titanic sank in 1912 after hitting an iceberg.",
    # Should be PARTIALLY_TRUE or FALSE
    "SS Joola was the worst peacetime sea disaster.",
]

if __name__ == "__main__":
    for claim in TESTS:
        print("=" * 70)
        print(f"CLAIM: {claim}")
        print()
        result = validate_maritime_claim(claim)
        if result is None:
            print("NOT A MARITIME RANKING CLAIM — skipped.")
        else:
            print(format_verdict_for_output(result))
        print()
