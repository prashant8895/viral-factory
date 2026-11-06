# Curious page playbook

This file is the rulebook Claude follows every morning for the Curious page.
Claude may edit the "Learnings" section at the bottom as the numbers come in.
Everything else changes only when Prashant agrees.

## 1. What the pages are

Two pages, one topic a day, made once and voiced twice:

- **curious-en**: English (Kokoro voice, free)
- **curious-hi**: Hinglish (Gemini voice, ~₹1 a video)

Both use the same pictures, so the second language costs nothing extra. After 10
videos each, compare them and put more effort where the numbers are better.

**The idea:** things everyone sees every day but never questions. Anyone should get
it, whatever their education. The test: "I've seen this a hundred times and never
knew!" Example: the brushes on escalators aren't shoe cleaners; they keep feet and
clothes away from a dangerous gap.

**The look (all free):**
- A poster-style opening title: huge, two lines, one key word in red ("SHOE CLEANER *NAHI* HAI!")
- Realistic, dramatic AI pictures, one per line, top third kept clear for titles
- A short headline at the top of every scene, key word in yellow
- Code-made motion timed to the words: arrows, rings, crosses, ticks, labels, counters
- Steady camera moves, sound effects, word-by-word captions in the lower third

## 2. What makes a topic

| Bucket | Example | Why it works |
|---|---|---|
| Seen but never noticed | Escalator brushes, the tiny hole in a padlock, the dimples on a golf ball, why pen caps have a hole | "I always wondered!" + tag a friend |
| Everyday myth busted | "Cracking knuckles causes arthritis", "Shaving makes hair thicker" | People love being corrected, comment wars |
| Why does it happen | Why onions make you cry, why you get goosebumps, why bread goes stale | Relatable, visual |
| Body & health, carefully | Why your stomach growls, what happens if you hold a sneeze | Proven by big pages in this niche; facts only |
| India everyday | Why Indian trains have yellow lines at the end, why autos are 3-wheeled | Hinglish page gold, still interesting in English |

Rules for picking:
- It must be **seen in daily life** by most people, in India and abroad
- One surprising fact at the core, explainable in under a minute
- It must be **visual**: every line can become a strong picture
- Facts checked against 2 sources; put the sources in the caption
- Health topics: facts only, no advice beyond basic safety, no scary claims without a source

Length is an experiment: start at 40–50 s. Try 60–90 s on the strongest topics
and keep whatever the watch-time numbers favour (record it in Learnings).

## 3. The daily trend check (6:40 AM IST)

Claude looks at, in this order:

1. Google Trends daily searches: India, US, UK
2. YouTube Shorts and Instagram Reels trending topics and sounds (vidIQ if connected)
3. Reddit: r/todayilearned, r/explainlikeimfive, r/NoStupidQuestions, r/askscience
4. Big news of the day that is safe to explain (launches, sport, space, weather events)
5. Upcoming dates in the next 3 days (festivals, matches, holidays) worldwide

Every idea gets a score out of 25. Only ideas scoring 17+ get pitched.

| Score (1–5 each) | Question |
|---|---|
| Trend heat | Are lots of people searching or posting about this right now? |
| Curiosity gap | Does the hook make you need the answer? |
| Visual payoff | Is there one shot that looks amazing in 3D? |
| Share trigger | Would someone send this to a friend or tag someone? |
| Evergreen tail | Will it still get views next month? |

## 4. Script rules

One job file, both languages: `"languages": ["en", "hi"]`, and every spoken or
written field has both versions, e.g. `"narration": {"en": "...", "hi": "..."}`.
Copy the format from `jobs/curious/sample-escalator.json`.

- **Hinglish** = how young urban Indians actually talk: Hindi grammar, everyday English
  words, written in English letters ("Ye gap joote ki lace tak ko kheench sakta hai").
  Not a word-for-word translation of the English. Same facts, its own natural lines.
- Line 1 is the hook, spoken over the poster title. It names the everyday thing and
  breaks the belief ("You've been using this wrong your whole life").
- `hook_text`: 3–6 words, one `*key word*` (shown red). Hinglish versions often use NAHI / ASLI / SACH.
- 6–8 scenes, one idea each, 85–130 words per language. Last line = share prompt or loop.
- Every scene after the first has a `headline` (2–4 words, one `*key word*`).
- Every scene has a `visual` (realistic, dramatic, subject in the lower two-thirds, no text)
  and ideally one overlay timed to a spoken word (`"on"`): arrow at the thing, ring around
  the detail, cross on the myth, tick on the right way, counter on any number.
- `motion`: push (default), pull (reveal), drift_left / drift_right.
- `sfx`: boom on the hook; then one of thud, ding, riser, sparkle, pop, tick, boing, crash, whoosh.
- Mark 1–2 key words per line with `*stars*` (shown bigger, in orange).

### Hook formulas that work

- "This is what happens if you…"
- "Nobody tells you this about…"
- "There's a reason you've never seen…"
- "In 40 seconds you'll understand…"
- "This [thing] should not exist."
- "Watch what happens when…"

## 5. Posting

| Item | Rule |
|---|---|
| Frequency | 1 video a day, same video on YouTube Shorts, Instagram Reels, Facebook Reels |
| Time | 7:00 PM IST for weeks 1–2. Then test 6:30 AM IST (US evening) on alternate days |
| Title (YouTube) | The hook, under 60 characters, ends with #shorts |
| Caption (IG/FB) | Line 1 = the hook as a question. Line 2 = a comment bait ("Would you last 3 days?"). 3–5 hashtags only |
| AI label | Always on where the platform lets us set it. Caption always says "AI animation" |

## 6. Hard no's

- No real people's faces or voices. No celebrity lookalikes.
- No copyrighted characters, logos, songs or film clips.
- No medical or money advice. Facts only, no "do this".
- No tragedy-baiting (disasters, deaths in the news) for views.
- No made-up facts. If it can't be verified, it doesn't go in.
- No kids-targeted content (keeps us out of "Made for Kids" limits).

## 7. If Prashant doesn't approve

Pitches go out at 7:00 AM IST. If there's no approval by 12:00 noon IST,
Claude makes the top-scored pitch so the day is not missed.

## 8. Learnings

Claude updates this every Sunday from the metrics. Format: date, what we
saw, what we change.

- (empty — first update after week 1)
