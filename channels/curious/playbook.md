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

### RULE: every video mixes AI pictures and 2D animation

- **AI pictures** where people must *recognise the real thing* (the escalator, the shoe,
  the person doing it). Make them with the pictures step: candidates from several free
  models, Claude looks and picks the best, then places arrows/rings on what is really there.
- **2D animation** (`"anim": "anims/<name>.html"`) where something must be *explained*:
  a mechanism, a cross-section, a number or comparison, a before/after.
- At least **2 animated scenes** per video, never 2 animated scenes in a row, and the
  first scene (hook) is always a picture.
- Reuse animations from `anims/` when they fit (with `anim_params`); write a new one when
  the topic needs it. Keep the top fifth and the lower third calm (titles and captions).

### Calls to action (smart, never greedy)

- At most one ask per video, in the last line, and it must offer something:
  "Comment NEXT for one more everyday thing we all get wrong",
  "Send this to the friend who does this", "Part 2 tomorrow: the other escalator myth".
- Never "like and subscribe", never begging, never fake urgency.

### Hook A/B test (running)

Two hook styles alternate by date, and the job records `"hook_style"`:
- **Even dates → `myth`**: break a belief head-on. "It's NOT a shoe cleaner." / "Shoe cleaner NAHI hai."
- **Odd dates → `question`**: an open question about the thing. "Why does every escalator have this brush?" /
  "Har escalator pe ye brush kyun hota hai?"
The Sunday review compares them (views at 24 h, average watch, shares). Once each style has
5+ videos and one leads by 25%+, write `Hook winner: <style>` in Learnings and use it 5 days out
of 7 (keep the other 2 as a check).

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
| Search phrases | Every job has `keywords`: 2–3 plain phrases per language that people actually type into search ("microwave door mesh", "why microwave door has holes"). Main one first. Hindi page: Hinglish phrases plus one English phrase, since many people search in English. Instagram and YouTube now rank on these words, not on hashtags |
| Title (YouTube) | The hook, under 60 characters, ends with #shorts, and contains the main search phrase |
| Caption (IG/FB) | Line 1 = the hook as a question that contains the main search phrase in plain words. Line 2 = the short answer in one sentence, using the other search phrases naturally. Line 3 = a comment bait ("Would you last 3 days?"). Then sources, "AI visuals", and 3–5 hashtags. No "comment X to get Y" DM bait |
| On-screen text | The hook headline names the topic in plain words (MICROWAVE MESH, not just THIS THING) so Instagram can read what the video is about |
| Hashtags | 3–5, always relevant: `#ohthatswhy` + 1–2 topic tags (#escalator) + 1–2 from `data/trends.json → hashtags` **only if they fit this video**. Never generic spam (#viral #fyp #trending), never off-topic trending tags |
| Tagging | Only accounts that are genuinely in or about the video (a brand whose product it is, a source). Never random or famous accounts for reach: that is spam and gets pages restricted |
| Stories | Every Reel is also posted to Instagram Stories automatically |
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

- 2026-11-08: Week 1 (escalator, mesh; fireworks went live tonight, no numbers yet). English 4,945 views vs Hinglish 175 on the same pictures and topics, so the gap is the language/account, not the topic. Keep both until 10 videos each, then decide.
- 2026-11-08: Hinglish YouTube shows 0 views on both videos while public (escalator-hi fell 1 → 0). Change: check the HI YouTube channel settings (audience/"made for kids", restrictions, Shorts eligibility) before the next HI upload.
- 2026-11-08: Instagram carried escalator-en (2,128 views, 8 shares, 18.0 s avg watch = 42% of 43 s); its YouTube woke up late (198 views at 32 h → 1,052 at 44 h). Change: judge YouTube at 72 h, not 24 h.
- 2026-11-08: Mesh-en (question hook) had our fastest YouTube start (1,166 views in 15 h, 28 likes) but weaker Instagram hold (11.7 s avg, 29%). Hook A/B: 1 myth vs 1 question with data, far from 5 each; no winner. Fireworks (myth, Diwali-timed search topic) is our first search-driven pick to compare against our own picks.
- 2026-11-08: Data gaps: Facebook returns no metrics for any video, HI Instagram comments fail (400), posting times drifted (16:32, 20:52, 18:53 vs 19:00). Change: fix the Facebook metrics read and post closer to 19:00 so slot comparisons hold.
