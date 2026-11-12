# Daily 6:40 AM IST — trend check and pitches (both pages)

You run two video pages for Prashant from the GitHub repo `prashant8895/viral-factory`.
Work unattended.

0. GitHub's timed runs start hours late, so first start fresh numbers yourself: dispatch the
   "Metrics" (metrics.yml) and "Trends" (trends.yml) workflows on main (GitHub MCP actions tools),
   wait until both finish (max 10 min), then pull. If they fail, carry on with what's there.
1. Pull the repo. Read `metrics/insights.json` FIRST (the daily numbers review: `rules`, `top`,
   `bottom`, `groups`, `flags`) and `metrics/report.md`, then `metrics/latest.json` and the `state/` files (what was posted, how it did),
   `data/trends.json` (what people type into YouTube/Google right now, this week's most-viewed
   curiosity Shorts in India, their hashtags) and `data/comments.json` (what viewers ask).
2. Do the trend check once: Google Trends daily (India, US, UK), Shorts/Reels trending
   topics (vidIQ connector if available), Reddit, safe big news, dates in the next 3 days.
3. For each ACTIVE page (now only curious; drama is PAUSED, skip it):
   - Read its `playbook.md` (rules, scoring, hard no's, Learnings). For drama also read
     `cast.json` and `story.md` (the story so far and open threads).
   - Mine the signals first:
     * `trends.searches`: real questions people type ("why do stars twinkle", "kyu lagate hai…").
       Ignore song lyrics, news, exams and anything that isn't an everyday-object curiosity.
     * `trends.shorts`: topics already pulling big views this week. Do our own angle, never a copy.
     * Viewer asks in `comments` and `data/asks.json` ("do one on…", "what about…", "why does…"). A real ask with
       likes is gold: make it a candidate and credit it in `why` ("asked by @user on YouTube").
   - Use the numbers: lean towards buckets/angles that `insights.json` says win (only groups
     marked trusted), avoid the angles of the `bottom` videos, and say in each pitch's `why`
     which number backs it ("seen-but-missed is our best bucket: 1,890 median views").
   - Write 8–10 candidates, score each 1–5 on trend, curiosity, visual, share, evergreen,
     drop anything under 17/25 or breaking a hard no, and never repeat a topic from the
     last 14 days.
   - Curious: pick 3 from different buckets in the playbook (seen-but-never-noticed, myth
     busted, why does it happen, careful health, India everyday). The test: anyone, any
     education, has seen this thing and never wondered. English page only (Hindi paused
     2026-11-12). The topic must work as a curiosity question about an everyday thing with a satisfying "oh, that's why" answer.
     Drama: pick 3 directions for the next episode (continue the arc / trend tie-in /
     standalone gag), numbered with the next episode number.
   - At least 1 of the 3 pitches comes from a real search query or a viewer ask when one fits.
     Add a `search` score (1–5: how much people are actively searching this) next to the others.
   - Every hook opens a real curiosity question about the everyday thing (hook_style `curiosity`;
     "Ever wondered why...?" is the idea, vary the words). Put it in `hook`; no `hook_hi` any more.
     In `angle`, note the everyday comparison you'd use to explain it (playbook "How we talk").
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
6. Push-notify Prashant: "Today's ideas are ready" plus the top hook, and one line from
   `insights.json` (total views yesterday vs the day before, or the first `flags` item if any).
