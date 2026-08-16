# postpublish

Audits a live YouTube video against the post-publish playbook, and executes
the parts of that playbook the API can actually perform.

The playbook itself — what top channels do after publishing, on what
timeline, and why — is in [PLAYBOOK.md](PLAYBOOK.md).

Standard library only. No dependencies, no install step.

## Setup

Three environment variables, never a file in the repo:

```sh
export YT_CLIENT_ID=...
export YT_CLIENT_SECRET=...
export YT_REFRESH_TOKEN=...
```

The refresh token needs `https://www.googleapis.com/auth/youtube` or
`.../youtube.force-ssl`. A read-only token authenticates fine and then fails
on the first write, so `apply --apply` checks the scope up front rather than
failing halfway through a run.

## Commands

```sh
python -m postpublish audit    <videoId>            # read-only score
python -m postpublish init     <videoId>            # create a pack, seeded from live
python -m postpublish validate <videoId>            # check authored copy
python -m postpublish apply    <videoId>            # DRY RUN — prints the diff
python -m postpublish apply    <videoId> --apply    # actually writes
python -m postpublish playbook                      # the manual checklist
```

### audit

Read-only, and works on **any** video, including channels you do not own.
That is also how you use it to reverse-engineer a bigger channel: point it
at their last ten uploads and read what they do consistently.

```
[PASS  ] title.length               title is 59 chars
[FAIL  ] description.chapters       no chapters. Chapters raise the odds of...
                                    -> add >=3 markers starting at 0:00
SCORE: 72.7% of automatable checks pass
```

Checks that come back `MANUAL` are not failures — they are the work the API
cannot see or do, printed every run so it stays on the list.

### packs

A pack is a plain JSON file holding every asset one video needs: title plus
A/B variants, description parts, chapters, tags, the pinned comment,
playlist targets, the community post, the Shorts derivative brief and the
cross-platform copy.

The tool does **not** write the copy. Generated titles are how every channel
in a niche ends up sounding identical. What it does is define the slots so
nothing is forgotten, and validate authored copy against every hard platform
limit before it touches a live video.

## Safety

Mutating a live video is not reversible by this tool, so:

1. **Dry run is the default.** Nothing is written without `--apply`.
2. **Validation gates the run.** A pack with any `FAIL` never reaches the
   API — a rejected write mid-run would leave the video half-updated.
3. **Every write prints before/after** so you approve a real diff.
4. **The live snippet is backed up to disk** before the first write.
5. **Snippet updates are read-modify-write.** `videos.update` deletes any
   writable field the request omits; see PLAYBOOK.md, "The one trap".

## Tests

```sh
python -m unittest discover -s . -p "test_*.py"
```

43 tests, no network. The ones that matter most are in
`tests/test_api_safety.py`, which pin the non-destructive merge, and
`tests/test_apply_flow.py`, which assert a dry run sends zero requests and
an invalid pack sends zero requests even with `--apply`.
