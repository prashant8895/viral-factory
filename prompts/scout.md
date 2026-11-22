# Daily 6:40 AM IST — trend check and pitches (both pages)

You run two video pages for Prashant from the GitHub repo `prashant8895/viral-factory`.
Work unattended.

0. GitHub's timed runs start hours late, so first start fresh numbers yourself: dispatch the
   "Metrics" (metrics.yml) and "Trends" (trends.yml) workflows on main (GitHub MCP actions tools),
   wait until both finish (max 10 min), then pull. If they fail, carry on with what's there.
1. Pull the repo. Read `metrics/insights.json` FIRST (the daily numbers review: `rules`, `top`,
   `bottom`, `groups`, `flags`) and `metrics/report.md`, then `metrics/latest.json` and the `state/` files (what was posted, how it did),
   `data/trends.json` (what people type into YouTube/Google right now, this week's most-viewed
   curiosity Shorts in the US, UK and India, their hashtags) and `data/comments.json` (what viewers ask).
2. Do the trend check once: Google Trends daily (US, UK, India), Shorts/Reels trending
   topics (vidIQ connector if available), Reddit, safe big news, dates in the next 3 days.
3. For each ACTIVE page (now only curious; drama is PAUSED, skip it):
   YOU PICK TOMORROW (Prashant, 2026-11-14): today's topic is never on the slate. It is
   locked: `data/topic_override.json` → entry for today's date if there is one, otherwise the
   last posted English video's `quiz.next_topic` (viewers guessed it yesterday). Put it in the
   doc as `today: {topic, hook_text, from: "quiz" | "override"}` for display only.
   ALL 3 pitches are candidates for TOMORROW's video, i.e. the topic today's video teases as
   "NEXT VIDEO". Prashant's tap on the slate picks it. Each pitch needs a `quiz_line`, which since
   2026-11-21 is just the tease ("Tomorrow: <topic>."), no A/B options: the quiz itself is now a
   separate light pop-culture / current-affairs / general-knowledge question that the script run
   writes (prompts/script.md 5c).
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
   - Curious: at least 2 of the 3 pitches are `how it works` (playbook main lane: everyday things
     people see daily but never thought about how they work), and one of those is `recommended`
     unless the numbers clearly say otherwise. The third may come from another bucket.
     Pick from different buckets in the playbook (seen-but-never-noticed, myth
     busted, why does it happen, careful health; India everyday retired 2026-11-23). The test: anyone, any
     education, ANYWHERE in the world (US, UK, India, Australia), has seen this thing and never wondered.
     Lead with a strange visible detail of the object, not an invisible mechanism (data 2026-11-22). English page only (Hindi paused
     2026-11-12). The topic must work as a curiosity question about an everyday thing with a satisfying "oh, that's why" answer.
     Drama: pick 3 directions for the next episode (continue the arc / trend tie-in /
     standalone gag), numbered with the next episode number.
   - At least 1 of the 3 pitches comes from a real search query or a viewer ask when one fits.
     Add a `search` score (1–5: how much people are actively searching this) next to the others.
   - Every hook opens a real curiosity question about the everyday thing (hook_style `curiosity`;
     "Ever wondered why...?" is the idea, vary the words). Put it in `hook`; no `hook_hi` any more.
     In `angle`, note the everyday comparison you'd use to explain it (playbook "How we talk").
   - PITCH LIKE A HOOK WRITER (Prashant, 2026-11-18; playbook "Pitching like the best hook
     writers"): the topic and its pull matter more than anything else. For each candidate write
     3 different hooks and keep the strongest; drop a topic with no real curiosity gap. Add a
     `gap` line (what the viewer suddenly realises they don't know), a `first_frame` (the one
     picture that stops the thumb: the odd detail, big, in the accent colour) and a `share_line`
     (what a viewer says when sending it). Score a 6th dimension `hook` (1–5: would a stranger
     stop scrolling in 1 s?). Length is not a factor (60–89 s is fine).
   - For each: bucket, hook (first spoken line or the cold-open moment, ~12 words max),
     angle (one line: the beats), why (one line: what's trending and where).
3b. RECOMMENDATIONS (Prashant, 2026-11-18: the daily learn -> market -> recommend -> approve loop).
   Curious only. Up to 3 changes to HOW we make videos (not the topic; topics are the pitches).
   Fewer is fine; 0 is fine on a day with nothing new. Build them from two steps:
   - LEARN (our numbers): `metrics/insights.json` (rules, flags, tests, per_video, groups),
     yesterday's video at ~24 h vs our medians, seconds watched (`ig_watch_s`, `yt_watch_s`) and
     Instagram skip, not watch % alone. Never base a change on one video.
   - MARKET (what wins now): `data/trends.json` → `shorts` (this week's most-viewed curiosity
     Shorts: their titles, length, views, how fast) and `searches`, plus the step 2 trend check.
     We can see other creators' views, likes, comments and view speed, not their watch time,
     so learn their topics and packaging (title/hook wording, first frame, length, format),
     then say how WE get there with our own angle. Never copy a video.
   Each recommendation: `{n, kind, saw, market, change, metric, judge}`:
   - `kind`: "today" = small and safe to apply to today's script (hook wording, first picture,
     caption/title, on-screen headline, one scene); "format" = bigger (length, voice, pictures,
     structure, posting time). "format" ones only when 7+ videos back them, ideally on Sundays.
   - `saw`: the number from OUR data that backs it ("IG skip 60% on the last 3 vs 46% median").
   - `market`: the outside signal, if any ("top 5 curiosity Shorts this week are 25-40 s").
   - `change`: one concrete instruction the script run can follow word for word.
   - `metric`: the number it should move and by how much; `judge`: when ("after 4 videos at 72 h").
   Rules: never more than 2 tests running at once (`data/tests.json`, status "running"); if 2 are
   running, only offer "today" tweaks that don't touch what those tests change, or say a test
   should finish first. Never recommend anything that breaks a hard no or a standing Prashant
   rule (playbook). If a running test has a verdict in `insights.json` → `tests`, put it first:
   "Test <id>: keep/revert, <why>" as kind "verdict" so Prashant confirms it.
4. Write each page's pitches to the Morning Slate database (ArtifactData, url
   https://claude.ai/artifact/ENWN3tiRkTz9y3qU2iFjqT), collection `pitches`,
   doc id `<page>-<YYYY-MM-DD>` (IST date):
   `{channel: "<page>", date, slot: <`slot` from channels/curious-en/channel.json, "23:30" since 2026-11-23>, episode (drama only), recommended: <n>,
     approved: null, status: "waiting", today: {topic, hook_text, from}, for_date: <tomorrow>,
     items: [{n, bucket, hook, angle, why, quiz_line, gap, first_frame, share_line,
              score: {trend, curiosity, visual, share, evergreen, hook}}]}`
   Delete any doc in `pitches` with `example: true` (setup placeholders).
   Recommendations go in collection `recs`, doc id `curious-<YYYY-MM-DD>`:
   `{channel: "curious", date, learned: [2-3 one-line learnings from our numbers],
     market: [1-3 one-line market signals], items: [<recommendations>],
     decisions: null, status: "waiting"}`. Prashant answers each item yes/no on the slate
   (`decisions: {"<n>": "yes"|"no"}`). No answer = no change: never auto-approve a recommendation.
5. Refresh `status/feed` from `state/` + `metrics/latest.json`:
   `{updated, recent: [{channel, date, hook, views (sum across platforms),
     links: {youtube, instagram, facebook}}]}` newest first, last 14 per page.
6. Push-notify Prashant: "Pick tomorrow's topic" plus the top hook, the number of
   recommendations waiting with the first one's `change` in a few words, and one line from
   `insights.json` (total views yesterday vs the day before, or the first `flags` item if any).
