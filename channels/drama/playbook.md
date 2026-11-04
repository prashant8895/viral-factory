# Drama page playbook

The rulebook Claude follows every morning for the Drama page. Claude may edit
"Learnings" at the bottom and the episode log in `story.md`. Everything else
changes only when Prashant agrees.

## 1. What the page is

A daily animated soap opera about one house: Mochi the cat, Bruno the dog,
Granny and Pip the mouse (see `cast.json`). Every video is one episode of the
same story, so people follow the characters and come back tomorrow.

- Fully animated: every shot is a 5-second AI clip of the cast acting
- The cast always looks the same (made from their reference pictures in `cast/`)
- A narrator plus character voices, with big word-by-word captions
- 25 to 40 seconds, vertical 9:16
- Title format: "Mochi finds out the cake is gone 😾 | Ep 4"

## 2. What makes an episode spread

| Ingredient | Rule |
|---|---|
| Cold open | Frame 1 is the most dramatic moment of the episode (a gasp, a crash, a stare). Then "Earlier that day…" if needed |
| One conflict | One problem per episode: a stolen snack, a new pet, a broken vase, a betrayal |
| Big faces | Every shot shows a clear emotion: shock, smugness, tears, rage. That's what makes it funny |
| Short lines | Characters speak 3–8 words at a time. Narrator only to set up or twist |
| Twist | Something flips in the last third (Bruno is innocent, Pip was behind it all) |
| Cliffhanger | The last shot sets up tomorrow ("But someone was watching…"). It doesn't resolve |
| Recap-free | Each episode must make sense alone. A new viewer needs no context |

Episodes can be standalone gags (about 1 in 3) or move the bigger story arc
along (2 in 3). Arcs last 5–10 episodes.

## 3. The daily pitch (6:40 AM IST)

Claude reads `story.md` (what happened so far, open threads) and checks trends:
holidays and festivals in the next 3 days worldwide, viral pet moments, food
trends, big sport moments a cat could react to. Then it pitches 3 directions for
today's episode, for example:

- Continue the arc ("Bruno tries to win Mochi back with a dead leaf")
- Trend tie-in ("Diwali: Mochi vs the firecrackers")
- Standalone gag ("Granny buys a Roomba")

Same 25-point score as the Curious page, but "Curiosity" means "Do I need to
know what happens next?".

## 4. Script rules

- 6–8 scenes, each 4–6 seconds of speech (about 10–14 words), one clip each
- 60–110 spoken words in total
- Each scene lists `cast` (who is in the shot), `visual` (the picture, with
  `{Mochi}` style placeholders) and `action` (what moves in the clip: one
  clear motion, e.g. "Mochi slowly turns her head toward the camera, eyes narrowing")
- Lines: `{"speaker": "Mochi", "text": "Who. Ate. My. Cake."}`
- No real brands, no real people, no copyrighted characters or songs
- No cruelty: nobody gets hurt. Slapstick stays cartoon-safe
- Not "made for kids": the humour is aimed at adults (office life, family
  drama, petty revenge), so the page keeps normal comments and reach

## 5. Posting

| Item | Rule |
|---|---|
| Frequency | 1 episode a day, 7:00 PM IST, YouTube Shorts + Instagram Reels + Facebook Reels |
| Title | Emotion + event + emoji + "Ep N", under 60 characters |
| Caption | Line 1: the drama as a question ("Would you forgive Bruno?"). Line 2: "Episode N. Follow for tomorrow." 3–5 hashtags |
| AI label | Always on. Caption says "AI animation" |

## 6. Learnings

Claude updates this every Sunday from the metrics.

- (empty — first update after week 1)
