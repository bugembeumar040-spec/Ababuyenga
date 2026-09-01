# FOOTBALL % DECODED — X account pivot

Plan for turning [@monedecoded](https://x.com/monedecoded) into a football
account covering the top five European leagues, using the production
pipeline this repo already runs.

---

## Two things to know before the plan

**1. I cannot touch the account.** There is no X connector in this
session — I can't change the bio, upload media, or post. Everything here
is prepared for you to execute, or for a scheduler to pick up.

**2. "Copyright-free clips of top European leagues" do not exist.**
Premier League, La Liga, Serie A, Bundesliga, Ligue 1 and UEFA footage is
owned by the leagues and their broadcasters, enforced by automated
detection, and there is no fair-dealing carve-out for reposting football
action as entertainment. Accounts built on cut match footage do grow fast
— and then get struck and suspended, usually within a season. The clips
are not the asset; the account is.

**You already solved this.** The finance pack in this repo shoots on
generated footage with a negative prompt that strips faces. That idiom
transfers to football perfectly, because it dodges *both* traps at once:
match-footage copyright **and** player image rights, which in football are
licensed assets guarded harder than the footage is.

---

## The positioning

Not another clip account. **The money behind the European game.**

Why this lane and not highlights:

- **It keeps your audience.** A hard pivot from `monedecoded` to
  highlights strands every follower you have. "Football money" is the
  same promise — decode the number — pointed at a bigger sport.
- **It is the format you already shoot.** Scene map, numbers burned in
  during the edit, the two-numbers-in-collision beat. Football finance is
  *made* of collisions: fee vs. book value, wage bill vs. revenue, net
  spend vs. gross.
- **It cannot be taken down.** Nobody issues a strike over a balance sheet.
- **It argues.** PSR, amortisation, net spend and points deductions are
  the most reliably quote-tweeted subjects in football X. Engagement in
  this lane comes from disagreement, and disagreement is free.
- **It is underserved in video.** The football-finance audience is served
  by long threads and long YouTube. Almost nobody is doing it as a tight
  9:16 with your production values.

Bio, for when you rebrand:

> Football, decoded by the numbers. Where the money in the European game
> actually goes. No highlights — the other half of the sport.

---

## The rights rule — one line

**You can say it. You cannot show it.**

Naming clubs, players, fees and figures in the voiceover and in burned-in
text is commentary. That is legal and it is the whole substance of the
account. What you must never put on screen:

| Never on screen | Why |
|---|---|
| Match or broadcast footage | League/broadcaster copyright |
| Club badges and crests | Trademarks |
| Replica kits, sponsor and manufacturer marks | Trademark + design right |
| A recognisable real player's face or likeness | Image rights, licensed |
| Identifiable stadium exteriors, competition branding | Trademark |

Everything the packs generate is deliberately anonymous: unbranded kit,
blank boots, an empty academy pitch, a ledger, floodlights, a tunnel. The
faceless negative prompt you already use does most of this work; the
football packs extend it with the badge and likeness bans.

---

## The post mix

Run four formats so the feed isn't one note:

1. **The pack** — a 55s 9:16 short, one mechanism decoded. One per week.
   This is the account's reason to exist and what gets followed.
2. **The card** — a single still, one number, one line of text. Cheap:
   pull frames from the pack's Track B, which are already generated.
   Three to four per week.
3. **The thread** — the pack's script as 6–8 posts, published on a
   different day to the video. Costs nothing, reaches the text audience,
   and is where the arguments start.
4. **The reply** — quote the week's actual football-money news with one
   sentence of decoding. This is what makes the account current instead of
   evergreen, and it's the fastest follower source. No production cost.

## The week

| Day | Slot |
|---|---|
| Mon | Card — the weekend's money story |
| Tue/Wed | Reply-decode on European nights |
| Thu | Thread — last week's pack as text |
| Fri | Card — pre-weekend |
| Sat/Sun | The pack drops; reply-decode through the matchday |

**The season matters more than the week.** This lane has three peaks:
the summer and January windows, the 31 December PSR assessment date, and
club accounts filing in spring — which is when points deductions,
amortisation rows and wage-bill stories break. Bank packs ahead of those
windows. Everything in the backlog below is timed to one of them.

---

## Packs

- `pure-profit-prompt-pack.txt` — why clubs sell academy players. Book
  value, amortisation, and the £40m that is entirely profit. **Written,
  ready to shoot.**

Backlog, in the order I'd shoot them:

- **The eight-year contract** — how contract length was used to spread a
  fee thin, and why the rule changed to a five-year cap.
- **Net spend is a magic trick** — the number fans argue with is the one
  that hides the most.
- **The wage bill is the club** — revenue-to-wage ratio as the only
  number that predicts a collapse.
- **Nobody pays £100m** — instalments, add-ons and sell-on clauses; the
  headline fee is a press release, not a payment.
- **The stadium is the strategy** — matchday revenue as the gap that
  actually separates the top five leagues.
