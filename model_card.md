# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0** — a content-based music recommender with an AI Playlist Planner agent layer powered by Google Gemini.

---

## 2. Intended Use

VibeFinder generates personalized song recommendations based on a user's stated taste preferences: their favorite genre, favorite mood, target energy level, and whether they prefer acoustic or produced sounds. It is designed for individual listeners who want music suggestions that match the vibe they are already in — not necessarily to discover something completely new.

The system assumes the user can articulate their preferences clearly (e.g., "lofi, chill, low energy, acoustic"). It does not track listening history or learn over time. This project was built for classroom exploration as part of a CodePath Applied AI Systems course, but the scoring logic and agentic layer are fully functional.

---

## 3. How the Model Works

When a user submits their preferences, each song in the catalog gets a score on a scale from 0 to 9.5. The score comes from four separate signals:

**Genre match (up to 2.0 points):** If the song's genre exactly matches the user's favorite genre, it earns 2 points. Otherwise it earns zero. This is the biggest single signal after energy.

**Mood match (up to 1.5 points):** Same idea — an exact match on mood adds 1.5 points.

**Energy proximity (up to 4.0 points):** Rather than a hard cutoff, energy uses a bell-curve (Gaussian) approach. A song earns the full 4 points if its energy level is exactly what the user wants. Songs that are a little off earn slightly less; songs very far away in energy earn nearly nothing. This is the largest component of the score and is what separates songs that share the same genre.

**Acousticness proximity (up to 2.0 points):** Works the same way as energy. If the user likes acoustic music, the system targets an acousticness of 0.75; if they prefer produced music, it targets 0.10. Songs are scored on how close they land.

The songs with the highest total score are returned as the top recommendations. The agentic AI layer (built on top) uses Gemini to interpret natural language requests like "make me a late-night study playlist" and calls the recommender behind the scenes.

---

## 4. Data

The catalog contains **20 songs** stored in `data/songs.csv`. Every song has the following attributes: title, artist, genre, mood, energy (0–1), tempo in BPM, valence, danceability, and acousticness.

**Genres represented:** lofi, pop, rock, ambient, jazz, synthwave, indie pop, r&b, blues, folk, hip-hop, classical, metal, reggae, country, trap, electronic — 17 distinct genres across 20 songs.

**Moods represented:** happy, chill, intense, relaxed, focused, moody, romantic, peaceful, confident, melancholic, aggressive, nostalgic, dark, sad, euphoric.

No data was removed from the starter dataset. The catalog is deliberately small for a classroom simulation. Notably, several genres (e.g., metal, reggae, classical, trap) have only a single representative song each, which limits how useful recommendations can be for those styles. The data also does not include any world music, Latin, gospel, or R&B subgenres beyond a single entry, so large portions of musical taste are entirely missing.

Tempo, valence, and danceability are present in the dataset but are **not used** in the scoring function — they exist as data but are currently unused features.

---

## 5. Strengths

The system works best when a user's preferences align tightly with a well-represented genre. For example:

- A **chill lofi** listener gets highly relevant results because there are multiple lofi songs with low energy and high acousticness (Library Rain, Midnight Coding, Focus Flow) that score well across all four components.
- A **high-energy pop** fan sees Sunrise City and Gym Hero consistently rise to the top because they match on genre and land very close to the target energy range.
- The Gaussian proximity scoring is a meaningful improvement over a simple threshold filter — it creates a continuous ranking rather than a binary in/out decision, so songs that are close but not perfect still get partial credit.

The system reliably separates high-energy songs from low-energy ones regardless of genre, which means the energy score alone provides a useful secondary sort when genre matches are scarce.

---

## 6. Limitations and Bias

**Small catalog:** With 20 songs, any genre with only one entry (metal, reggae, classical, trap, blues, folk, country, ambient) will return that one song at the top regardless of how well it fits, simply because nothing else matches. A user who likes metal will always get Iron Curtain as their first result.

**Exact string matching:** Genre and mood comparisons require an exact case-insensitive match. A user who types "hip hop" will get zero genre bonus against songs labeled "hip-hop." This makes the categorical signals brittle.

**Unused features:** Tempo, valence, and danceability are in the data but ignored by the scorer. A user who cares about tempo (e.g., wants 120 BPM for running) has no way to express that.

**No diversity mechanism:** The top 5 recommendations can all come from the same artist or sound very similar to each other. There is no penalty for redundancy.

**No collaborative signal:** The system is purely content-based. It has no way to surface a song that "people like you also loved" — all recommendations are driven entirely by song attributes, not listening patterns.

**Overfit to energy:** Because energy has the highest maximum score (4.0 out of 9.5), two users with very different genre preferences but similar energy targets can end up with overlapping recommendations, which feels counterintuitive.

---

## 7. Evaluation

Three pre-built profiles were tested: **Chill Lofi**, **High-Energy Pop**, and **Deep Intense Rock**.

For **Chill Lofi**, the top results were the three lofi tracks (Midnight Coding, Library Rain, Focus Flow) followed by other low-energy, acoustic songs like Spacewalk Thoughts and Mountain Trail. This matched intuition well — those songs genuinely do sound appropriate for studying or relaxing.

For **High-Energy Pop**, Sunrise City and Gym Hero topped the list. Bass Drop (electronic, euphoric) also appeared in the top 5 because of its high energy and danceability despite the genre mismatch, which shows how strongly energy drives the score.

For **Deep Intense Rock**, Storm Runner was the only rock song in the catalog, so it ranked first by a wide margin. The remaining slots were filled by other high-energy songs (Iron Curtain, Bass Drop) — which is defensible but highlights that the catalog is too small to give meaningful rock recommendations beyond one song.

The most surprising finding was how much a genre mismatch can be overridden by a very strong energy match. A song in the wrong genre but with the exact right energy can outscore a genre match with the wrong energy level.

---

## 8. Future Work

- **Expand the catalog** significantly — at minimum 5–10 songs per genre to make recommendations within a genre meaningful.
- **Use the unused features** — tempo, valence, and danceability are already in the data and could improve precision for runners, dancers, or users with specific emotional states in mind.
- **Fuzzy genre/mood matching** — handle synonyms and alternate spellings ("hip-hop" / "hip hop", "r&b" / "rnb") and allow partial credit for related genres (e.g., lofi adjacent to ambient).
- **Diversity constraint** — cap the number of songs per artist or per genre in any top-k result to avoid redundant recommendations.
- **Improve the AI agent** — the current Gemini-powered agent already translates natural language into recommender calls, but it could also explain trade-offs ("I couldn't find a jazz song with high energy, so here's the closest match") and remember preferences across a session.
- **Add a feedback loop** — let users thumbs-up/thumbs-down results and adjust the target profile weights accordingly.

---

## 9. Personal Reflection

Building this recommender made it clear how much hidden complexity lies behind what feels like a simple feature in apps like Spotify or Apple Music. The scoring logic itself is not that complicated — four signals, a bit of math — but the quality of the results depends almost entirely on the quality and size of the catalog. With 20 songs, the system works well as a demonstration but quickly runs out of meaningful variety.

Something unexpected was how strongly the Gaussian energy score dominated the output. I initially assumed genre and mood matching would be the most important signals, but energy proximity's higher weight means two very different-sounding songs can end up with nearly identical scores if they share the same energy level.

This project changed the way I think about music apps. What looks like "the algorithm knows me" is really a combination of a massive catalog, implicit feedback from listening history, and collaborative filtering from millions of users — none of which exist in a content-only system like this. The agentic AI layer was a step toward making the interface feel smarter, letting users describe what they want in plain language instead of filling out a form, but the recommendations are only as good as the underlying scorer and data.
