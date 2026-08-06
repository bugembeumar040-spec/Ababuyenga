"""Edit decision list for 'They Call You a Deadbeat'.

Timeline derived from the RECORDED VO (57.81s), not the prompt pack's
~150wpm estimates -- the recorded read is tighter and drops two scripted
lines, so the pack's map does not survive contact with it.

Cut points sit in the gap between utterances so picture leads sound by
~0.25s and the shot is established by the time the voice arrives.
Everything is held in FRAMES at 24fps so nothing drifts against the VO.

Source in-points are chosen for where the ACTION is in each generated
clip, not from 0 -- A01's hand only enters at 3.4s, and A05 has to end
before AMIR's beanie drifts white at ~4.5s.
"""

FPS = 24
W, H = 1080, 1920

# cut points in seconds, taken from the VO gaps, then quantised to frames
CUTS_S = [0.000, 3.900, 9.550, 14.300, 18.100, 22.400,
          28.380, 33.020, 37.680, 44.020, 48.600, 58.500]
CUTS_F = [round(t * FPS) for t in CUTS_S]          # 0,94,229,...,1404
TOTAL_F = CUTS_F[-1]
TOTAL = TOTAL_F / FPS

# name, source in-point (s), note
SHOTS = [
    ("A01", 3.30, "hook — hand enters 3.4, slides the card, withdraws"),
    ("A02", 1.20, "the term — left card nudged proud of the right"),
    ("A03", 0.20, "the revolver — clerk slides one card forward"),
    ("A04", 1.15, "the product — card rotating into the key light"),
    ("A05", 0.00, "the limit — AMIR + phone, out before the head drifts white"),
    ("A06", 0.00, "the rewards — scale tips and settles; tail freezes"),
    ("A07", 2.20, "the box — fingertip taps the empty ruled box"),
    ("A08", 0.10, "the rule — brass stamp presses once"),
    ("A09", 0.40, "the real sale — bar set down, then nothing grows"),
    ("A10", 0.20, "time — sand running, slow push"),
    ("A11", 0.08, "the close — AMIR walks out and settles"),
]

UPSCALE = {"A01", "A02", "A05", "A07", "A09", "A11"}   # generated at 720x1280

SRC_LEN = {
    "A01": 10.041667, "A02": 10.041667, "A03": 5.041667, "A04": 5.041667,
    "A05": 10.041667, "A06": 5.041667, "A07": 10.041667, "A08": 5.041667,
    "A09": 10.041667, "A10": 5.041667, "A11": 10.041667,
}


def scenes():
    for i, (name, sin, note) in enumerate(SHOTS):
        f_in, f_out = CUTS_F[i], CUTS_F[i + 1]
        need = f_out - f_in
        avail = int((SRC_LEN[name] - sin) * FPS)      # whole frames available
        live = min(need, avail)
        yield dict(idx=i + 1, name=name, note=note, src_in=sin,
                   f_in=f_in, f_out=f_out, frames=need,
                   live=live, freeze=need - live,
                   tin=f_in / FPS, tout=f_out / FPS, length=need / FPS)


if __name__ == "__main__":
    print(f"{'#':4} {'IN':>7} {'OUT':>7} {'LEN':>6} {'FRM':>4} {'SRC':>5} "
          f"{'AVAIL':>5} {'FRZ':>4}  NOTE")
    for s in scenes():
        flag = "" if not s["freeze"] else "  <-- freeze-extend"
        print(f"{s['name']:4} {s['tin']:7.3f} {s['tout']:7.3f} {s['length']:6.3f} "
              f"{s['frames']:4d} {s['src_in']:5.2f} "
              f"{int((SRC_LEN[s['name']]-s['src_in'])*FPS):5d} {s['freeze']:4d}  "
              f"{s['note']}{flag}")
    print(f"\nTOTAL {TOTAL_F} frames = {TOTAL:.3f}s @ {FPS}fps")
