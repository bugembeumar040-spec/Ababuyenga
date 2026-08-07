# beats.py — scene map + caption cues for the SALAAM short
# Timings derived from word-level STT alignment of the delivered VO (86.67s).
# Text is the WRITTEN script, never the STT transliteration.

W, H, FPS = 1080, 1920, 30
XF = 0.45          # crossfade length between scenes
TOTAL = 88.20      # final runtime

# (scene, in, out, image, move)
# move: pin = push in, pout = pull out, pl/pr = push + drift left/right,
#       pu/pd = push + drift up/down
SCENES = [
    ( 1,  0.00,  4.85, "s01", "pin"),
    ( 2,  4.85,  7.62, "s02", "pu"),
    ( 3,  7.62, 11.35, "s03", "pout"),
    ( 4, 11.35, 14.80, "s04", "pin"),
    ( 5, 14.80, 18.45, "s05", "pl"),
    ( 6, 18.45, 22.75, "s06", "pout"),
    ( 7, 22.75, 26.05, "s07", "pr"),
    ( 8, 26.05, 30.25, "s08", "pin"),
    ( 9, 30.25, 34.65, "s09", "pd"),
    (10, 34.65, 38.45, "s10", "pin"),
    (11, 38.45, 42.70, "s11", "pout"),
    (12, 42.70, 47.45, "s12", "pin"),
    (13, 47.45, 50.25, "s13", "pout"),
    (14, 50.25, 55.15, "s14", "pl"),
    (15, 55.15, 59.55, "s15", "pin"),
    (16, 59.55, 66.00, "s16", "pin"),
    (17, 66.00, 70.05, "s17", "pout"),
    (18, 70.05, 76.45, "s18", "pr"),
    (19, 76.45, 80.05, "s19", "pin"),
    (20, 80.05, 82.60, "s20", "pout"),
    (21, 82.60, 85.05, "s21", "pin"),
    (22, 85.05, 88.20, "s22", "pout"),
]

# kind: "hook" big white | "en" narration | "scripture" cream quote
#       "ar" Arabic gold | "ref" small gold citation
CUES = [
    ( 0.00,  1.85, "hook",      "TWO WORDS."),
    ( 1.92,  3.18, "en",        "You say them\nevery day"),
    ( 3.22,  4.62, "en",        "without thinking."),
    ( 5.44,  7.34, "ar_small",  "السَّلَامُ عَلَيْكُمْ"),
    ( 7.20,  8.64, "en",        "But do you know"),
    ( 8.68, 11.05, "en",        "WHO says them\nto you first?"),
    (11.52, 13.16, "en",        "Allah describes\nthe believers"),
    (13.20, 14.66, "en",        "on the Day\nthey meet Him:"),
    (14.82, 18.30, "ar",        "تَحِيَّتُهُمْ يَوْمَ يَلْقَوْنَهُ سَلَامٌ"),
    (18.78, 21.40, "scripture", "“Their greeting,\nthe Day they meet Him —"),
    (21.44, 22.92, "scripture", "is Peace.”"),
    (22.98, 25.62, "ref",       "AL-AHZAB · 44"),
    (26.20, 28.00, "en",        "This isn’t a habit."),
    (28.04, 30.14, "hook",      "IT’S THE LANGUAGE\nOF PARADISE."),
    (30.36, 32.44, "en",        "And the Prophet ﷺ"),
    (32.50, 34.52, "en",        "told us what to do\nwith it HERE."),
    (34.98, 36.48, "scripture", "“You will not\nenter Paradise"),
    (36.52, 38.32, "scripture", "until you believe."),
    (38.56, 40.52, "scripture", "And you will\nnot believe"),
    (40.56, 42.52, "scripture", "until you love\none another.”"),
    (42.82, 44.42, "en",        "Then he said —"),
    (44.54, 46.10, "en",        "shall I show you\nwhat will"),
    (46.14, 47.62, "en",        "make you love\neach other?"),
    (47.88, 50.32, "ar",        "أَفْشُوا السَّلَامَ بَيْنَكُمْ"),
    (50.36, 52.94, "scripture", "“Spread the salaam\nbetween you.”"),
    (53.56, 55.06, "ref",       "SAHIH MUSLIM"),
    (55.26, 57.32, "en",        "And when it\ncomes to you —"),
    (57.50, 59.42, "hook",      "IT IS NOT\nOPTIONAL."),
    (59.78, 65.98, "ar",        "وَإِذَا حُيِّيتُم بِتَحِيَّةٍ\nفَحَيُّوا بِأَحْسَنَ مِنْهَا\nأَوْ رُدُّوهَا"),
    (66.10, 68.10, "scripture", "“When you are\ngreeted —"),
    (68.14, 70.12, "scripture", "answer with\nbetter than it."),
    (70.20, 72.06, "scripture", "Or at the\nvery least,"),
    (72.08, 73.72, "scripture", "return it.”"),
    (73.84, 75.92, "ref",       "AN-NISA · 86"),
    (76.80, 79.32, "en",        "They asked him\nwhich Islam is best."),
    (79.98, 82.56, "en",        "He said:\nFEED PEOPLE —"),
    (82.68, 85.02, "en",        "and give salaam\nto the one you know…"),
    (85.04, 88.05, "hook",      "…AND THE ONE\nYOU DON’T."),
]
