"""
eval.py — Automated evaluation harness for the AI Playlist Planner.

Runs 5 representative test cases through the full agent pipeline and
checks each output against 4 quality criteria using simple deterministic
heuristics. No golden answers are required — checks test for reasonable
behavior given the input vibe.

Each test checks:
  1. Output non-empty  — the agent returned something (not blank, not an error)
  2. Response length   — at least 200 chars (a real playlist is several lines)
  3. Vibe keyword      — at least one expected keyword appears in the response
  4. Expected song     — at least one expected song title from the catalog appears

A test case PASSES when all 4 checks pass.

Requirements:
  - GEMINI_API_KEY must be set in .env or the environment
  - Run from the project root with the venv active:

      python -m ai_agent.eval
"""

import os
import sys
import logging
from typing import List, Dict, Tuple

# ── Logging setup ──────────────────────────────────────────────────────────────
# Must come before any import that uses the logger so agent.py's
# log lines are visible during the eval run.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.recommender import load_songs
from ai_agent.agent import plan_playlist


# ── Test cases ─────────────────────────────────────────────────────────────────
# expected_keywords: at least one must appear (case-insensitive) in the output.
# expected_songs:    titles from data/songs.csv — at least min_song_matches must appear.

TEST_CASES = [
    {
        "id": 1,
        "name": "Late-night coding session",
        "input": (
            "I need music for a late-night coding session. "
            "Something calm and focused, not distracting."
        ),
        "min_length": 200,
        "expected_keywords": ["lofi", "focus", "chill", "calm", "acoustic"],
        "expected_songs": ["Midnight Coding", "Focus Flow", "Library Rain", "Spacewalk Thoughts"],
        "min_song_matches": 2,
    },
    {
        "id": 2,
        "name": "Intense gym workout",
        "input": (
            "I'm about to do a heavy lifting session at the gym. "
            "I need the most aggressive, high-energy music possible."
        ),
        "min_length": 200,
        "expected_keywords": ["energy", "intense", "aggressive", "heavy", "workout", "pump"],
        "expected_songs": ["Iron Curtain", "Bass Drop", "Gym Hero", "Storm Runner"],
        "min_song_matches": 2,
    },
    {
        "id": 3,
        "name": "Rainy Sunday morning",
        "input": (
            "It's a rainy Sunday morning and I'm making breakfast. "
            "I want something warm, cozy, and acoustic."
        ),
        "min_length": 200,
        "expected_keywords": ["acoustic", "calm", "cozy", "peaceful", "warm", "gentle", "soft"],
        "expected_songs": ["Mountain Trail", "Coffee Shop Stories", "Library Rain", "Porch Swing Blues"],
        "min_song_matches": 2,
    },
    {
        "id": 4,
        "name": "Romantic dinner",
        "input": "I'm cooking a romantic dinner at home. I need soft, warm background music.",
        "min_length": 200,
        "expected_keywords": ["romantic", "soft", "warm", "smooth", "gentle", "cozy", "relaxed"],
        "expected_songs": ["Golden Hour", "Coffee Shop Stories", "Isla Verde", "Nocturne in D"],
        "min_song_matches": 1,
    },
    {
        "id": 5,
        "name": "Pre-game hype",
        "input": (
            "Getting ready for a big game tonight. "
            "Need hype music to pump me up and get the energy going."
        ),
        "min_length": 200,
        "expected_keywords": ["energy", "hype", "pump", "upbeat", "confidence", "motivat", "excit"],
        "expected_songs": ["Sunrise City", "Street Cypher", "Gym Hero", "Neon Pulse", "Iron Curtain"],
        "min_song_matches": 1,
    },
]


# ── Check functions ─────────────────────────────────────────────────────────────

def check_non_empty(output: str) -> Tuple[bool, str]:
    """Output is not blank and does not look like an error."""
    is_error = "something went wrong" in output.lower() or output.startswith("AGENT ERROR")
    ok = bool(output.strip()) and not is_error
    detail = f"{len(output)} chars" if ok else "empty or error response"
    return ok, detail


def check_substantial(output: str, min_length: int) -> Tuple[bool, str]:
    """Output is long enough to contain a real playlist.
    Returns False immediately if the output is an error message —
    length is only meaningful for valid responses."""
    is_error = "something went wrong" in output.lower() or output.startswith("AGENT ERROR")
    if is_error:
        return False, "skipped — output is an error message"
    ok = len(output) >= min_length
    detail = (
        f"length {len(output)} >= {min_length}"
        if ok
        else f"too short ({len(output)} chars, expected >= {min_length})"
    )
    return ok, detail


def check_vibe_keyword(output: str, keywords: List[str]) -> Tuple[bool, str]:
    """At least one expected vibe keyword appears in the output."""
    lower = output.lower()
    found = [kw for kw in keywords if kw.lower() in lower]
    ok = len(found) > 0
    detail = f"found: {found[:3]}" if ok else f"none of {keywords} found in output"
    return ok, detail


def check_song_present(output: str, songs: List[str], min_matches: int) -> Tuple[bool, str]:
    """At least min_matches expected song titles appear in the output."""
    found = [s for s in songs if s.lower() in output.lower()]
    ok = len(found) >= min_matches
    detail = (
        f"songs matched: {found}"
        if ok
        else f"only {len(found)}/{min_matches} expected songs found (got: {found})"
    )
    return ok, detail


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_eval(catalog: List[Dict]) -> None:
    passed = 0
    total_checks = 0
    passed_checks = 0
    response_lengths = []
    SEP = "─" * 62

    print()
    print("=" * 62)
    print("  AI PLAYLIST PLANNER — EVALUATION HARNESS")
    print(f"  {len(TEST_CASES)} test cases  |  catalog: {len(catalog)} songs")
    print("=" * 62)

    for tc in TEST_CASES:
        print()
        print(SEP)
        print(f"Test {tc['id']}/{len(TEST_CASES)}: {tc['name']}")
        short_input = tc["input"][:78] + ("..." if len(tc["input"]) > 78 else "")
        print(f"  Input: \"{short_input}\"")
        print()

        output = ""
        try:
            output = plan_playlist(tc["input"], catalog)
        except Exception as exc:
            output = f"AGENT ERROR: {exc}"
            print(f"  [EXCEPTION] {exc}")

        response_lengths.append(len(output))

        checks: List[Tuple[str, bool, str]] = [
            ("Output non-empty",    *check_non_empty(output)),
            ("Response length",     *check_substantial(output, tc["min_length"])),
            ("Vibe keyword found",  *check_vibe_keyword(output, tc["expected_keywords"])),
            ("Expected song found", *check_song_present(output, tc["expected_songs"], tc["min_song_matches"])),
        ]

        case_passed = True
        case_passed_count = 0
        for check_name, ok, detail in checks:
            symbol = "PASS" if ok else "FAIL"
            print(f"  [{symbol}] {check_name}: {detail}")
            total_checks += 1
            if ok:
                passed_checks += 1
                case_passed_count += 1
            else:
                case_passed = False

        result_label = "PASS" if case_passed else "FAIL"
        print()
        print(f"  RESULT: {result_label} ({case_passed_count}/{len(checks)} checks passed)")

        if case_passed:
            passed += 1

    # ── Summary ────────────────────────────────────────────────────────────────
    avg_len = int(sum(response_lengths) / len(response_lengths)) if response_lengths else 0

    print()
    print("=" * 62)
    print("  EVALUATION SUMMARY")
    print("=" * 62)
    print(f"  Tests passed:           {passed}/{len(TEST_CASES)}")
    print(f"  Individual checks:      {passed_checks}/{total_checks}")
    print(f"  Avg response length:    {avg_len} chars")
    print()

    if passed == len(TEST_CASES):
        print("  All tests passed. Agent performs reliably across vibe types.")
    elif passed >= len(TEST_CASES) - 1:
        failed = len(TEST_CASES) - passed
        print(f"  {failed} test(s) failed — review FAIL lines above for details.")
    else:
        failed = len(TEST_CASES) - passed
        print(f"  {failed} test(s) failed — agent may need prompt or tool adjustments.")

    print("=" * 62)
    print()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print()
        print("ERROR: GEMINI_API_KEY is not set.")
        print("Add it to your .env file or export it in your shell, then re-run:")
        print()
        print("  echo 'GEMINI_API_KEY=your_key_here' >> .env")
        print("  python -m ai_agent.eval")
        print()
        sys.exit(1)

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "songs.csv")
    catalog = load_songs(os.path.normpath(csv_path))

    run_eval(catalog)
