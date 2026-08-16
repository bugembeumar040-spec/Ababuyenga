# What is verified, what is inferred

Written for the `packs/sbFXFoL1-5A/` pack. The distinction matters because
the copy in that pack is about to go on a live video, and some of it rests
on firmer ground than the rest.

## Verified

| Fact | Source |
|---|---|
| Video ID `sbFXFoL1-5A` | given |
| Title: "The Jinn Couldn't See a Dead King. So How Did He See Yours?" | YouTube public oembed endpoint |
| Channel: Clarity in the Quran | YouTube public oembed endpoint |
| Channel ID `UC0eBu0ZXcF20pTAG3lUnPXA` | watch page payload |

## NOT verified — could not be read

The live video's description, tags, duration, view count, retention, whether
it is a Short or long-form, and its transcript are all **unknown**. Three
independent routes failed:

1. **vidIQ MCP tools** — account out of credits (`vidiq_get_videos_by_ids`
   and every other 5-credit call).
2. **Direct scraping** — YouTube served its bot interstitial to both `curl`
   and the fetch tool; the watch page redirected to a `/sorry/` challenge.
3. **YouTube Data API** — the `YT_REFRESH_TOKEN` in the environment is dead.
   A refresh returns `invalid_grant: Token has been expired or revoked`.

## Consequences for the pack

- **Chapters are empty, deliberately.** Chapters need the real runtime and
  segment boundaries. Inventing timestamps would push a description whose
  markers do not match the video — and if the last marker lands past the
  runtime, the chapters silently fail to render. The validator enforces this
  against the real duration once the API can read it.
- **Playlists are empty.** Requires the channel's real playlist IDs.
- **The description body describes content I have not watched.** It is
  derived from the title's argument, which is Qur'an 34:14 in Surah Saba' —
  Sulayman's death going unnoticed by the jinn until a creature of the earth
  consumed his staff, and the verse's own conclusion that they did not know
  the unseen. That reading is standard and the title states it plainly, but
  the four bullet points listing "what the video covers" are an inference
  about structure, not a transcript. **Check them against the actual video
  before applying.**

## To close the gap

Re-mint the refresh token, then:

```sh
python -m postpublish init sbFXFoL1-5A --force   # seed from the live video
python -m postpublish audit sbFXFoL1-5A          # score what is actually there
python -m postpublish validate sbFXFoL1-5A       # re-check against real runtime
python -m postpublish apply sbFXFoL1-5A          # dry run, read the diff
```

`init --force` overwrites the pack with live values, so copy the authored
description body out first if you want to keep it.
