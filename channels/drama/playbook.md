# Drama page playbook

The rulebook Claude follows every morning for the Drama page. Claude may edit
"Learnings" at the bottom and the episode log in `story.md`. Everything else
changes only when Prashant agrees.

## 1. What the page is

An animated soap opera told by animals, in the format behind the biggest viral
AI pet dramas: an underdog is humiliated, rises through hard work and kindness,
and gets a satisfying payback. Every video is one episode, so people follow
Mochi and come back tomorrow.

Cast (see `cast.json`): **Mochi**, a poor ginger street cat (hero);
**Duchess**, a rich white Persian (villain); **Rocco**, her bulldog bodyguard
boyfriend; **Bruno**, Mochi's loyal goofy street-dog friend; **Granny**, who
runs a tiny failing bakery and believes in Mochi.

- Fully animated: every shot is a 5-second AI clip of the cast acting
- The cast always looks the same (made from their reference pictures in `cast/`)
- A deep trailer-style narrator plus acted character voices, big word-by-word captions
- 25 to 30 seconds, 5–6 shots, vertical 9:16 (short keeps it rewatchable and keeps animation costs down)
- Title format: "She poured milk on her only fish 😿 | Ep 1"

## 2. What makes an episode spread

| Ingredient | Rule |
|---|---|
| Cold open | Shot 1 is the most emotional moment: the humiliation, the slap of a paw, the stare. No setup first |
| Clear sides | Within 3 seconds the viewer knows who to root for and who to hate |
| Stakes | Something Mochi needs is at risk: food, home, her bakery, Bruno, her dignity |
| Big faces | Every shot shows one clear emotion: tears, smugness, shock, quiet resolve |
| Short lines | Characters speak 2–8 words. Villains get the quotable lines ("Know your place.") |
| Payoff | Most episodes end on a small win or a twist, so the viewer gets a hit of satisfaction |
| Cliffhanger | The last line sets up tomorrow ("But Duchess wasn't finished.") |
| Recap-free | One narrator line at the start tells a new viewer all they need |
| Kind hero | Mochi never wins by cruelty. Payback is clever, public and fair |

Follow the arc outline in `story.md`. About 1 in 5 episodes can be a standalone
side story (Bruno's terrible plan, Rocco's secret soft side) to keep it fresh.

## 3. The daily pitch (6:40 AM IST)

Claude reads `story.md` (what happened so far, open threads) and checks trends:
holidays and festivals in the next 3 days worldwide, viral pet moments, food
trends, big sport moments a cat could react to. Then it pitches 3 directions for
today's episode, for example:

- Continue the arc ("Duchess sends Rocco to inspect the bakery")
- Trend tie-in ("Diwali: Duchess bans street cats from the festival lights")
- Side story ("Bruno tries to make Mochi a birthday cake")

Same 25-point score as the Curious page, but "Curiosity" means "Do I need to
know what happens next?".

## 4. Script rules

- 5–6 scenes, each 4–6 seconds of speech (about 8–14 words), one clip each
- 40–60 spoken words in total (the acted voice is slower, so this lands at 25–30 s)
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
