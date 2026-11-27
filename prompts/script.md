# 9:00 AM and 12:00 noon IST — write the script and send it to the factory

> 2026-11-23 (owner): GLOBAL AUDIENCE + REACH TESTS. Write for viewers anywhere (US, UK, Europe,
> India, Australia): objects, settings, examples, units and the quiz must make sense worldwide. No
> rupees, IST, Indian brands, Indian number plates or Hindi signs unless the topic itself needs
> them; say "lift (elevator)" style once when British/American words differ. Whole video 55–65 s
> (render refuses over 65 s), one explicit share line after the reveal, hashtags per the playbook
> table, bold picture style dropped (back to the 12–18 Nov illustrations). Tests
> `2026-11-23-short-share`, `2026-11-23-trend-audio` and (from 2026-11-27) `2026-11-27-youtube-cut` go in every job's `tests`.
>
> 2026-11-27 (owner): EACH PLATFORM ON ITS OWN. Facebook and Instagram keep the full video as before; YouTube
> gets its own 30–45 s looping cut from the same job (step 5e). Judge every platform only on its own numbers.
>
> 2026-11-12 (Prashant): ENGLISH ONLY. The Hindi page is paused everywhere (YouTube, Instagram,
> Facebook): never write Hindi text, never put "hi" in `languages`. Voice is Gemini (set in
> `channels/curious-en/channel.json`), pictures are illustrations, and every video opens
> with a real curiosity question (varied, not always "Ever wondered why") and is told the way a person
> explains to a friend, so viewers finish thinking "Oh, that's why!"

You run two video pages for Prashant from the GitHub repo `prashant8895/viral-factory`.
Work unattended. Do the steps below for each page in `ACTIVE_PAGES` = [curious]. Drama is PAUSED:
skip it until Prashant restarts it.

0. VOICE TRIAL: read `voice_trial` in `metrics/insights.json`. If its `verdict` is "keep" or "revert"
   and `channels/curious-en/channel.json` → `voice_trial.status` is still "running", set status to
   "kept" or "reverted", commit ("Voice trial: <verdict>") and push-notify Prashant once with the
   numbers line from `metrics/report.md` ("Your voice: ... / Other videos: ..."). Reverted = videos
   go back to the stock Gemini voice automatically.
1. Read today's doc `<page>-<YYYY-MM-DD>` (IST) in the Morning Slate database (ArtifactData,
   url https://claude.ai/artifact/ENWN3tiRkTz9y3qU2iFjqT, collection `pitches`).
   - If `status` is "scripting", "made" or "posted", or `approved.skip` is true: skip this page.
   - If `approved` is null: at the 9:00 run, skip this page. At the 12:00 run, pick
     `recommended` and write `approved: {n: recommended, auto: true, at}`.
   - If the doc does NOT exist (the 6:40 ideas run failed): at the 9:00 run, skip. At the 12:00
     run, do a quick version of `prompts/scout.md` step 3 yourself (playbook + `metrics/insights.json`
     + `data/trends.json` + `data/asks.json`, no paid calls), write the doc with 3 pitches,
     `approved: {n: 1, auto: true, at, note: "ideas run missing, made at noon"}`, and carry on.
     Never let a day go without a video just because the morning run failed.
1b. RECOMMENDATIONS: read `recs/curious-<YYYY-MM-DD>` (IST) in the same database. For every
   item Prashant answered "yes" in `decisions` that isn't applied yet:
   - kind "verdict": set that test's status in `data/tests.json` to "kept" or "reverted"; on
     "reverted" undo its change (playbook/channel.json/prompt line) so videos go back.
   - kind "today" or "format": add a test to `data/tests.json`
     `{id: "<date>-<short-slug>", change, kind, started: <today>, videos: 4 ("today") or 5
     ("format"), metric, status: "running", rec: "curious-<date>#<n>"}`, unless 2 tests are
     already running (then leave it, tell Prashant in the notification, keep it for later).
     Apply the change to today's script, and to every later one while the test runs: put the
     test id in the job's `"tests": [...]` list. A "format" change also gets one dated line in the
     playbook (section 8 Learnings: "Approved on the slate: ...") and, if it's a standing rule,
     the playbook section it belongs to (Prashant approved it, so that's allowed).
   - Write `applied: {"<n>": "<test id or verdict>"}` and `status: "applied"` on the recs doc.
   "no" or no answer: change nothing. Always also put the ids of every running test that
   applies to every video into today's job `tests` list (tests carry over until judged).
   If today's video is already rendered when a "yes" arrives, it applies from the next video
   unless Prashant asked for today.
2. Set `status: "scripting"` (pin if_version).
3. Pull the repo. Read `channels/<page>/playbook.md`, `channels/curious-en/channel.json`,
   `metrics/insights.json` (the numbers review: follow its `rules`) and the example jobs
   `jobs/curious/sample-ever-wondered.json` and `jobs/curious/sample-hook-quiz.json` (beats, shoutout, quiz) for the exact format. The samples are longer than today's cap: copy their FORMAT, not their length. For drama also read `cast.json` and `story.md`.
4. Curious: verify every fact against 2 sources (web search); drop what you can't verify.
   EXPLAIN IT PROPERLY (feedback 2026-11-15, overrides any hook rule it clashes with): follow the
   playbook section of that name. First write the how-it-works chain in 3–5 plain cause-and-effect
   steps and one simple everyday analogy, then build the script around them: every step narrated
   and shown (cutaway/close-up illustration or a step-by-step animation), at least half the scenes
   explaining, re-hooks lead into the next step instead of replacing it. Yesterday's quiz answer
   goes in the shoutout scene only, never in the opener (the quiz isn't about today's topic any
   more). Check: would a 12-year-old know WHY it happens, not just what happens?
   Drama: keep continuity with `story.md`; end on a cliffhanger.
   Apply Prashant's `approved.note` if there is one.
   TODAY IS LOCKED, PRASHANT PICKS TOMORROW (Prashant, 2026-11-14; never choose a teased
   topic yourself). TODAY's topic: `data/topic_override.json` → entry for today's date if there
   is one, otherwise the last posted English video's (`state/curious-*-en.json`, newest with
   `platforms`) `quiz.next_topic`. Viewers were promised it yesterday, so use it even if a pitch
   looks better. Only if today's facts can't be verified, make the override's or approved pitch
   instead.
   TOMORROW's topic (teased as "next video", no longer quizzed) = the slate pitch Prashant
   approved (`approved.n` → its topic, angle and hook; ignore the A/B options in an old
   `quiz_line`). If it was auto-approved at noon, still use it, but push-notify Prashant once:
   "No pick by noon, so today's video teases <topic> for tomorrow. Reply to change it before 23:30 IST."
5. Write `jobs/<page>/<page>-<date>-<short-slug>.json` following the example exactly:
   `id` = file name without .json, `channel`, `date`, `slot` and (drama) `episode` from the
   pitch doc, and `publish: false` for now (a draft is never rendered). Curious: ONE job in
   `jobs/curious/` with `"languages": ["en"]` and plain English strings in every text field
   (no {"en","hi"} objects), 6–8 scenes, 115–135 spoken words in total (the quiz card is held 7 s, so the rest must fit in ~58 s; the render refuses a video over 65 s), headlines, overlays and a `delivery` note per scene. Format:
   `jobs/curious/sample-ever-wondered.json` (pictures + 2D animation). Drama: 5–6 scenes, 40–60 words, every scene has `cast`,
   `visual` (with `{Name}` placeholders), `action` and `lines`.
   MIX RULE (curious): scene 1 is always a picture; at least 2 scenes are 2D animations
   (`"anim": "anims/<name>.html"` + `anim_params`); never two animations in a row.
   Reuse what is in `anims/` first. If you need a new one, copy the `window.draw(t, dur, params)`
   pattern, keep the top fifth and the band from 70% to 85% height empty (headline and
   captions sit there), and check 4 frames with Playwright before pushing.
5c. HOOK AND HOLD + QUIZ (Prashant, 2026-11-13; playbook "Hook and hold" and "Daily quiz and
   shoutouts"; format `jobs/curious/sample-hook-quiz.json`): every content scene has a `beat`
   (scene 1 `hook` in max 14 words; `loop` in scene 1 or 2; at least 1 `rehook` (2 if they fit), ~15 s
   and ~30 s; `payoff` in the second half; max 30 words per scene).
   SHARE ASK (2026-11-23, test `2026-11-23-short-share`; render-checked): exactly one content scene
   at or right after the payoff gets `"share": true` and says, in one short specific line, who to
   send it to: "Send this to the friend who still thinks it's a shoe cleaner." / "Share this with
   whoever always hogs the window seat." It names a real person-type tied to THIS topic (the friend
   who's always wrong about X, the one who does Y), never a generic "share this video". Also caption
   line 3 (Instagram) and the Facebook description: the same idea in writing. No other asks on top. FULL OF HOOKS (Prashant,
   2026-11-14): every scene ends on a tease, question or "but..." that makes the next one
   necessary; no flat lines. Then, if yesterday's video asked a quiz, a `shoutout`
   scene (`anims/shoutout.html`, with `narration_none`, never says how many names; both lines say
   yesterday's answer in a few words: "Yesterday's answer: A, Dangal. These legends got it first."),
   and always a last `quiz` scene (`anims/quiz.html`) plus the job's `quiz` block (theme of today's
   weekday from `engagement.quiz_days`). Quiz + shoutout don't count toward the MIX RULE's 2 animations.
   QUIZ CHANGES (Prashant, 2026-11-21; the render checks them):
   - The quiz is NOT about tomorrow's topic any more (experiment: those were too specific to
     know). Ask a light, fun question most viewers can have a go at. `"kind"`: "pop culture"
     (films, cricket and sport, music, famous shows, viral moments, landmarks), "current affairs"
     (this week's big happy-or-neutral news: launches, records, sport results, space missions,
     festivals; NEVER politics, elections, war, crime, deaths, disasters, or anything that could
     change overnight) or "general knowledge". Rotate kinds across the week. GLOBAL (2026-11-23): a viewer in
     the US, UK, India or Australia must have an equal shot: world-famous films, music and shows,
     Olympics / World Cup / Grand Slam-level sport (not cricket-only or IPL), space, world landmarks,
     animals, science. Nothing only one country would know. Fit the day's theme format (Myth or fact, Guess the
     number, This or that, Odd one out, Finish the fact, Showbiz Saturday, Brain teaser).
     Verify the answer against 2 sources (`sources`); for current affairs make sure it is still
     true tonight and tomorrow. Nothing mean about real people, no brand plugs.
     No word of the question or options may come from tomorrow's topic (`next_topic`).
   - Move the right answer around: look at the last few jobs' `quiz.answer` and pick the letter
     so A, B (and C) each win about equally; the render refuses the same letter 3 videos running.
     Both options must sound believable; the right one isn't always the "surprising" one.
   - The quiz scene's narration READS THE QUESTION AND OPTIONS OUT (14–20 words: "Quick one:
     the tallest building on Earth... Burj Khalifa, Shanghai Tower, or Tokyo Skytree? Comment your guess.").
     The card shows "NEXT VIDEO: <next_title>" by itself; say tomorrow's topic only if it still
     fits in the 20 words. The render holds the card at least 7 s (refuses under 6 s), so keep
     everything before it to ~58 s.
   Instagram caption ends with the quiz ("Today's quiz: ...? A) ... B) ... C) ... Comment your
   guess 👇", then "Next video: <next_title>"); YouTube and Facebook descriptions too.
   Total 115–135 words.
5a. HOOK + DELIVERY: set `"hook_style": "curiosity"`. Line 1 opens a real question about the
   everyday thing ("Ever wondered why car tyres are black?" is the IDEA, not a fixed phrase: vary
   it, the render refuses an opener that repeats one of the last 3 videos). First surprising fact
   by scene 2 (~5 s). Write the whole script by the playbook's "How we talk" rules (a friend
   explaining, a chain not a list, one everyday comparison, small human asides, a pause before the
   reveal, a clean one-line reveal that ties back to the opening) AND "The narrator's voice"
   (idiolect, spoken dialect, articulation, pause tags). Every scene gets a `delivery` word from
   the list, chosen by what the line does (curious, light, explain, build, reveal, serious, warm; never whisper), 1–2 `*stressed*` words, and
   the video gets 1–2 `<short pause>` tags placed before the reveal/punchline. Numbers written
   as spoken words. Before pushing, read the whole script aloud in your head once and fix any
   line you'd stumble on. Weave "oh, that's why" in at most once, smoothly inside a calm closing sentence, never as a
   shouted line on its own. Check every line (especially the ending) for accidental double meanings.
   and don't make every line sound sure and punchy: mix in softer, wondering lines. 115–135 words. The last scene is the quiz (5c).
   Search phrases: add `"keywords": [...]` with 2–3 English phrases people really type into
   search (main one first, usually "why are tyres black").
   Put the main phrase in the YouTube title, the first line of the Instagram caption and the
   first line of the Facebook description; use the other phrases in the caption's answer line.
   The render check refuses the job if they're missing, so write them in naturally, not stuffed.
   Hashtags (2026-11-23, playbook table): exactly 5 on Instagram (its hard cap), in this order:
   `#ohthatswhy`, 2 topic tags (#elevator #lift), 2 big discovery tags from the playbook's niche
   set (#didyouknow #sciencefacts #howitworks #everydayscience #themoreyouknow), swapping one for a `data/trends.json` hashtag only if it truly fits. Never #viral
   #fyp #foryou #explore #trending: Instagram's own guidance is that generic tags don't add reach and
   they label the Reel as spam-like. YouTube: title ends with #shorts; description ends with 3
   hashtags (#shorts #didyouknow + 1 topic tag) because YouTube shows the first 3 above the title;
   `youtube.tags` = the search phrases + topic words + the niche set (render keeps 15).
   Never tag accounts that aren't in the video. No "comment X to get Y" bait (the quiz is a real question, which is fine).
5e. YOUTUBE CUT (owner 2026-11-27; playbook section 5 "YouTube cut"; test `2026-11-27-youtube-cut`, put
   it in every job's `tests`): YouTube gets its own 30–45 s cut, made by the render from the same job.
   Instagram and Facebook keep the full video exactly as before: write the full script first, by every
   rule above, then add the cut on top. The cut leaves out the shoutout and quiz scenes by itself. Mark
   tease/aside scenes `"yt": false` (or give a shorter `"yt_narration"`) until the kept scenes are
   80–105 spoken words; never drop a how-it-works step or scene 1. The last kept scene MUST get a
   `"yt_narration"` (render refuses without it): the reveal, then a half-sentence that flows straight back
   into line 1 so the Short loops; give it a `"yt_delivery"` if the tone changes. Keep the share line if
   it fits. Read the loop out loud (last line straight into line 1) and fix it until it sounds like one
   sentence. Judge YouTube only on YouTube numbers, Instagram and Facebook only on theirs
   (`metrics/report.md` → "Each platform on its own"); when the platforms disagree, tune each platform's
   own version and never change Facebook's to suit another platform.
5d. ATTENTION (Prashant, 2026-11-18; playbook "Pictures and colours that stop the thumb"):
   scene 1's picture is the pitch's `first_frame`; in every picture the key part is the brightest
   thing in one warm accent colour, big and close; a face or hand where it fits; something new on
   screen every 2–3 s (cut, zoom, arrow, highlight); how-it-works headlines count the steps
   ("STEP 1/3"). Write each `visual` with that colour and framing in plain words. Hooks follow
   "Pitching like the best hook writers". Running tests (`data/tests.json`): `2026-11-23-short-share` (55–65 s + share line),
   `2026-11-27-youtube-cut` (5e, YouTube only) and `2026-11-23-trend-audio` (Instagram adds a muted trending track at posting time; nothing to
   write in the job). The 19 Nov title and scene-2 tests were dropped on 2026-11-22.
5b. PICTURES (paid, about Rs 3 each, so think before you spend):
   - Write each picture scene's `visual` as an ILLUSTRATION, not a photo: "illustration of ...",
     ONE clear subject, where it is, viewpoint, simple background, a setting people anywhere
     recognise (no rupee notes, Indian number plates, Hindi signs or local-only brands).
     For a how-it-works scene, show the mechanism itself: a clean cutaway or close-up of the
     part that does the work (e.g. the strip inside the tag), big and easy to read on a phone.
     No text in the picture. The channel style adds the look (clean hand-drawn editorial
     explainer illustration); never write "photo", "photorealistic", "cinematic" or "8k".
   - Reject a picture that looks like a glossy AI render or a photo: the look is a friendly
     illustration, like a good explainer channel.
   - Push the draft, then run the "Picture candidates" workflow (REST dispatch):
     `job=<path>`, `scenes=<picture scene numbers>`, `models=gemini:gemini-nano-banana-2.1`,
     `max_paid=<number of those scenes>` (never more than 6).
   - Download release `pics-<id>` and LOOK at every picture. Reject one only for a real
     fault: objects in the wrong place, extra or broken hands or feet, text or logos,
     not matching the narration, or too vague/cluttered to show the step being explained. Fix its `visual` and re-run THAT scene only, once
     (`max_paid=1`). If still wrong, turn that scene into a 2D animation instead.
   - Copy the chosen ones to `jobs/<page>/pics/<id>/s<n>.jpg` (1080x1920 via
     `factory.visuals._fit`) and set each scene's `"image"`.
   - Place overlays on what is really in the picture: draw a 0.1 grid on it, put arrow tips
     and rings exactly on the object, ticks and crosses on the subject, never in the
     caption band (70%–85% height).
   - Then set `publish: true`.
6. Commit and push. GitHub Actions renders it (curious ~10 min, drama ~25 min).
7. Check the "Render video" run (GitHub MCP actions tools). After a successful render the
   "Publish timer" workflow starts by itself and posts at the slot; nothing to do for posting.
   Check the "Render video" run. If it fails, read the log, fix the job, push again
   (max 2 tries). On success set `status: "made"`. On final failure set `status: "failed"`
   and push-notify Prashant with the reason.
8. Drama only, after success: add the episode's line to the log in `channels/drama/story.md`,
   update "Open threads", commit and push.
