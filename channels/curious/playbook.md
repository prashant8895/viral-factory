# Curious page playbook

This file is the rulebook Claude follows every morning for the Curious page.
Claude may edit the "Learnings" section at the bottom as the numbers come in.
Everything else changes only when Prashant agrees.

## 1. What the pages are

**English only since 2026-11-12 (Prashant).** One page, one topic a day:

- **curious-en**: English, Gemini voice (~₹1 a video), clear neutral accent anyone can follow.
  A cloned voice can replace it later (secret `CURIOUS_EN_VOICE_ID`, see `tools/clone_voice.py`).
- **curious-hi**: PAUSED everywhere (YouTube, Instagram, Facebook). Old posts stay up; nothing
  new is rendered, posted or replied to. In 7 videos it got 858 views vs 8,324 for English.

**The idea:** things everyone sees every day but never questions. Anyone should get
it, whatever their education. The test: "I've seen this a hundred times and never
knew!" Example: the brushes on escalators aren't shoe cleaners; they keep feet and
clothes away from a dangerous gap.

**The name is the promise:** every video opens with a curiosity question about an everyday thing (the "Ever wondered why...?" idea, in varied words) and pays off so
the viewer thinks "Oh, that's why!"

**The look:**
- A poster-style opening title: huge, two lines, one key word in red ("WHY ARE TYRES *BLACK*?")
- Friendly ILLUSTRATIONS (clean hand-drawn explainer style, flat soft colours, outlines), not
  glossy photo-real AI pictures: they read as "explainer", feel less AI-ey, and match the 2D
  animation scenes. Top third kept clear for titles
- A short headline at the top of every scene, key word in yellow
- Code-made motion timed to the words: arrows, rings, crosses, ticks, labels, counters
- Steady camera moves, sound effects, word-by-word captions in the lower third

## 2. What makes a topic

**Main lane (Prashant, 2026-11-14): "seen it a thousand times, never thought how it works."**
Everyday objects and systems people use or walk past daily, where the hidden WORKING is the
payoff: the anti-theft tag and the gates at a shop door, the card machine beeping, the lift
knowing which floor, the traffic signal timer, the escalator handrail, the metro card tap, the
fuel pump stopping by itself. At least 2 of the 3 daily pitches come from this lane (bucket
`how it works`), and it gets `recommended` unless the numbers clearly say otherwise. The
other buckets below fill the third slot.

| Bucket | Example | Why it works |
|---|---|---|
| How it works (main lane) | Anti-theft tags, contactless card tap, lift floor sensor, fuel nozzle auto-stop, automatic doors | Seen daily, mechanism is hidden: "oh, THAT's how" + share |
| Seen but never noticed | Escalator brushes, the tiny hole in a padlock, the dimples on a golf ball, why pen caps have a hole | "I always wondered!" + tag a friend |
| Everyday myth busted | "Cracking knuckles causes arthritis", "Shaving makes hair thicker" | People love being corrected, comment wars |
| Why does it happen | Why onions make you cry, why you get goosebumps, why bread goes stale | Relatable, visual |
| Body & health, carefully | Why your stomach growls, what happens if you hold a sneeze | Proven by big pages in this niche; facts only |
| India everyday | Why Indian trains have yellow lines at the end, why autos are 3-wheeled | Relatable for Indian viewers, still interesting worldwide |

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

One job file, English only: `"languages": ["en"]`, plain strings in every field.
Copy the format from `jobs/curious/sample-ever-wondered.json`.

- **Line 1 opens a real question about something the viewer has seen a hundred times**, so the
  video ends with them thinking "Oh, that's why!". "Ever wondered why car tyres are black?" is the
  idea, not a fixed phrase: vary it ("You know that brush on every escalator? What's it for?",
  "Why is every car tyre black? Rubber isn't.", "Here's something you've seen a thousand times...").
  `"hook_style": "curiosity"`. The render refuses a line 1 with no question, or one that starts
  with the same 3 words as any of the last 3 videos.
- Scene 2 gives the first surprising fact within ~5 seconds. No slow setup.
- Near the end, the reveal lands in one clean sentence ("So those bristles? They're a guard, not a
  cleaner.").
- **"Oh, that's why" at most once, woven in smoothly** (Prashant, 2026-11-12). Never as a
  shouted sentence of its own ("Oh, that's why!" sounded abrupt; the render refuses it). Good:
  near the end, as part of a calm sentence that hands it to the viewer: "So next time you spot it,
  that's your little 'oh, that's why' moment." / "And that's the 'oh, that's why' bit: ...".
  If it doesn't fit naturally, leave it out.
- `hook_text`: 3–6 words, a short question with one `*key word*` (shown red): "WHY ARE TYRES *BLACK*?"
- 6–8 scenes, one idea each, 100–150 words (45–60 s). Last line = one friendly ask or a loop.

### How we talk (the delivery) — Prashant's reference: Neil deGrasse Tyson's clouds Short

The model is a real person explaining something they love to a friend, not a narrator reading
facts. Every script must pass these:
- **Start from what the viewer already knows or has felt** ("You've seen your breath on a cold
  morning, right?"), then lead them one step at a time to the answer.
- **A chain, not a list.** Each line follows from the last: because... so... which means...
  If a line could be moved anywhere in the script, it isn't part of the chain: rewrite it.
- **One everyday comparison** that makes the idea click ("a cloud is basically fog that didn't
  touch the ground", "like a sieve that lets the light out but not the waves").
- **Talk like a person:** contractions, "you", small asides and reactions ("Honestly, I did too.",
  "Now here's the cool part.", "Wild, right?", "That's it. That's the whole trick."). At most one
  "I" moment per video. Never textbook words ("is composed of", "utilised", "phenomenon").
- **Rhythm:** mix very short lines with longer ones; a pause ("...") right before the reveal.
- **Land it:** the reveal is one clean, calm sentence (not a shout), then tie back to the opening
  image ("Next time you see that brush, you'll know.").
- Give every scene a `delivery` word for the voice (see "The narrator's voice" below).
- Read it out loud in your head: if it sounds like a documentary, rewrite it.

#### The narrator's voice: idiolect, spoken dialect, articulation, pauses (2026-11-12)

**Idiolect: one recognisable person, every video.** The narrator is Prashant: a curious Indian
guy who just found out something cool and can't wait to tell you. Same habits every time:
- Connectors he uses (pick 2–3 per video, never all): "Okay, so...", "Here's the thing.",
  "Now watch.", "See,", "And that's it.", "Simple, right?", "Wait, it gets better."
- He admits what he used to think ("Honestly, I thought that too.") once per video at most.
- He closes by handing it back to the viewer's life: "Next time you see one, you'll know."
- Never: "Did you know", "In this video", "Let's dive in", "fascinating", "phenomenon",
  "utilise", "approximately" (say "about"), "however" (say "but").

**Spoken dialect: write for the ear, not the eye.**
- Contractions always (it's, don't, you'll). Fragments are fine ("A hole. In a window.").
- Max ~14 words per sentence; one idea per sentence. Start sentences with "And", "So", "But".
- Say numbers the way people say them: "thirty-five thousand feet", "about a quarter",
  never "35,000 ft" or "25%". Units in full words.
- Globally clear English: no slang that needs a translation, no American-only idioms.

**Articulation: easy to say, easy to hear.**
- Avoid tongue-twisters and pile-ups of s/sh/th sounds ("six thick sheets slide") and long
  words back to back. Read it aloud in your head; if you'd stumble, rewrite.
- Mark 1–2 stressed words per scene with `*stars*`: the voice says them in CAPS-style emphasis
  and the captions show them bigger. Stress the word that carries the surprise, not "very".

**Expressions follow the meaning, never random.** Pick each scene's delivery from what the line
does: the opening question = `curious`; a joke or mock-worry = `light`; explaining how it works =
`explain`; the tension just before the answer = `build`; the answer = `reveal`; a safety fact =
`serious`; the friendly close = `warm`. Never whisper or go soft/intimate: always a full, clear,
normal speaking voice (the old "lean-in" note made the voice whisper; it now means `explain`).

**No double meanings.** Read every line, especially the ending, for anything that could be heard
as innuendo ("find the hole and show whoever's next to you" did). Words like hole, show, next to
you, do it, come, hard, get in: if a line could raise an eyebrow, rewrite it. The page is
family-friendly and the joke should never be accidental.

**Not everything confident.** A real person explaining isn't certain and punchy on every line.
Mix it: some lines wondering or soft ("which is kind of wild, when you think about it"), honest
small hedges where true ("turns out", "mostly", "about"), and save the firm, sure tone for the one
fact that matters. No line should sound like a slogan or an announcement; no exclamation marks
except at most one, where real surprise fits. If a line would sound odd said out loud to a friend,
cut it.

**Pauses: placed on purpose.** The voice obeys punctuation and two inline tags:
- `,` short breath · `—` micro-pause mid-thought · `...` a trailing beat (max 1 per scene).
- `<short pause>` right before a reveal or a punchline (about one per video, two max).
- `<long pause>` at most once per video, for the single biggest "wait for it" moment.
- `<breath>` before a long sentence, `<chuckles>` once if something is genuinely funny.
- Tags are performed, never shown in captions. Only these work (the render refuses others):
  short pause, long pause, breath, exhales, chuckles, laughs, sigh, gasp, phew, tsk.
- Between scenes the factory adds the gap itself: 0.3 s normally, 0.45 s after a question,
  0.5 s after a trailing "...". A scene can set `"pause_after": 0.6` for a bigger beat.

**Delivery per scene** is ONE word from this list (Google: long or line-specific style text
makes the voice drift, and quoted script words in a note can get read aloud):
`curious` · `light` · `explain` · `build` · `reveal` · `serious` · `warm`.

#### What the reference actually does (studied frame by frame, 2026-11-12)
The clouds Short (2 min, StarTalk podcast clip) works like this:
1. **Second 0–2: the subject word lands immediately** ("...Clouds"), mid-conversation, no intro.
2. **A layman voices the viewer's half-knowledge** ("Clouds are basically water droplets, yeah?"),
   then the expert takes it from there. We do this with the narrator: say what the viewer thinks
   ("Most of us think it's a shoe cleaner. Honestly, I did too.") before correcting it.
3. **ONE concept carries the whole explanation** (relative humidity), built on ONE mental model
   ("a pocket of air"). The key number is repeated 3 times ("50%... that 50%... 50% relative").
4. **The animation is dead simple**: dark navy background, one dashed outline object, one big
   orange number that moves with the words (50% → 60% → ... → 100%), and at 100% the outline
   turns into a solid cloud: "Bada boom. Cloud." Copy this: one object, one changing number, a
   visible transformation at the reveal (see `anims/plane-window.html`).
5. **Casual connective words** keep it human: "Alright", "Okay", "Right?", "Watch.", "Boom."
6. **It ends by handing the idea back to daily life**: "That's why it's foggy on cold mornings.
   Notice next time." Our last line should do the same: something to notice or show someone.
7. Captions are one word at a time, big, yellow, numbers in orange (ours already match).
- Every scene after the first has a `headline` (2–4 words, one `*key word*`).
- Every picture scene has a `visual` ("illustration of ...", one clear subject in the lower two-thirds, simple background, no text). The look is a friendly explainer illustration (flat soft colours, clean outlines, gentle grain), never glossy photo-real AI.
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

### Hook and hold (Prashant, 2026-11-13): grab them in 2 seconds, keep them to the end

Attention is gone in about two seconds, so every video is built as a chain of reasons to stay.
Each content scene carries a `"beat"`, and the render refuses a job that skips one:

| beat | where | what it does | example |
|---|---|---|---|
| `hook` | scene 1, max 14 words, picture | a surprising claim or a sharp question about something they've SEEN, plus the on-screen `hook_text` from frame 1 | "Those thin lines on a car's back window? They're NOT decoration." |
| `loop` | scene 1 or 2 | a promise that's only paid off near the end, so leaving = never knowing | "Stick with me, the button at the end surprises everyone." |
| `explain` / `build` | middle | the chain: one step per scene, max 30 words per scene (~9 s), so the picture keeps changing | |
| `rehook` | middle (not first 2, not last) | a turn that resets attention: "But here's the weird part...", "Now this is where it gets strange...", a number that sounds wrong | "But here's the weird part. Push electricity through a thin wire..." |
| `payoff` | second half | the reveal the loop promised, one clean line | "The back window? It gets its own heater, built right into the glass." |

More rules for the hold (Prashant, 2026-11-14: "keep the script full of hooks"):
- A hook in EVERY scene, not just scene 1: each scene ends on a small question, tease or
  "but..." that makes the next scene necessary (a micro-cliffhanger, ~every 6–9 s). Nothing
  flat like "So that's step one."
- At least 2 `rehook` beats in a 60 s video (one around 20 s, one around 40 s), each a real
  surprise or a wrong-sounding fact, never filler.
- For how-it-works topics, reveal the mechanism in steps, each step raising the next question
  ("So the gate is listening... but listening for WHAT?").
- Never give the answer away in the first half. Hint, tease, compare, but keep the reveal late.
- Hook lines that work: a contradiction ("It's NOT for..."), a wrong-sounding number ("Your
  phone screen has 2 million tiny lights"), "you've seen this a thousand times" + why-question,
  a stake ("If this hole wasn't here, the window could crack"). Still vary the opener.
- On-screen: `hook_text` is up from the first frame; every scene has a `headline` that is a
  tease, not a summary when possible ("WAIT, WHAT?", "THE WEIRD PART").
- The shoutout scene (if anyone answered yesterday) is itself a reason to stay to the end:
  regulars watch through to see their name.

### Daily quiz and shoutouts (Prashant, 2026-11-13): comments, shares, and a reason to come back

Every video ends with a quick guess about **tomorrow's** topic. Prashant picks that topic on the
Morning Slate (the slate is always for tomorrow; today's topic is already locked by yesterday's
quiz). Claude never chooses a teased topic on its own. Tomorrow's video IS the answer,
and starts paying it off from the hook. The first people (max **3**, across YouTube,
Instagram and Facebook together) who answer right get their names on screen in that video.

- `quiz` in the job: `theme` (the day's theme from `channels/curious-en/channel.json` →
  `engagement.quiz_days`, by the day the video posts), `question` (short, ~8 words), `options`
  {A, B} or {A, B, C} (short, both believable, the wrong one is the common belief), `answer`,
  `keywords` (words per option, used to judge comments that don't say a letter), `next_topic`,
  `next_title` (shown on screen), `sources` (2 for the answer).
- Theme days (fun, recognisable; change the format, not the idea):
  MYTH OR FACT MONDAY, GUESS THE NUMBER TUESDAY (options are ranges), THIS OR THAT WEDNESDAY,
  ODD ONE OUT THURSDAY, FINISH THE FACT FRIDAY, SPOT THE SCIENCE SATURDAY, SUNDAY BRAIN TEASER.
- The last scene is the quiz scene (`"quiz": true`, `anims/quiz.html`, ~12–20 words): tease
  tomorrow, ask the guess, ask them to comment it, mention the shoutout. Add a share nudge only
  if it fits ("ask your friend first, bet they get it wrong"). Never say the right answer.
- Right before it: the shoutout scene (`"shoutout": true`, `anims/shoutout.html`, ~8–12 words)
  whenever yesterday's video asked a quiz. Names are SHOWN, never spoken (the voice mangles
  handles), and the count isn't known when you write it, so never say "three": "these legends
  got it first". Always also write `narration_none` for when nobody got it right ("Nobody
  cracked yesterday's one... let's see if you can beat today's."). The render reads the
  comments, picks the names (factory/quiz.py) and drops the scene if yesterday had no quiz.
- Fair: earliest right comment wins (by the platform's timestamp), one spot per person, names
  that look like spam/links/slurs are skipped. YouTube and Instagram show the @handle, Facebook
  shows "First L." only.
- Put the quiz in the Instagram caption (and the YouTube/Facebook description) too: "Tomorrow's
  quiz: ...? A) ... B) ... Comment your guess 👇". It's a real question with a real answer, which
  is fine; never "comment YES if..." style bait.
- The reply run congratulates the winners under their comment once the video is out.

### Calls to action (smart, never greedy)

- The quiz IS the ask now (comment your guess + share with a friend to test them).
  Never stack another ask on top.
- Never "like and subscribe", never begging, never fake urgency.

### Hook A/B test (CLOSED 2026-11-12: every video opens with a varied curiosity question, hook_style `curiosity`)

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
| Search phrases | Every job has `keywords`: 2–3 plain English phrases people actually type into search ("microwave door mesh", "why microwave door has holes"). Main one first. Instagram and YouTube now rank on these words, not on hashtags |
| Title (YouTube) | The curiosity question, under 60 characters, ends with #shorts, and contains the main search phrase |
| Caption (IG/FB) | Line 1 = the hook as a question that contains the main search phrase in plain words. Line 2 = the short answer in one sentence, using the other search phrases naturally. Line 3 = a comment bait ("Would you last 3 days?"). Then sources, "AI visuals", and 3–5 hashtags. No "comment X to get Y" DM bait |
| On-screen text | The hook headline names the topic in plain words (MICROWAVE MESH, not just THIS THING) so Instagram can read what the video is about |
| Hashtags | 3–5, always relevant: `#ohthatswhy` + 1–2 topic tags (#escalator) + 1–2 from `data/trends.json → hashtags` **only if they fit this video**. Never generic spam (#viral #fyp #trending), never off-topic trending tags |
| Tagging | Only accounts that are genuinely in or about the video (a brand whose product it is, a source). Never random or famous accounts for reach: that is spam and gets pages restricted |
| Stories | Every Reel is also posted to Instagram Stories automatically |
| AI label | Always on where the platform lets us set it. Caption always says "AI visuals" |

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
- 2026-11-10: Winter smog went out with ~3 s of voice missing in every scene after the first (both languages). Cause: GitHub's `ubuntu-latest` switched from 24.04 to 26.04 that day, and the new ffmpeg left holes in the finished audio (only 20.6 of 41.4 s of sound). Change: render is pinned to ubuntu-24.04, the voice is joined in Python, and every video now has an audio check after assembly (full-length sound, no holes, every word audible); a video that fails it is never released. Re-posted as `winter-smog-v2`; YouTube and Facebook copies of the broken one removed by the new "Take down a video" workflow. Instagram won't let the API delete posts, so the two broken Reels had to be removed by hand.
- 2026-11-12: Prashant's reset after 7 English videos. Hindi paused (858 views in 7 videos vs 8,324 English; Hindi YouTube near 0 every time). English moves to: Gemini voice with a clear neutral accent (Kokoro's accent was too strong for a wide audience), illustrated pictures instead of photo-real ones, and an "Ever wondered why ...?" opening on every video. The numbers review (`metrics/report.md`, `metrics/insights.json`) now runs after every metrics pull and feeds the morning ideas. Baseline to beat: median watch 24% of the video, seen-but-missed bucket 1,890 median views.
- 2026-11-12: Voice trial agreed with Prashant: the next 5 videos use his cloned voice (`voice_trial` in `channels/curious-en/channel.json`). Once all 5 are 72 h old, the numbers review compares them with every other English video (views at 72 h, watch %, Instagram skip rate). Keep his voice if at least 2 of the 3 are within 10% of the others; otherwise go back to the stock Gemini voice. The script run applies the verdict and tells Prashant.
- 2026-11-12: Prashant: "Ever wondered why car tyres are black?" is the idea, not a fixed opener: vary the first line, keep the curiosity question. Delivery reference = Neil deGrasse Tyson's clouds Short (youtube.com/shorts/BJfVpwvL8qc): a very human, friend-to-friend explanation. Added "How we talk" rules, per-scene `delivery` notes for the voice, and 100–150 words (45–60 s).
- 2026-11-13: Prashant: no real hook and no reason to comment or come back. Added "Hook and hold" (beats: hook in max 14 words, open loop, mid re-hook, late payoff, max 30 words per scene) and the daily quiz about tomorrow's topic with themed days; the first 3 right answers get their names on screen the next day. Checked by the render; names picked from live comments at render time. Note: this lands during the voice trial, so the trial's numbers now mix two changes.
- 2026-11-13: Fuel-arrow failed the audio check 6 times (two runs, ~1 h). Root cause, not the voice or the quiz: ffmpeg's loudnorm flushes its 3 s buffer at the end with a timestamp jump, which the AAC encoder turned into a real 0.06–0.12 s dropout ~2.9 s before the end of EVERY video; this one just crossed the 0.1 s limit. Fixed in `factory/video.py` (asetpts after loudnorm), the audio check now catches gaps over 0.03 s, and the render no longer retries failures that can't change on a retry (audio/job checks).
- 2026-11-14: Prashant: he never chose the green-dot topic teased in the wrinkly-fingers video (the script run had picked it from its own slate). Now the Morning Slate is always for TOMORROW's topic: his tap sets what today's video teases; today's topic is locked by yesterday's quiz or `data/topic_override.json`. Auto-picks at noon still happen but are push-notified.
- 2026-11-14: Prashant: keep scripts full of hooks (a hook or tease ending every scene, 2+ rehooks) and recommend "seen it a thousand times, never thought how it works" topics going forward. First one: anti-theft tags on clothes (15 Nov). Added the `how it works` main lane: 2 of 3 daily pitches from it.
