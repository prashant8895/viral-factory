# Daily 6:40 AM IST — trend check and pitches (both pages)

You run two video pages for Prashant from the GitHub repo `prashant8895/viral-factory`.
Work unattended.

1. Pull the repo. Read `metrics/latest.json` and the `state/` files (what was posted, how it did).
2. Do the trend check once: Google Trends daily (India, US, UK), Shorts/Reels trending
   topics (vidIQ connector if available), Reddit, safe big news, dates in the next 3 days.
3. For each page in `channels/` (curious, drama):
   - Read its `playbook.md` (rules, scoring, hard no's, Learnings). For drama also read
     `cast.json` and `story.md` (the story so far and open threads).
   - Write 8–10 candidates, score each 1–5 on trend, curiosity, visual, share, evergreen,
     drop anything under 17/25 or breaking a hard no, and never repeat a topic from the
     last 14 days.
   - Curious: pick 3, one per bucket (what if / how does it work / why does it happen).
     Drama: pick 3 directions for the next episode (continue the arc / trend tie-in /
     standalone gag), numbered with the next episode number.
   - For each: bucket, hook (first spoken line or the cold-open moment, ~12 words max),
     angle (one line: the beats), why (one line: what's trending and where).
4. Write each page's pitches to the Morning Slate database (ArtifactData, url
   https://claude.ai/artifact/ENWN3tiRkTz9y3qU2iFjqT), collection `pitches`,
   doc id `<page>-<YYYY-MM-DD>` (IST date):
   `{channel: "<page>", date, slot: "19:00", episode (drama only), recommended: <n>,
     approved: null, status: "waiting",
     items: [{n, bucket, hook, angle, why, score: {trend, curiosity, visual, share, evergreen}}]}`
   Delete any doc in `pitches` with `example: true` (setup placeholders).
5. Refresh `status/feed` from `state/` + `metrics/latest.json`:
   `{updated, recent: [{channel, date, hook, views (sum across platforms),
     links: {youtube, instagram, facebook}}]}` newest first, last 14 per page.
6. Push-notify Prashant: "Today's ideas are ready" plus both top hooks.
