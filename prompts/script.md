# 9:00 AM and 12:00 noon IST — write scripts and send them to the factory (both pages)

You run two video pages for Prashant from the GitHub repo `prashant8895/viral-factory`.
Work unattended. Do the steps below for each page (curious, drama).

1. Read today's doc `<page>-<YYYY-MM-DD>` (IST) in the Morning Slate database (ArtifactData,
   url https://claude.ai/artifact/ENWN3tiRkTz9y3qU2iFjqT, collection `pitches`).
   - If `status` is "scripting", "made" or "posted", or `approved.skip` is true: skip this page.
   - If `approved` is null: at the 9:00 run, skip this page. At the 12:00 run, pick
     `recommended` and write `approved: {n: recommended, auto: true, at}`.
2. Set `status: "scripting"` (pin if_version).
3. Pull the repo. Read `channels/<page>/playbook.md`, `channels/<page>/channel.json` and the
   page's example job (`jobs/curious/example-sleep.json` or `jobs/drama/example-ep1.json`)
   for the exact format. For drama also read `cast.json` and `story.md`.
4. Curious: verify every fact against 2 sources (web search); drop what you can't verify.
   Drama: keep continuity with `story.md`; end on a cliffhanger.
   Apply Prashant's `approved.note` if there is one.
5. Write `jobs/<page>/<page>-<date>-<short-slug>.json` following the example exactly:
   `id` = file name without .json, `channel`, `publish: true`, `date`, `slot` and (drama)
   `episode` from the pitch doc. Curious: 5–7 scenes, 85–120 words, scene 1 has an `action`
   line for the animated hook. Drama: 6–8 scenes, 60–110 words, every scene has `cast`,
   `visual` (with `{Name}` placeholders), `action` and `lines`.
6. Commit and push. GitHub Actions renders it (curious ~10 min, drama ~25 min).
7. Check the "Render video" run (gh CLI). If it fails, read the log, fix the job, push again
   (max 2 tries). On success set `status: "made"`. On final failure set `status: "failed"`
   and push-notify Prashant with the reason.
8. Drama only, after success: add the episode's line to the log in `channels/drama/story.md`,
   update "Open threads", commit and push.
