# Reflection and Ethics

## 1. Limitations and Biases

**Catalog size is the biggest constraint.**
The system works entirely from 20 hand-picked songs. No matter how well the agent reasons about a user's situation, it can only recommend what exists in that catalog. A user asking for K-pop, Latin trap, or Afrobeats will get routed toward whatever genre scores closest — not what they actually want. This is a data limitation, not an algorithmic one, but it shapes every output the system produces.

**The scoring weights encode assumptions.**
Genre match is worth +2.0 points and mood match is worth +1.5. These numbers were chosen by design, but they impose a fixed priority order on every recommendation: genre always outweighs mood, mood always outweighs energy proximity. A user who cares more about energy level than genre label will be poorly served by a system that doesn't know that about them.

**The catalog's genre and mood labels are culturally narrow.**
The 20 songs span pop, lofi, rock, jazz, r&b, ambient, folk, blues, metal, reggae, classical, and a few others — all broadly Western. The mood labels (chill, intense, romantic, focused, melancholic, euphoric) reflect a particular emotional vocabulary. Users whose musical culture uses different genre names or emotional categories will find the system doesn't map onto their world cleanly.

**The Gaussian scoring curve assumes symmetric preferences.**
The algorithm treats "slightly too much energy" and "slightly too little energy" as equally bad. In practice, a user who wants calm music while studying probably tolerates music that's a little too quiet much better than music that's a little too loud. The curve doesn't capture that asymmetry.

**The AI agent can only be as good as its tools.**
If `get_recommendations` returns results, Gemini trusts them. There is no step where the agent double-checks whether a song it is recommending actually fits the situation — it relies entirely on the scoring engine's output and its own reasoning. If the scoring engine produces a counterintuitive ranking (which can happen with conflicting preferences), Gemini will explain it confidently rather than flag it as potentially wrong.

---

## 2. Could Your AI Be Misused?

For a music recommender, the risk surface is narrower than most AI systems, but it is not zero.

**Mood reinforcement is the most realistic concern.**
A user going through a difficult time could describe their mood honestly ("I feel hopeless and exhausted") and the system would recommend music that matches — dark, melancholic, low-energy tracks — without any awareness that this might deepen rather than help their state. The system has no model of user wellbeing, only user preference.

**Prompt injection through the situation field.**
The user's free-text input is sent directly to Gemini as part of the conversation. A user could attempt to inject instructions into the prompt — for example, describing a "situation" that is actually a hidden instruction to ignore the system prompt or behave differently. The current system doesn't sanitize or validate the input before passing it to the model.

**API key exposure.**
This actually happened during this project: the Gemini API key was committed to a Git repository, detected by Google's automated scanner, and revoked. Any system that embeds credentials in code or stores them in tracked files is one accidental push away from a compromised key.

**Potential mitigations:**
- Add a brief mood-safety check before routing a request — if the input contains signals of crisis or distress, respond with a resource rather than a playlist.
- Limit the length and allowed content of the situation input field.
- Treat API credentials as infrastructure secrets, not application code — use environment variables only, verify `.gitignore` coverage before the first commit, and rotate keys on any suspected exposure.

---

## 3. What Surprised You While Testing?

**The API key was flagged as leaked during a live evaluation run.**
The most unexpected moment in the entire project was watching the eval script succeed on the first tool call (`get_catalog_summary` completed, returning 376 bytes) and then fail on the very next API call — not because of a code error, but because Google had detected the key in a public repository and invalidated it mid-session. A reliability evaluation that was designed to test the AI ended up surfacing a real operational security failure instead.

**The agent followed the system prompt's tool-ordering instruction without being forced to.**
The system prompt says "ALWAYS call `get_catalog_summary` first." Looking at the logging output across all test cases, the agent did this on every single session, every time — it never skipped it or reordered its calls. That consistency was not guaranteed. An LLM could reasonably decide to skip the catalog summary if it felt confident about the genre and mood values. It didn't. The system prompt design held up.

**The `check_substantial` bug in the eval script passed bad outputs.**
During the second test run (after key rotation), the eval showed `Response length: PASS (471 chars)` on a test that had just raised an exception. The 471 characters were the error message itself, not a playlist. The check was measuring string length without caring whether the string was a valid response. This is the kind of quiet failure that makes evaluation harder to trust than it looks — a metric can show green while the underlying behavior is broken. The fix is described in the AI Collaboration section below.

---

## 4. Collaboration With AI (Claude)

Claude assisted throughout this project — from the initial architecture design, to writing the agent and tool code, to building the evaluation harness, to debugging the API key errors. The collaboration was productive but not flawless.

---

**A moment where the AI gave a genuinely helpful suggestion:**

When it came time to build the AI agent layer, Claude's strongest suggestion was architectural: keep `src/recommender.py` completely untouched and wrap it as a tool rather than rewriting the scoring logic inside the agent or inside a new file. The reasoning was that the scoring engine already had 39 passing tests and a known-correct implementation — there was no reason to risk breaking it by modifying it. Instead, `get_recommendations` in `tools.py` calls `recommend_songs()` directly, which means the test suite remains valid, the existing scoring behavior is preserved, and the agent only adds new behavior on top.

This turned out to be the right call. The original tests continued to run and pass without any changes throughout the entire agent development. That wouldn't have been true if the scoring logic had been copied or refactored into a new location.

---

**A moment where the AI's suggestion was flawed:**

Claude wrote the `check_substantial` function in `eval.py` as a simple character-length check:

```python
def check_substantial(output: str, min_length: int) -> Tuple[bool, str]:
    ok = len(output) >= min_length
    ...
```

The problem: it counts characters in the string regardless of what that string contains. When the API key was invalid and every test raised an exception, the error message string (`"AGENT ERROR: 400 INVALID_ARGUMENT..."`) was 471 characters — long enough to pass the 200-character minimum. So `check_substantial` reported `PASS` on every failed test, making the results look better than they were.

Claude actually noticed this bug at the end of the session ("I can fix that after your key is working") but did not fix it before delivering the code. Pointing it out and deferring the fix is not the same as not introducing the bug. A correct implementation should only measure length on outputs that passed the `check_non_empty` gate first. The corrected version:

```python
def check_substantial(output: str, min_length: int) -> Tuple[bool, str]:
    # Only meaningful if the output is not an error — skip if non_empty already failed
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
```

This experience is a good illustration of a general principle about working with AI tools: the AI can produce code that is structurally correct and passes casual review while still containing a logic error that only shows up under specific conditions. The responsibility for catching those errors remains with the developer.
