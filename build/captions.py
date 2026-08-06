"""Caption + burn-in schedule, timed to the recorded VO's word timestamps.

Every IN point is a real word onset from vo_words.json, so type lands on the
syllable rather than near it. Every OUT clears its cut by >=0.19s, per the
pack's caption spec.

TEXT BUDGET. At most two text objects on screen at once. The pack lists a
CAP1/CAP2 pair AND a burn-in number for several scenes, but stacking all
three collides and reads as clutter, so the burn-in number takes the CAP1
slot -- either replacing CAP1 (05, 06) or handing off to it (10, 11).
A07 is the exception: its number is set in ink on the white statement page,
a different colour in a different zone, so it costs nothing.

Colour system, carried from the Klarna pack:
  CREAM  #F5F0E6  body
  INK    #0A0C10  outline / diegetic print
  ACCENT #E85F42  the word that costs you something
"""

CREAM = (245, 240, 230)
INK = (10, 12, 16)
ACCENT = (232, 95, 66)
DIM = (245, 240, 230, 195)

# Per-scene scrim peak alpha. The renders run from near-black (A01) to a
# blown-out white statement page (A07); one global scrim either does nothing
# or crushes the golden hour, so it is set per shot.
SCRIM = {
    "A01": 0.40, "A02": 0.62, "A03": 0.60, "A04": 0.60, "A05": 0.70,
    "A06": 0.44, "A07": 0.82, "A08": 0.40, "A09": 0.44, "A10": 0.46,
    "A11": 0.70,
}

# kind : cap1 | cap2 | hero | num | slam | print   (drives type treatment)
# slot : cap1 | cap2 | print, or an explicit y with yanchor
EVENTS = [
    # ---- 01 THE HOOK  (cut 0.000-3.917) -------------------------------
    dict(scene="A01", kind="cap1", slot="cap1", tin=0.12, tout=3.72,
         runs=[("PAY IN FULL EVERY MONTH", CREAM)]),
    dict(scene="A01", kind="cap2", slot="cap2", tin=1.30, tout=3.72,
         runs=[("the industry has ", CREAM), ("a word", ACCENT), (" for you", CREAM)]),

    # ---- 02 THE TERM  (cut 3.917-9.542) -------------------------------
    # "Deadbeats" lands at 4.12. The pack is right that this word is the whole
    # video, so it holds the frame alone for 1.2s before CAP2 arrives.
    dict(scene="A02", kind="hero", slot="cap1", tin=4.12, tout=9.30,
         runs=[("DEADBEAT", ACCENT)]),
    dict(scene="A02", kind="cap2", slot="cap2", tin=5.34, tout=9.30,
         runs=[("that's the actual term. not an insult — ", CREAM),
               ("a category.", ACCENT)]),

    # ---- 03 THE REVOLVER  (cut 9.542-14.292) --------------------------
    dict(scene="A03", kind="cap1", slot="cap1", tin=9.94, tout=14.08,
         runs=[("THE PROFITABLE ONE\nIS A ", CREAM), ("REVOLVER", ACCENT)]),
    dict(scene="A03", kind="cap2", slot="cap2", tin=12.16, tout=14.08,
         runs=[("someone who never quite clears it", CREAM)]),

    # ---- 04 THE PRODUCT  (cut 14.292-18.083) --------------------------
    dict(scene="A04", kind="cap1", slot="cap1", tin=14.84, tout=17.88,
         runs=[("THE CARD ISN'T\nTHE PRODUCT", CREAM)]),
    dict(scene="A04", kind="cap2", slot="cap2", tin=16.68, tout=17.88,
         runs=[("the ", CREAM), ("balance", ACCENT), (" is", CREAM)]),

    # ---- 05 THE LIMIT  (cut 18.083-22.417) ----------------------------
    # the number replaces CAP1 -- it is the scene's whole argument
    dict(scene="A05", kind="num", slot="cap1", tin=18.62, tout=22.20,
         label="CREDIT LIMIT",
         runs=[("£2,000", CREAM), ("  →  ", DIM), ("£3,500", ACCENT)]),
    dict(scene="A05", kind="cap2", slot="cap2", tin=20.20, tout=22.20,
         runs=[("you didn't ask. ", CREAM), ("it arrived.", ACCENT)]),

    # ---- 06 THE REWARDS  (cut 22.417-28.375) --------------------------
    # the two-numbers-in-collision beat. Set small against huge; the size
    # difference is the argument, so it gets the heaviest type in the film.
    dict(scene="A06", kind="num", y=1016, yanchor="top", tin=24.20, tout=28.18,
         runs=[("1% BACK", CREAM)], vsize=76),
    dict(scene="A06", kind="slam", y=1148, yanchor="top", tin=25.64, tout=28.18,
         runs=[("24.9% APR", ACCENT)], vsize=168),
    dict(scene="A06", kind="cap2", slot="cap2", tin=26.90, tout=28.18,
         runs=[("the cashback is the ", CREAM), ("bait", ACCENT), (", not the gift", CREAM)]),

    # ---- 07 THE BOX  (cut 28.375-33.000) ------------------------------
    # set in ink on the white page so it reads as printed, not captioned,
    # and scaled with the shot's 10% push so it sits on the paper
    dict(scene="A07", kind="print", slot="print", tin=29.60, tout=32.80,
         label="MINIMUM PAYMENT DUE", runs=[("£25.00", INK)]),
    dict(scene="A07", kind="cap1", slot="cap1", tin=28.94, tout=32.80,
         runs=[("THE SMALLEST NUMBER\nON THE PAGE", CREAM)]),
    dict(scene="A07", kind="cap2", slot="cap2", tin=31.30, tout=32.80,
         runs=[("in its own box. ", CREAM), ("that's not an accident.", ACCENT)]),

    # ---- 08 THE RULE  (cut 33.000-37.667) -----------------------------
    dict(scene="A08", kind="cap1", slot="cap1", tin=33.28, tout=37.47,
         runs=[("RIBA", ACCENT), (" ISN'T A FEE\nYOU TRIGGER", CREAM)]),
    dict(scene="A08", kind="cap2", slot="cap2", tin=35.86, tout=37.47,
         runs=[("it's the ", CREAM), ("revenue model", ACCENT)]),

    # ---- 09 THE REAL SALE  (cut 37.667-44.000) ------------------------
    # the pack's "PROFIT: FIXED AT THE SALE" burn-in is dropped here: CAP1
    # and CAP2 already say it word for word, and three objects collided.
    dict(scene="A09", kind="cap1", slot="cap1", tin=38.12, tout=43.80,
         runs=[("A REAL SALE TAKES\nITS PROFIT ", CREAM), ("ONCE", ACCENT)]),
    dict(scene="A09", kind="cap2", slot="cap2", tin=40.68, tout=43.80,
         runs=[("at the moment of sale. ", CREAM), ("it never grows again.", CREAM)]),

    # ---- 10 TIME  (cut 44.000-48.583) ---------------------------------
    # burn-in first, then hands the slot to CAP1 -- sequential, never stacked
    dict(scene="A10", kind="num", slot="cap1", tin=44.74, tout=46.62,
         label="RIBA", runs=[("PRICED IN TIME", ACCENT)]),
    dict(scene="A10", kind="cap1", slot="cap1", tin=46.90, tout=48.38,
         runs=[("TIME IS THE INGREDIENT", CREAM)]),

    # ---- 11 THE CLOSE  (cut 48.583-58.500) ----------------------------
    # "£0.00" lands on the word "zero" at 50.32. It is the only number in the
    # film set in cream rather than terracotta -- the cost colour resolves.
    dict(scene="A11", kind="num", slot="cap1", tin=50.32, tout=51.36,
         label="BALANCE", runs=[("£0.00", CREAM)]),
    dict(scene="A11", kind="cap1", slot="cap1", tin=51.56, tout=58.30,
         runs=[("BE ", CREAM), ("WORTHLESS", ACCENT), ("\nTO THEM", CREAM)]),
    dict(scene="A11", kind="cap2", slot="cap2", tin=54.20, tout=58.30,
         runs=[("Follow — the ", CREAM), ("halal card fix", ACCENT), (" is next.", CREAM)]),
]
