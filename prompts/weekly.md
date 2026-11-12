# Sunday 8:00 PM IST — weekly learnings (both pages)

You run two video pages for Prashant from the GitHub repo `prashant8895/viral-factory`.
Work unattended.

1. Pull the repo. Dispatch "Metrics" first and wait for it (cron runs start hours late). Read
   `metrics/report.md` and `metrics/insights.json` (made automatically after every metrics
   pull), `metrics/history.csv`, `state/`, and each `channels/<page>/playbook.md`.
   English page only (Hindi paused 2026-11-12). The hook test is closed: every video uses
   a curiosity question (`curiosity`, earlier `ever-wondered`); compare instead old (Kokoro voice, photo pictures) vs new (Gemini voice,
   illustrations) using `voice` and `picture_style` in insights `groups`.
2. Per page, for each video from the last 7 days: views at ~24 h and ~72 h per platform,
   plus likes, shares, saves and average watch time where present.
3. Compare by bucket, hook style, length and platform (drama: also arc vs standalone, and
   which characters were in the top episodes). Find what the top 2 and bottom 2 share.
   Note YouTube videos still "private" (audit pending).
3b. (Closed 2026-11-12, kept for history) Hook A/B: compare `myth` vs `question` (from `state/*.json` `hook_style`): median views at
   24 h, average watch, shares per 1k views, per language. When each has 5+ videos and one leads
   by 25%+, write `Hook winner: <style>` in Learnings. Also note which search-driven or viewer-asked
   topics beat our own picks.
4. Append 3–5 dated lines to each page's "Learnings" section: what we saw, what we change.
   Change other sections only if Prashant agreed in a Morning Slate note.
5. Commit and push. Push-notify Prashant with each page's biggest learning and total views.
