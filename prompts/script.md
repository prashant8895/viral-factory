# 9:00 AM and 12:00 noon IST — write the script and send it to the factory

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
2. Set `status: "scripting"` (pin if_version).
3. Pull the repo. Read `channels/<page>/playbook.md`, `channels/curious-en/channel.json`,
   `metrics/insights.json` (the numbers review: follow its `rules`) and the example job
   `jobs/curious/sample-ever-wondered.json` for the exact format. For drama also read `cast.json` and `story.md`.
4. Curious: verify every fact against 2 sources (web search); drop what you can't verify.
   Drama: keep continuity with `story.md`; end on a cliffhanger.
   Apply Prashant's `approved.note` if there is one.
5. Write `jobs/<page>/<page>-<date>-<short-slug>.json` following the example exactly:
   `id` = file name without .json, `channel`, `date`, `slot` and (drama) `episode` from the
   pitch doc, and `publish: false` for now (a draft is never rendered). Curious: ONE job in
   `jobs/curious/` with `"languages": ["en"]` and plain English strings in every text field
   (no {"en","hi"} objects), 6–8 scenes, 100–150 words, headlines, overlays and a `delivery` note per scene. Format:
   `jobs/curious/sample-ever-wondered.json` (pictures + 2D animation). Drama: 5–6 scenes, 40–60 words, every scene has `cast`,
   `visual` (with `{Name}` placeholders), `action` and `lines`.
   MIX RULE (curious): scene 1 is always a picture; at least 2 scenes are 2D animations
   (`"anim": "anims/<name>.html"` + `anim_params`); never two animations in a row.
   Reuse what is in `anims/` first. If you need a new one, copy the `window.draw(t, dur, params)`
   pattern, keep the top fifth and the band from 70% to 85% height empty (headline and
   captions sit there), and check 4 frames with Playwright before pushing.
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
   and don't make every line sound sure and punchy: mix in softer, wondering lines. 100–150 words. Last line = one friendly ask or loop, never pushy.
   Search phrases: add `"keywords": [...]` with 2–3 English phrases people really type into
   search (main one first, usually "why are tyres black").
   Put the main phrase in the YouTube title, the first line of the Instagram caption and the
   first line of the Facebook description; use the other phrases in the caption's answer line.
   The render check refuses the job if they're missing, so write them in naturally, not stuffed.
   Hashtags: follow the playbook table (3–5, relevant, `#ohthatswhy` first; trending tags from
   `data/trends.json` only if they genuinely fit). Never more than 5. Never tag accounts that
   aren't in the video. No "comment X to get Y" bait.
5b. PICTURES (paid, about Rs 3 each, so think before you spend):
   - Write each picture scene's `visual` as an ILLUSTRATION, not a photo: "illustration of ...",
     ONE clear subject, where it is, viewpoint, simple background, Indian setting where it fits.
     No text in the picture. The channel style adds the look (clean hand-drawn editorial
     explainer illustration); never write "photo", "photorealistic", "cinematic" or "8k".
   - Reject a picture that looks like a glossy AI render or a photo: the look is a friendly
     illustration, like a good explainer channel.
   - Push the draft, then run the "Picture candidates" workflow (REST dispatch):
     `job=<path>`, `scenes=<picture scene numbers>`, `models=gemini:gemini-nano-banana-2.1`,
     `max_paid=<number of those scenes>` (never more than 6).
   - Download release `pics-<id>` and LOOK at every picture. Reject one only for a real
     fault: objects in the wrong place, extra or broken hands or feet, text or logos,
     not matching the narration. Fix its `visual` and re-run THAT scene only, once
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
