# viral-factory
Used for posting viral contents.

Makes one animated, voiced, captioned short video a day ("Oh That's Why", English only since
2026-11-12; the Hindi page and Drama are paused),
and posts it to YouTube Shorts, Instagram Reels and Facebook Reels.

| Page | What | Animation |
|---|---|---|
| `curious` | What if / how does it work / why does it happen | First 5–8 s animated, then AI pictures with camera moves |
| `drama` | Daily soap opera: Mochi the cat, Bruno the dog, Granny, Pip | Every shot animated, same cast each episode |

## Daily flow (IST)

| Time | Who | What |
|---|---|---|
| 06:15 | GitHub Actions `metrics.yml` | Pulls views/likes/shares into `metrics/` |
| 06:40 | Claude scheduled task (`prompts/scout.md`) | Trend check, 3 pitches per page into Morning Slate |
| 07:00 | Prashant | One tap per page on Morning Slate (optional note) |
| 09:00 / 12:00 | Claude scheduled task (`prompts/script.md`) | Scripts, fact check, pushes `jobs/<page>/*.json` (auto-picks at noon; writes its own pitches if the 6:40 run failed) |
| +10–25 min | GitHub Actions `render.yml` | Voices, pictures, clips, captions, video → GitHub release |
| right after | GitHub Actions `publish-timer.yml` | Waits on a runner until the slot, then starts `publish.yml` (cron runs here start 6–9 h late) |
| 19:00 | GitHub Actions `publish.yml` | Posts each page to every platform whose keys are set |
| 20:00 | GitHub Actions `metrics.yml` → `factory/analyze.py` | Numbers, then `metrics/report.md` + `metrics/insights.json` (what to do more/less of; read by every Claude run) |
| Sun 20:00 | Claude scheduled task (`prompts/weekly.md`) | Writes learnings into each playbook |

## Pieces

- `channels/<page>/` — `channel.json` (voices, style, animation), `playbook.md` (rules);
  drama also has `cast.json`, `cast/` (reference pictures, made on first run) and `story.md`
- `factory/` — `render.py` (job → video), `publish.py`, `metrics.py`, `platforms.py`, `visuals.py`, `tts.py`, `video.py`
- `jobs/<page>/` — one JSON per video (see the `example-*` files)
- `state/` — what was rendered/posted, with post links (never double-posts)
- `tools/` — optional scripts to get YouTube and Meta keys from a laptop

## Secrets (Settings → Secrets and variables → Actions)

Shared: `POLLINATIONS_KEY` (pictures free; animation paid with Pollen on the same key), `YT_CLIENT_ID`, `YT_CLIENT_SECRET`.

Per page (prefix `CURIOUS_` or `DRAMA_`): `YT_REFRESH_TOKEN`, `META_PAGE_TOKEN`, `IG_USER_ID`, `FB_PAGE_ID`.

Variables (same screen, Variables tab): `VIDEO_MODEL` (picture → clip),
`IMAGE_EDIT_MODEL` (keeps the drama cast looking the same). Both are Pollinations model ids.

Each platform on each page switches on by itself once its secrets exist.

## Run by hand

Actions → "Render video" → Run workflow → `jobs/curious/example-sleep.json` or `jobs/drama/example-ep1.json`.
Actions → "Publish" → Run workflow → force_id to post one job now.

## When something fails

- Every picture and animation is tried 4 times (waits of 30 s, 2 min, 5 min). If one still fails,
  the whole video is tried again twice more, 10 minutes apart.
- A video that still fails is not released and not posted. Nothing half-done goes out.
- Posting retries at 19:30, 20:00 and 21:00 IST (07:00 and 07:30 for the morning slot), only
  for the platforms still missing, so nothing is posted twice.
- Failures open a GitHub issue in this repo that mentions the owner, so GitHub emails and
  notifies Prashant. The issue closes itself when a retry works.
