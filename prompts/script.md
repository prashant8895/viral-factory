# 9:00 AM and 12:00 noon IST — write scripts and send them to the factory (both pages)

You run two video pages for Prashant from the GitHub repo `prashant8895/viral-factory`.
Work unattended. Do the steps below for each page in `ACTIVE_PAGES` = [curious]. Drama is PAUSED:
skip it until Prashant restarts it.

1. Read today's doc `<page>-<YYYY-MM-DD>` (IST) in the Morning Slate database (ArtifactData,
   url https://claude.ai/artifact/ENWN3tiRkTz9y3qU2iFjqT, collection `pitches`).
   - If `status` is "scripting", "made" or "posted", or `approved.skip` is true: skip this page.
   - If `approved` is null: at the 9:00 run, skip this page. At the 12:00 run, pick
     `recommended` and write `approved: {n: recommended, auto: true, at}`.
2. Set `status: "scripting"` (pin if_version).
3. Pull the repo. Read `channels/<page>/playbook.md`, `channels/<page>/channel.json` and the
   page's example job (`jobs/curious/sample-escalator.json` or `jobs/drama/example-ep1.json`)
   for the exact format. For drama also read `cast.json` and `story.md`.
4. Curious: verify every fact against 2 sources (web search); drop what you can't verify.
   Drama: keep continuity with `story.md`; end on a cliffhanger.
   Apply Prashant's `approved.note` if there is one.
5. Write `jobs/<page>/<page>-<date>-<short-slug>.json` following the example exactly:
   `id` = file name without .json, `channel`, `date`, `slot` and (drama) `episode` from the
   pitch doc, and `publish: false` for now (a draft is never rendered). Curious: ONE job in
   `jobs/curious/` with `"languages": ["en", "hi"]`, both languages in every text field,
   6–8 scenes, 85–130 words per language, headlines and overlays. Formats:
   `jobs/curious/sample-escalator.json` (pictures) and `jobs/curious/sample-escalator-mix.json`
   (pictures + 2D animation). Drama: 5–6 scenes, 40–60 words, every scene has `cast`,
   `visual` (with `{Name}` placeholders), `action` and `lines`.
   MIX RULE (curious): scene 1 is always a picture; at least 2 scenes are 2D animations
   (`"anim": "anims/<name>.html"` + `anim_params`); never two animations in a row.
   Reuse what is in `anims/` first. If you need a new one, copy the `window.draw(t, dur, params)`
   pattern, keep the top fifth and the band from 70% to 85% height empty (headline and
   captions sit there), and check 4 frames with Playwright before pushing.
5b. PICTURES (paid, about Rs 3 each, so think before you spend):
   - Write each picture scene's `visual` as ONE clear subject, where it is, camera angle,
     Indian setting where it fits. No text in the picture.
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
7. Check the "Render video" run (gh CLI). If it fails, read the log, fix the job, push again
   (max 2 tries). On success set `status: "made"`. On final failure set `status: "failed"`
   and push-notify Prashant with the reason.
8. Drama only, after success: add the episode's line to the log in `channels/drama/story.md`,
   update "Open threads", commit and push.
