# System Architecture — AI Playlist Planner

## Component Overview

| Component | File | Role |
|---|---|---|
| Streamlit UI | `ai_agent/app.py` | User-facing web interface; loads catalog; renders output |
| Gemini Agent | `ai_agent/agent.py` | Manages agentic loop; sends/receives messages with Gemini API |
| Tool Dispatcher | `agent.py · run_tool()` | Routes Gemini's function_call requests to the right Python function |
| Tool Library | `ai_agent/tools.py` | 4 callable tools: catalog summary, recommendations, filter, song details |
| Recommender Engine | `src/recommender.py` | Core scoring logic: `score_song()`, `recommend_songs()` |
| Song Catalog | `data/songs.csv` | 20 songs with genre, mood, energy, acousticness, valence, tempo |
| Test Suite | `tests/test_recommender.py` | 39 pytest tests; human-verified correctness of recommender |

---

## Data Flow Diagram

```mermaid
flowchart TD
    User(["👤 User\n(types a vibe / situation)"])
    UI["Streamlit UI\nai_agent/app.py"]
    CSV[("Song Catalog\ndata/songs.csv\n20 songs")]
    Agent["Gemini Agent\nai_agent/agent.py\nplan_playlist()"]
    GeminiAPI["☁️ Gemini API\ngemini-3-flash-preview\n(LLM reasoning)"]
    Dispatcher["Tool Dispatcher\nrun_tool()"]
    Tools["Tool Library\nai_agent/tools.py"]
    Recommender["Recommender Engine\nsrc/recommender.py\nscore_song() · recommend_songs()"]
    Output(["📋 Playlist\n(markdown rendered in UI)"])
    Tests["🧪 Test Suite\ntests/test_recommender.py\n39 pytest tests"]
    Human(["👤 Human / Developer\n(runs tests, reviews results)"])

    User -- "situation text" --> UI
    CSV -- "load_songs()" --> UI
    UI -- "plan_playlist(situation, songs)" --> Agent

    Agent -- "Turn 1: send user message\n+ system prompt\n+ tool schemas" --> GeminiAPI
    GeminiAPI -- "function_call parts\n(tool name + args)" --> Agent
    Agent -- "tool name + args" --> Dispatcher
    Dispatcher -- "dispatch" --> Tools
    Tools -- "get_recommendations()\nfilter_songs_by_attribute()\nget_song_details()" --> Recommender
    Recommender -- "scored song list" --> Tools
    Tools -- "JSON result" --> Dispatcher
    Dispatcher -- "FunctionResponse parts" --> Agent
    Agent -- "Turn N: send tool results" --> GeminiAPI
    GeminiAPI -- "final text response\n(no more function_calls)" --> Agent
    Agent -- "playlist string" --> UI
    UI -- "st.markdown(result)" --> Output

    Human -- "pytest" --> Tests
    Tests -- "validates score_song()\nrecommend_songs()" --> Recommender
```

---

## Agentic Loop Detail

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant Agent as agent.py
    participant Gemini as Gemini API
    participant Tools as tools.py
    participant Rec as recommender.py

    UI->>Agent: plan_playlist(situation, songs)
    Agent->>Gemini: Turn 0 — user message + system prompt + tool schemas

    loop Tool-use rounds (max 10)
        Gemini-->>Agent: response.parts (function_call)
        Agent->>Tools: run_tool(name, args, songs)
        alt get_recommendations
            Tools->>Rec: recommend_songs(user_prefs, songs, k)
            Rec-->>Tools: [(song, score, explanation), ...]
        else get_catalog_summary / filter / get_song_details
            Tools-->>Agent: JSON result (no recommender call)
        end
        Tools-->>Agent: JSON result string
        Agent->>Gemini: FunctionResponse parts (tool results)
    end

    Gemini-->>Agent: final text (no function_calls)
    Agent-->>UI: playlist markdown string
    UI-->>UI: st.markdown(result) → rendered output
```

---

## Where Humans Are Involved

| Touch point | How |
|---|---|
| **Input** | User types a natural-language situation in the Streamlit text box |
| **Output review** | User reads and judges the AI-generated playlist |
| **Test authoring** | Developer wrote 39 unit tests in `tests/test_recommender.py` |
| **Test execution** | Developer runs `pytest` to verify recommender correctness |
| **API key setup** | Developer sets `GEMINI_API_KEY` in `.env` before running |
