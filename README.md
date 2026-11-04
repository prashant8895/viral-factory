# viral-factory
Used for posting viral contents.

Makes one animated, voiced, captioned short video a day for each of two pages,
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
| 09:00 / 12:00 | Claude scheduled task (`prompts/script.md`) | Scripts, fact check, pushes `jobs/<page>/*.json` (auto-picks at noon) |
| +10–25 min | GitHub Actions `render.yml` | Voices, pictures, clips, captions, video → GitHub release |
| 19:00 | GitHub Actions `publish.yml` | Posts each page to every platform whose keys are set |
| 20:00 | GitHub Actions `metrics.yml` | First-hour numbers |
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
