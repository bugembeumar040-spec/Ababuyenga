# The post-publish playbook

What good channels actually do to a video *after* it is live, why each step
exists, and which ones a machine can do for you.

Publishing is the middle of the process, not the end. The first 24–72 hours
are when YouTube collects the data that decides how far the video travels,
and almost every lever that moves that data is pulled after the upload
button.

---

## The window

The system measures a new video's click-through rate, average view duration
and early satisfaction signals against what it *expected* from your channel,
and scales impressions from there. Beat the expectation early and
distribution compounds; miss it and the video settles. This is why the work
below is time-boxed rather than "whenever you get to it".

Benchmarks worth holding yourself to: CTR in the 4–10% band depending on
niche and channel size, and a decision point at 48 hours — sitting under
about 3% CTR is the signal to change the title or the thumbnail rather than
wait it out.

The nuance that matters: CTR and retention are judged **together**. A title
that wins the click and loses the viewer is worse than a duller title that
keeps them, because the satisfaction signal is what the ranking actually
optimises. Do not treat a CTR fix as free.

---

## T+0 to T+60 minutes

| Step | Why it exists |
|---|---|
| **Pin a comment** | The highest-leverage free space on the watch page. It sets the discussion topic instead of letting the top comment set it for you. |
| **Community post** | Pushes the video to already-subscribed, already-engaged people, which is the cheapest early traffic there is. |
| **Reply to every comment** | Early replies pull commenters back for a second session and seed the thread before it sets. |
| **Verify the end screen and cards** | These are the only on-platform mechanism that converts one view into the next one. |
| **Add to a playlist** | Session length, not single-video watch time, is what the system rewards. A playlist is the mechanism. |

## T+1 to T+24 hours

| Step | Why it exists |
|---|---|
| **Publish a Shorts derivative** | A 20–40s cut from the strongest segment, pointing at the long-form. Reaches a different surface with the same asset. |
| **Syndicate off-platform** | External traffic is uncorrelated with the browse signal, so it adds to distribution rather than cannibalising it. |
| **Heart 3–5 real comments** | Hearting notifies the commenter. It is the cheapest re-engagement action available. |
| **Watch the retention graph** | The first dip tells you where the edit failed. That is next video's lesson, and sometimes this video's re-cut. |

## T+24 to T+72 hours

| Step | Why it exists |
|---|---|
| **Judge CTR against your own average** | Your channel's baseline is the only meaningful comparison; niche averages are noise. |
| **Start a Test & Compare run** | YouTube's native A/B test optimises for watch time, not just clicks. Requires YPP. **Not available for Shorts, Premieres or scheduled live.** |
| **Rewrite the title if retention is fine but CTR is not** | Good retention plus bad CTR is a packaging problem, and packaging is the cheap thing to change. |
| **Leave it alone if both are fine** | Churning metadata on a working video resets its learning for no reason. |

---

## What a machine can and cannot do

This is the part most "YouTube automation" writing gets wrong, so it is
stated precisely. Verified against the YouTube Data API v3 reference.

### Automatable — the tool in this directory does these

| Action | Method | Quota |
|---|---|---|
| Rewrite title / description / tags | `videos.update` | 50 |
| Set a custom thumbnail | `thumbnails.set` | 50 |
| Post a top-level comment | `commentThreads.insert` | 50 |
| Add to a playlist | `playlistItems.insert` | 50 |
| Upload captions | `captions.insert` | 400 |
| Read everything for the audit | `videos.list`, etc. | 1–50 |

Default daily quota is 10,000 units, so a full pass over one video costs
roughly 2% of a day's budget. Auditing is cheap; writing is not.

### Not automatable — no API surface exists

- **Pinning a comment.** `commentThreads.insert` posts it; nothing pins it.
  This is the single most common false claim in automation guides.
- **Hearting a comment.**
- **End screens and cards.** Studio only.
- **Community posts.** No public API.
- **Test & Compare A/B tests.** No public API.
- **Retention graphs.** A different API (Analytics), and not per-moment.

A tool that hides this tier teaches you a checklist with holes in it, so
`postpublish` prints these every run as unchecked boxes.

---

## The one trap that will cost you a live video

`videos.update` **replaces** the entire `snippet` part. Any writable field
your request omits is deleted from the live video. Send `{"title": "..."}`
on its own and you have just wiped the description, the tags and the
category of a video that was working.

The only safe form is read-modify-write: fetch the current snippet, apply
your delta, send the merged object back. `api.update_video_snippet()` does
this and `tests/test_api_safety.py` pins the behaviour, because this is the
kind of bug you only find in production.

---

## Sources

- [YouTube Data API — videos.update](https://developers.google.com/youtube/v3/docs/videos/update) (the destructive-overwrite warning)
- [YouTube Data API — commentThreads.insert](https://developers.google.com/youtube/v3/docs/commentThreads/insert)
- [YouTube Data API — thumbnails.set](https://developers.google.com/youtube/v3/docs/thumbnails/set)
- [YouTube Help — A/B test titles and thumbnails](https://support.google.com/youtube/answer/16391400?hl=en-GB)
- [YouTube ends 2-year wait for Shorts thumbnails but blocks A/B testing](https://ppc.land/youtube-ends-2-year-wait-for-shorts-thumbnails-but-blocks-a-b-testing/)
- [How the YouTube Algorithm Actually Works in 2026: Retention, Satisfaction, and the Metrics That Matter](https://johnisaacson.co.uk/how-youtube-algorithm-works-2026/)
- [vidIQ — How the YouTube Algorithm Works in 2026](https://vidiq.com/blog/post/understanding-youtube-algorithm/)
- [The first 48 hours after upload](https://youseo.app/blogs/the-first-48-hours-after-upload-decide-everything-heres-exactly-what-to-do)
- [How to A/B Test YouTube Thumbnails: YouTube Studio's Native Tool (2026)](https://1of10.com/blog/how-to-ab-test-youtube-thumbnails/)
