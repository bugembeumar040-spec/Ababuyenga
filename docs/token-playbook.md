# Token playbook

Where this account's tokens actually go, and what changes it. Measured from the 21
completed sessions on this repo, 5–10 Aug 2026.

---

## The measurement

| | tokens | share |
|---|---|---|
| **Cache read** | 111,795,987 | **95.0%** |
| Cache write | 4,512,314 | 3.8% |
| Input | 351,289 | 0.3% |
| Output | 1,030,677 | 0.9% |
| **Total** | **117,690,267** | |

Three sessions on 8 Aug died on *"You've hit your session limit."* That is what this
document exists to prevent.

**Ninety-five percent of consumption is cache read** — re-reading context that was
already established, once per turn, for the life of the session. Only 0.9% is text
actually written. The account bills **108 cache-read tokens for every token of
output**, and in the worst session, 271.

The distribution is not even. The top 5 sessions are **74%** of all consumption:

| Session | cache read | ×its own output |
|---|---|---|
| Video character visual audit | 34,108,319 | 271× |
| Video consolidation and script enhancement | 17,234,459 | 135× |
| YouTube short from Higgsfield clips | 14,238,495 | 105× |
| Video generation with VO and images | 10,208,613 | 131× |
| Minimal tokens, quality output | 6,853,083 | 118× |

Median session: 2,571,662. The worst is **13× the median**, and it produced no more
work than several 500k sessions did.

---

## What that means

Cost is driven by **conversation length**, not by how much gets written. Every turn
re-bills the whole transcript, so a session's price grows roughly with the *square*
of its turn count. A 60-turn session is not twice a 30-turn session — it is nearer
four times.

Everything below follows from that one fact.

---

## The levers, in order of size

### 1. One deliverable per session

By far the largest. The 34M-token session drifted from a character audit into title,
description, hashtags and a pinned comment — every one of those later turns re-read
every image and every transcript from the audit that preceded it.

Finish the thing asked for, then start a new session for the next thing. A fresh
session re-reads a small `CLAUDE.md` instead of a 200-turn history.

### 2. Keep media out of long sessions

Four of the five worst sessions are media-heavy — video review, generated clips,
voiceover, stills. Image and video tool results are large and, once in the
transcript, **are re-read on every subsequent turn for the rest of the session.**

So: review media in a session that does nothing else, and end it when the review
ends. Never review 11 clips and then start writing packaging in the same session.

### 3. Answer the blocking question in the first message

Eight of 21 sessions ended blocked, waiting on something only the user had —
API credentials, a token budget, a rough timestamp, "what does laundry room
enhancement mean". Each one paid for a full context load to arrive at a question.

Front-load it. If a session needs an API key, a file, or a decision between two
readings of the request, say so in the opening message.

### 4. Read slices, not whole files

`credit-card-prompt-pack.txt` is 578 lines / ~9.5k tokens. Loading it to check one
caption pays 9.5k, and then pays it again on every turn after that.

- Reusable facts — house style, palette, characters, caption spec, VO settings,
  packaging — now live in `docs/canon.md` at under a fifth the size. Read that.
- For the pack itself, grep the `====` section header and read that range.

### 5. Match effort to the task

15 of 21 sessions ran at `ultracode` or `xhigh`. Writing captions, drafting a
description, or adding emotion tags to an existing script does not need maximum
reasoning; extended thinking is billed output and it compounds into every later
turn's cache read. Reserve the high settings for the analysis and audit work that
earns it.

### 6. Cut permission round-trips

`.claude/settings.json` in this repo pre-approves the read-only commands these
sessions actually use — `git status`, `git log`, `git diff`, `wc`, `ls`. Each avoided
prompt is one less turn, and every turn is a full re-read.

---

## Quick check

Session usage is visible per session in the sessions list. Two numbers worth
watching:

- **cache read ÷ output.** Under ~50× is healthy for this repo's work. Past 100×,
  the session has become mostly re-reading, and the work would be cheaper restarted.
- **cache read above ~5M.** Time to finish the current deliverable and open a new
  session rather than continuing.
