"""
maritime_validator.py
The Good Neighbor Guard — Veracore Phase 6
Maritime disaster ranking claim validator.

Integrates with: Claim Parser, Retrieval Engine, Adversarial Challenger, Consensus Engine.
Never hard-codes final verdicts — always verifies against retrieval artifacts.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference seed data
# These are SEED values only — not final authority.
# The engine must verify against retrieval artifacts before issuing verdicts.
# ---------------------------------------------------------------------------
SEED_MARITIME_DISASTERS = [
    {
        "name": "MV Doña Paz",
        "year": 1987,
        "estimated_deaths": 4386,
        "context": "peacetime",
        "notes": "Ferry collision in Philippines. Deadliest known peacetime maritime disaster.",
    },
    {
        "name": "SS Joola",
        "year": 2002,
        "estimated_deaths": 1863,
        "context": "peacetime",
        "notes": "Senegalese ferry capsize.",
    },
    {
        "name": "RMS Titanic",
        "year": 1912,
        "estimated_deaths": 1517,
        "context": "peacetime",
        "notes": "North Atlantic sinking. High cultural prominence.",
    },
    {
        "name": "MV Le Joola",
        "year": 2002,
        "estimated_deaths": 1863,
        "context": "peacetime",
        "notes": "Same as SS Joola — alternate name.",
    },
    {
        "name": "MV Wilhelm Gustloff",
        "year": 1945,
        "estimated_deaths": 9400,
        "context": "wartime",
        "notes": "Wartime evacuation sinking. Excluded from peacetime ranking.",
    },
    {
        "name": "MV Goya",
        "year": 1945,
        "estimated_deaths": 7000,
        "context": "wartime",
        "notes": "Wartime sinking. Excluded from peacetime ranking.",
    },
]

# Ships with high cultural prominence relative to their casualty ranking.
# Presence here triggers H-FLAG: CULTURAL_PROMINENCE_BIAS check.
HIGH_PROMINENCE_SHIPS = {
    "titanic", "rms titanic",
}

# Claim patterns that trigger maritime disaster ranking validation.
CLAIM_PATTERNS = [
    re.compile(
        r"(.+?)\s+(?:is|was|remains?)\s+(?:the\s+)?deadliest\s+(?:peacetime\s+)?maritime\s+disaster",
        re.IGNORECASE,
    ),
    re.compile(
        r"(.+?)\s+(?:caused|resulted in)\s+(?:the\s+)?most\s+(?:maritime\s+)?deaths\s+(?:in\s+peacetime)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(.+?)\s+(?:is|was)\s+(?:the\s+)?worst\s+(?:peacetime\s+)?(?:maritime|sea|naval)\s+(?:disaster|tragedy|accident)",
        re.IGNORECASE,
    ),
    re.compile(
        r"no\s+(?:maritime\s+)?(?:disaster|shipwreck|sinking)\s+(?:has\s+)?(?:killed|claimed)\s+more\s+(?:lives|people)\s+than\s+(.+?)(?:\s|$|\.)",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParsedMaritimeClaim:
    raw_claim: str
    ship_name: str
    claim_category: str = "maritime_disaster_ranking"
    cultural_prominence_flag: bool = False
    context_filter: str = "peacetime"   # peacetime | any


@dataclass
class DisasterRecord:
    name: str
    year: int
    estimated_deaths: int
    context: str
    notes: str
    source: str = "seed_data"           # updated to "retrieval" when verified


@dataclass
class MaritimeVerdict:
    verdict: str                        # TRUE | FALSE | PARTIALLY_TRUE | UNVERIFIABLE
    confidence: float                   # 0.0 – 1.0
    claimed_ship: str
    claimed_ship_deaths: Optional[int]
    top_ranked_ship: str
    top_ranked_deaths: int
    flags: list[str]
    comparison_table: list[dict]
    explanation: str
    retrieval_verified: bool = False


# ---------------------------------------------------------------------------
# Claim Parser
# ---------------------------------------------------------------------------

def parse_maritime_claim(claim_text: str) -> Optional[ParsedMaritimeClaim]:
    """
    Detect whether a claim makes a maritime disaster ranking assertion.
    Returns ParsedMaritimeClaim if detected, None otherwise.
    """
    for pattern in CLAIM_PATTERNS:
        match = pattern.search(claim_text)
        if match:
            ship_name = match.group(1).strip().rstrip(".,;")
            cultural_flag = ship_name.lower() in HIGH_PROMINENCE_SHIPS
            return ParsedMaritimeClaim(
                raw_claim=claim_text,
                ship_name=ship_name,
                cultural_prominence_flag=cultural_flag,
            )
    return None


# ---------------------------------------------------------------------------
# Ranking Engine
# ---------------------------------------------------------------------------

def rank_disasters(
    records: list[DisasterRecord],
    context_filter: str = "peacetime",
) -> list[DisasterRecord]:
    """
    Filter by context and rank by estimated deaths descending.
    Deduplicates by normalized name.
    """
    if context_filter == "peacetime":
        filtered = [r for r in records if r.context == "peacetime"]
    else:
        filtered = records

    # Deduplicate — keep higher death count for same ship
    seen: dict[str, DisasterRecord] = {}
    for r in filtered:
        key = r.name.lower().strip()
        if key not in seen or r.estimated_deaths > seen[key].estimated_deaths:
            seen[key] = r

    return sorted(seen.values(), key=lambda x: x.estimated_deaths, reverse=True)


def find_ship_record(
    ship_name: str,
    records: list[DisasterRecord],
) -> Optional[DisasterRecord]:
    """
    Find a disaster record by ship name (fuzzy: substring match, case-insensitive).
    """
    normalized = ship_name.lower().strip()
    for r in records:
        if normalized in r.name.lower() or r.name.lower() in normalized:
            return r
    return None


# ---------------------------------------------------------------------------
# Cultural Bias Detector
# ---------------------------------------------------------------------------

def detect_cultural_bias(
    claimed_ship: str,
    ranked: list[DisasterRecord],
) -> tuple[bool, float]:
    """
    Returns (bias_detected, confidence_penalty).
    If the claimed ship has high cultural prominence but does not rank #1,
    flag CULTURAL_PROMINENCE_BIAS and apply a confidence penalty.
    """
    normalized = claimed_ship.lower().strip()
    if normalized not in HIGH_PROMINENCE_SHIPS:
        return False, 0.0

    if not ranked:
        return False, 0.0

    top = ranked[0]
    if normalized not in top.name.lower():
        # Claimed ship is prominent but not #1 — bias flag applies
        return True, 0.20

    return False, 0.0


# ---------------------------------------------------------------------------
# Verdict Builder
# ---------------------------------------------------------------------------

def build_verdict(
    parsed: ParsedMaritimeClaim,
    retrieval_records: Optional[list[DisasterRecord]] = None,
) -> MaritimeVerdict:
    """
    Build a full verdict for a maritime ranking claim.

    If retrieval_records is provided, they are merged with seed data and
    marked as retrieval-verified. Otherwise seed data is used with a
    retrieval_verified=False flag.
    """
    flags: list[str] = []
    retrieval_verified = False

    # Merge seed + retrieval records
    all_records = [DisasterRecord(**d) for d in SEED_MARITIME_DISASTERS]

    if retrieval_records:
        for r in retrieval_records:
            r.source = "retrieval"
        all_records.extend(retrieval_records)
        retrieval_verified = True

    # Rank
    ranked = rank_disasters(all_records, parsed.context_filter)

    if not ranked:
        return MaritimeVerdict(
            verdict="UNVERIFIABLE",
            confidence=0.0,
            claimed_ship=parsed.ship_name,
            claimed_ship_deaths=None,
            top_ranked_ship="Unknown",
            top_ranked_deaths=0,
            flags=["NO_DATA"],
            comparison_table=[],
            explanation="No casualty data available to evaluate this claim.",
            retrieval_verified=False,
        )

    top = ranked[0]
    claimed_record = find_ship_record(parsed.ship_name, ranked)
    claimed_deaths = claimed_record.estimated_deaths if claimed_record else None

    # Cultural bias check
    bias_detected, confidence_penalty = detect_cultural_bias(parsed.ship_name, ranked)
    if bias_detected:
        flags.append("H-FLAG: CULTURAL_PROMINENCE_BIAS")

    if not retrieval_verified:
        flags.append("WARN: SEED_DATA_ONLY — retrieval verification recommended")

    # Determine verdict
    claimed_is_top = (
        claimed_record is not None
        and claimed_record.name.lower() == top.name.lower()
    )

    if claimed_record is None:
        verdict = "UNVERIFIABLE"
        confidence = 0.3
        explanation = (
            f"The claim references '{parsed.ship_name}', but no casualty data "
            f"was found for this vessel in the verified comparison set. "
            f"Cannot confirm or deny the ranking claim without retrieval data."
        )
    elif claimed_is_top:
        verdict = "TRUE"
        confidence = max(0.5, 0.95 - confidence_penalty)
        explanation = (
            f"The {parsed.ship_name} ({claimed_record.year}) with approximately "
            f"{claimed_deaths:,} estimated deaths ranks #1 in the verified "
            f"comparison set for {parsed.context_filter} maritime disasters. "
            f"The claim is supported by available data."
        )
    else:
        # Check if close (within 10%)
        if claimed_deaths and abs(claimed_deaths - top.estimated_deaths) / top.estimated_deaths < 0.10:
            verdict = "PARTIALLY_TRUE"
            confidence = max(0.3, 0.55 - confidence_penalty)
        else:
            verdict = "FALSE"
            confidence = max(0.2, 0.85 - confidence_penalty)

        explanation = (
            f"Although the {parsed.ship_name} ({claimed_record.year if claimed_record else 'unknown'}) "
            f"killed approximately {claimed_deaths:,} people, it is not the deadliest "
            f"{parsed.context_filter} maritime disaster. "
            f"The {top.name} ({top.year}) disaster killed an estimated {top.estimated_deaths:,} people, "
            f"making it the deadliest known {parsed.context_filter} maritime disaster "
            f"in the verified comparison set."
        )

    # Build comparison table (top 5 peacetime)
    comparison_table = [
        {
            "rank":             i + 1,
            "ship":             r.name,
            "year":             r.year,
            "estimated_deaths": r.estimated_deaths,
            "context":          r.context,
            "source":           r.source,
        }
        for i, r in enumerate(ranked[:5])
    ]

    return MaritimeVerdict(
        verdict=verdict,
        confidence=round(confidence, 2),
        claimed_ship=parsed.ship_name,
        claimed_ship_deaths=claimed_deaths,
        top_ranked_ship=top.name,
        top_ranked_deaths=top.estimated_deaths,
        flags=flags,
        comparison_table=comparison_table,
        explanation=explanation,
        retrieval_verified=retrieval_verified,
    )


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def validate_maritime_claim(
    claim_text: str,
    retrieval_records: Optional[list[DisasterRecord]] = None,
) -> Optional[dict]:
    """
    Full pipeline:
    1. Parse claim
    2. Detect cultural bias
    3. Rank disasters
    4. Build verdict

    Returns structured verdict dict, or None if claim is not a maritime ranking claim.
    """
    parsed = parse_maritime_claim(claim_text)
    if parsed is None:
        return None

    verdict = build_verdict(parsed, retrieval_records)

    return {
        "claim_category":       parsed.claim_category,
        "claimed_ship":         verdict.claimed_ship,
        "verdict":              verdict.verdict,
        "confidence":           verdict.confidence,
        "flags":                verdict.flags,
        "claimed_ship_deaths":  verdict.claimed_ship_deaths,
        "top_ranked_ship":      verdict.top_ranked_ship,
        "top_ranked_deaths":    verdict.top_ranked_deaths,
        "comparison_table":     verdict.comparison_table,
        "explanation":          verdict.explanation,
        "retrieval_verified":   verdict.retrieval_verified,
    }


# ---------------------------------------------------------------------------
# Formatted output (for Consensus Engine injection)
# ---------------------------------------------------------------------------

def format_verdict_for_output(result: dict) -> str:
    """
    Format a maritime verdict dict into the standard Veracore output block.
    """
    lines = []
    lines.append(f"VERDICT: {result['verdict']}")
    lines.append("")

    if result["flags"]:
        for flag in result["flags"]:
            lines.append(f"FLAG: {flag}")
        lines.append("")

    lines.append("Explanation:")
    lines.append(result["explanation"])
    lines.append("")

    lines.append("Comparison Table (Peacetime Maritime Disasters):")
    lines.append(f"{'Rank':<6}{'Ship':<30}{'Year':<8}{'Est. Deaths':<14}{'Source'}")
    lines.append("-" * 70)
    for row in result["comparison_table"]:
        marker = " ◄ CLAIMED" if row["ship"].lower() == result["claimed_ship"].lower() else ""
        lines.append(
            f"{row['rank']:<6}{row['ship']:<30}{row['year']:<8}"
            f"{row['estimated_deaths']:,<14}{row['source']}{marker}"
        )
    lines.append("")

    lines.append(
        f"Confidence: {int(result['confidence'] * 100)}% "
        f"| Retrieval Verified: {'YES' if result['retrieval_verified'] else 'NO (seed data only)'}"
    )

    return "\n".join(lines)
