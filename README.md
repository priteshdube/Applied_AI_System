# AI Playlist Planner

A music recommendation system that combines a deterministic scoring engine with a Google Gemini-powered AI agent. Describe what you're doing or feeling in plain English — the AI reasons through your vibe, queries the catalog using tools, and builds you a personalized playlist with song-by-song explanations.

---

## Original Project — Modules 1–3

**Music Recommender System** (`src/recommender.py`)

The original project is a pure Python music recommendation engine built across Modules 1–3 of the CodePath Applied AI course. It loads a catalog of 20 songs from a CSV file and scores each song against a user taste profile using a weighted Gaussian proximity algorithm. A user profile specifies a favorite genre, favorite mood, target energy level, and acoustic preference — and each song receives a numerical score (max ~9.5) based on how closely it matches those preferences. The top `k` highest-scoring songs are returned as recommendations, each with a plain-English explanation of why it ranked where it did.

---

## Title and Summary

**AI Playlist Planner** — Tell the AI what you're doing, get a playlist that fits.

Traditional music recommenders require users to fill out preference forms or click through menus. This project lets you describe your situation naturally — "late-night coding session," "pre-game hype," "Sunday morning with coffee" — and an AI agent translates that into structured preferences, queries the catalog, and returns a curated playlist with reasoning for every pick.

This matters because the gap between "I know what I want" and "I can describe it to a computer" is where most recommender systems fail. Using an LLM as the preference-extraction layer bridges that gap without sacrificing the transparency and correctness of a deterministic scoring engine underneath.

---

## Architecture Overview

The system is split into two layers that work together:

**Layer 1 — Deterministic Recommender (Modules 1–3)**
`src/recommender.py` contains the scoring engine. It computes a weighted score for every song against a user profile: +2.0 for a genre match, +1.5 for a mood match, and Gaussian proximity scores for energy (0–4.0) and acousticness (0–2.0). The math is fixed, testable, and produces the same output every time for the same inputs.

**Layer 2 — Gemini AI Agent (Module 4+)**
`ai_agent/` wraps Layer 1 in a tool-use agentic loop. The Gemini model receives the user's natural-language situation along with a system prompt and four tool schemas. It calls tools to explore the catalog, then calls `get_recommendations` — which delegates directly to Layer 1's `recommend_songs()` — to score and rank songs. The loop runs until Gemini stops calling tools and writes its final playlist response.

**UI**
`ai_agent/app.py` is a Streamlit web app. It loads the catalog once on startup, takes free-text input, calls `plan_playlist()`, and renders the agent's markdown response. The sidebar shows the full catalog for reference.

**Data flow:**
```
User types vibe
  → Streamlit calls plan_playlist(situation, songs)
    → Gemini receives message + system prompt + tool schemas
      → Gemini calls get_catalog_summary → knows valid genres/moods
        → Gemini calls get_recommendations(genre, mood, energy, acoustic)
          → tools.py calls recommend_songs() from src/recommender.py
            → scored, ranked songs returned as JSON to Gemini
              → Gemini writes final playlist text
                → Streamlit renders markdown to user
```

See [system_diagram.md](system_diagram.md) for full Mermaid flowcharts of both the component view and the turn-by-turn sequence.

**Testing** lives outside both layers: `tests/test_recommender.py` has 39 unit tests that validate the scoring engine directly, independent of the AI agent.

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) (free tier works)

### 1. Clone the repository

```bash
git clone <repo-url>
cd applied-ai-sytem-final
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Create a `.env` file in the project root:

```bash
echo "GEMINI_API_KEY=your_key_here" > .env
```

The `.env` file is not committed. The key is only needed for the AI Playlist Planner — the CLI recommender and test suite work without it.

### 5. Run the AI Playlist Planner (web app)

```bash
venv/bin/streamlit run ai_agent/app.py
```

Then open `http://localhost:8501` in your browser.

### 6. Run the CLI Recommender (no API key needed)

Runs the scoring engine against three pre-built profiles and prints the top 5 for each:

```bash
python -m src.main
```

### 7. Run the test suite

```bash
pytest
```

All 39 tests should pass. No API key or network connection required.

---

## Sample Interactions

These are real outputs from the agent. The song titles, scores, and reasoning all come from the actual 20-song catalog and scoring algorithm.

---

### Interaction 1 — Late-night coding session

**Input:**
> I need music for a late-night coding session. Something calm that helps me focus without being distracting.

**Agent reasoning (internal tool calls):**
1. Called `get_catalog_summary` → learned available genres include `lofi`, `ambient`, `classical`; moods include `chill`, `focused`, `peaceful`
2. Called `get_recommendations` with `favorite_genre="lofi"`, `favorite_mood="focused"`, `target_energy=0.38`, `likes_acoustic=True`, `k=5`

**Output:**
> Late-night focus calls for something that fades into the background without disappearing — low energy, mostly acoustic, no sudden drops. Here's what the catalog has for you:
>
> **Your Playlist:**
> 1. **Focus Flow** by LoRoom — A lofi track built for exactly this: 80 BPM, low energy, and high acousticness that keeps your brain in work mode.
> 2. **Midnight Coding** by LoRoom — The name says it all. Chill lofi with a 78 BPM groove that's been engineered for late-night sessions.
> 3. **Library Rain** by Paper Lanterns — The most acoustic track in the lofi catalog. At 0.86 acousticness it feels like studying in a quiet room with rain outside.
> 4. **Spacewalk Thoughts** by Orbit Bloom — Ambient instead of lofi, but the lowest energy track in the whole catalog (0.28). Perfect if you want near-silence with texture.
> 5. **Nocturne in D** by Aria Voss — A classical piano piece with the lightest touch in the catalog. If you need something that feels almost like silence, this is it.

---

### Interaction 2 — Pre-game workout hype

**Input:**
> I'm about to hit the gym for a heavy lifting day. I need something aggressive and high-energy to get me pumped up.

**Agent reasoning (internal tool calls):**
1. Called `get_catalog_summary` → noted high-energy genres: `metal`, `electronic`, `rock`, `trap`; moods: `aggressive`, `intense`, `euphoric`
2. Called `get_recommendations` with `favorite_genre="metal"`, `favorite_mood="aggressive"`, `target_energy=0.95`, `likes_acoustic=False`, `k=5`

**Output:**
> Heavy lifting day needs maximum intensity — high energy, heavy production, no acoustic warmth. The catalog's hardest-hitting tracks:
>
> **Your Playlist:**
> 1. **Iron Curtain** by Gravefield — The highest-energy track in the entire catalog at 0.97, 168 BPM, and a dark aggressive mood. This is the one.
> 2. **Bass Drop** by Circuit Null — Electronic at 0.95 energy and 140 BPM. Pure euphoric drive for when the iron needs to move.
> 3. **Gym Hero** by Max Pulse — The pop catalog's most intense entry at 0.93 energy and 132 BPM. Upbeat and aggressive at the same time.
> 4. **Storm Runner** by Voltline — Rock at 0.91 energy and 152 BPM. Fast, distorted, and relentless.
> 5. **Neon Pulse** by Trapdoor — Trap at 0.82 energy with a dark tone (valence 0.38) and high danceability. A different texture to round out the set.

---

### Interaction 3 — Rainy Sunday morning

**Input:**
> It's a rainy Sunday and I'm just making breakfast. Nothing intense, something warm and maybe a little nostalgic or cozy.

**Agent reasoning (internal tool calls):**
1. Called `get_catalog_summary`
2. Called `filter_songs_by_attribute` with `attribute="energy_range"`, `energy_min=0.0`, `energy_max=0.50` → scanned the low-energy portion of the catalog
3. Called `get_recommendations` with `favorite_genre="folk"`, `favorite_mood="peaceful"`, `target_energy=0.35`, `likes_acoustic=True`, `k=5`

**Output:**
> Rainy Sunday breakfast calls for something warm, unhurried, and mostly acoustic — the kind of music that feels like it was made in a small room. Here's your morning playlist:
>
> **Your Playlist:**
> 1. **Mountain Trail** by Cedar & Pine — The most acoustic track in the folk catalog at 0.95 acousticness. Gentle, 84 BPM, and deeply peaceful. Perfect for a slow morning.
> 2. **Coffee Shop Stories** by Slow Stereo — Jazz with 0.89 acousticness and a "relaxed" mood. This one actually sounds like the place you'd want to be right now.
> 3. **Porch Swing Blues** by Dusty Harp — Blues at 0.88 acousticness with a wistful, slightly sad tone. Fits the grey-sky vibe without being heavy.
> 4. **Backroad Honey** by June Calloway — Country with a "nostalgic" mood and 0.80 acousticness. If cozy had a sound, this is close to it.
> 5. **Library Rain** by Paper Lanterns — Lofi at 0.86 acousticness and very low energy. The transition pick if you want to shift from breakfast to a quiet sit-down after.

---

## Design Decisions

### Why keep the scoring engine separate and untouched?

The original `src/recommender.py` was never modified when the AI agent was added. This was a deliberate choice: the scoring logic is tested, correct, and deterministic. Wrapping it as a tool — rather than having Gemini score songs itself — means the AI is responsible only for preference extraction (the hard part), while a well-tested function handles the actual ranking. This also means the 39-test suite continues to be the source of truth for scoring behavior.

**Trade-off:** Gemini cannot explain fine-grained scoring decisions (e.g., "this song ranked 3rd because its energy was 0.12 away from your target"). The agent sees the top-k results but not the full score breakdown. A richer tool that exposed scores in the response would give Gemini more to work with — but also more tokens to process per turn.

### Why 4 tools instead of 1?

One large tool (e.g., `search_songs(query)`) would hide the reasoning steps. Using four small, single-purpose tools forces Gemini to make decisions at each step: *what catalog values exist? what should I recommend? do I need to explore a subset first?* This makes the agent's behavior more transparent and easier to debug — you can watch exactly which tools fire and why in the Streamlit terminal output.

**Trade-off:** More tools mean more round-trips to the API, which means more latency. For a 20-song catalog this is fine. At scale (thousands of songs) you'd want to rethink the tool surface.

### Why Streamlit instead of a REST API?

Streamlit let the UI be built in the same Python session as the agent, which means the loaded song catalog is cached in memory and shared between the catalog sidebar and the agent calls. A REST API would need a database or separate caching layer.

**Trade-off:** Streamlit is single-user by design — it does not support concurrent sessions well. For a production system you'd move to FastAPI + a proper frontend.

### Why a safety cap of `max_turns=10`?

The agentic loop has no natural hard stop from the model side — Gemini could theoretically keep calling tools indefinitely. Ten turns is conservative (typical sessions use 2–4), keeps API costs bounded, and never causes a long wait during a class demo.

---

## Testing Summary

### What the test suite covers

39 tests across 11 test classes in `tests/test_recommender.py`:

| Class | What it tests |
|---|---|
| `TestGaussian` | Gaussian helper: exact match, symmetry, sigma decay |
| `TestScoreSongNormal` | Correct bonus amounts, return type, max score of 9.5 |
| `TestScoreSongCaseSensitivity` | Genre and mood matching is case-insensitive |
| `TestEmptyStrings` | Empty genre/mood strings don't crash; documented "empty matches empty" behavior |
| `TestAdversarialProfiles` | Contradictory preferences (high-energy lofi fan, out-of-range energy values) |
| `TestRecommendKEdgeCases` | k=0, k > catalog size, k=1 |
| `TestEmptyCatalog` | Empty catalog returns empty list, doesn't raise |
| `TestRanking` | Results sorted descending, deterministic across calls, ties consistent |
| `TestAcousticMapping` | `likes_acoustic=True` targets 0.75; `False` targets 0.25 |
| `TestExplainRecommendation` | Explanation string is non-empty, contains "Score", mentions match/mismatch |
| `TestSingleSongCatalog` | One-song catalog always returns that song for k≥1 |

### What worked

- The Gaussian scoring behaves exactly as intended: at one sigma away from the target it returns ~60% of maximum points (`e^(-0.5) ≈ 0.6065`), verified by the `test_one_sigma_away_returns_approx_60_pct` test.
- The adversarial profile tests caught a real insight: a user who says they love lofi but wants maximum energy will never get a perfect-score result, because the genre/mood bonus and energy penalty partially cancel each other. That's the correct behavior and the test documents it explicitly.
- All 39 tests pass deterministically with no mocking of external services.

### What didn't work / what was learned

- **The AI agent is not directly unit-tested.** The agentic loop in `agent.py` makes live API calls to Gemini, so it can't be tested with `pytest` without mocking the entire SDK. This is a known limitation — the correctness guarantee lives in the scoring engine tests, not in integration tests for the agent.
- **Empty string behavior.** Early in development, `score_song` would register an empty genre preference as matching an empty genre in the catalog. Rather than silently "fixing" this edge case by adding a guard, a test was written to document the behavior explicitly. This is the right call: the catalog doesn't have blank genres, so it's harmless — and documenting known behavior is better than pretending the edge case doesn't exist.
- **k=0 needs to work.** It wasn't obvious that `recommend(user, k=0)` should return an empty list rather than crash. Writing the k-edge-case tests first surfaced this before it could become a real bug.

---

## Reflection

Building this project made two things clear that weren't obvious beforehand.

**LLMs are best used at the boundary between language and structure.** The hardest part of a music recommender isn't the math — it's understanding what a user actually wants when they say "something for a Sunday drive" or "I'm in a dark mood." The scoring engine can be perfectly calibrated and still fail if it gets bad inputs. Plugging Gemini in at exactly that boundary — preference extraction — gave the system its biggest quality jump for the least change to the underlying code.

**Agentic tool-use is most valuable when the steps are visible.** The most educational part of this project wasn't getting the agent to produce good playlists — it was watching it call `get_catalog_summary` before every session without being explicitly told to do so in that turn. The model learned from the system prompt that it should ground itself in valid values before reasoning. That's a behavior that emerges from good prompt design, not from code. Seeing that happen concretely changed how I think about what "reasoning" means in these systems: it's a sequence of decisions with observable checkpoints, not a black box.

---

## Project Structure

```
applied-ai-sytem-final/
├── data/
│   └── songs.csv              # 20-song catalog with 9 features per song
├── src/
│   ├── main.py                # CLI entry point (runs 3 pre-built profiles)
│   └── recommender.py         # Core engine: Song, UserProfile, score_song(), recommend_songs()
├── ai_agent/
│   ├── __init__.py
│   ├── agent.py               # Gemini agentic loop: plan_playlist()
│   ├── tools.py               # 4 tool functions + Gemini schema definitions
│   └── app.py                 # Streamlit web UI
├── tests/
│   └── test_recommender.py    # 39 unit tests (pytest)
├── system_diagram.md          # Mermaid architecture diagrams
├── model_card.md              # Model card
├── .env                       # API keys — not committed
├── requirements.txt           # Python dependencies
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Web UI | Streamlit |
| AI Model | Google Gemini (`gemini-3-flash-preview`) |
| AI SDK | `google-genai` 1.73.1 |
| Data handling | pandas, csv |
| Env management | python-dotenv |
| Testing | pytest |
