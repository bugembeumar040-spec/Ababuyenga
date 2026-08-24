# CLARITY IN THE QURAN — VO ALIGNMENT LEDGER

Batches delivered: **25 / 28**  ·  script total target: **43:18**

> **Missing: batches 17, 18, 19.** The running clock restarts from the script's own IN point after a gap, so drift below is measured within each contiguous run, not across the hole.

| # | dur | actual IN–OUT | script IN–OUT | drift | artic w/s | script match |
|---|-----|---------------|---------------|-------|-----------|--------------|
| 01 | 65.15s | 0:00.00–1:05.15 | 0:00.00–1:06.00 | -0.85s | 2.75 | 93% |
| 02 | 76.43s | 1:05.15–2:21.58 | 1:06.00–2:27.00 | -5.42s | 2.80 | 100% |
| 03 | 90.91s | 2:21.58–3:52.49 | 2:27.00–3:51.00 | +1.49s | 2.81 | 98% |
| 04 | 73.40s | 3:52.49–5:05.89 | 3:51.00–5:05.00 | +0.89s | 2.68 | 98% |
| 05 | 66.77s | 5:05.89–6:12.66 | 5:05.00–6:16.00 | -3.34s | 2.94 | 96% |
| 06 | 89.00s | 6:12.66–7:41.66 | 6:16.00–7:45.00 | -3.34s | 2.68 | 94% |
| 07 | 105.33s | 7:41.66–9:26.99 | 7:45.00–9:15.00 | +11.99s | 2.41 | 96% |
| 08 | 86.67s | 9:26.99–10:53.66 | 9:15.00–11:03.00 | -9.34s | 2.89 | 98% |
| 09 | 91.72s | 10:53.66–12:25.38 | 11:03.00–12:30.00 | -4.62s | 2.70 | 95% |
| 10 | 104.52s | 12:25.38–14:09.89 | 12:30.00–14:22.00 | -12.11s | 2.74 | 99% |
| 11 | 83.49s | 14:09.89–15:33.38 | 14:22.00–16:00.00 | -26.62s | 2.89 | 80% |
| 12 | 103.55s | 15:33.38–17:16.93 | 16:00.00–17:43.00 | -26.07s | 2.74 | 97% |
| 13 | 104.05s | 17:16.93–19:00.98 | 17:43.00–19:20.00 | -19.02s | 2.69 | 98% |
| 14 | 66.27s | 19:00.98–20:07.25 | 19:20.00–20:33.00 | -25.75s | 3.13 | 96% |
| 15 | 101.88s | 20:07.25–21:49.13 | 20:33.00–22:16.00 | -26.87s | 2.67 | 77% |
| 16 | 113.40s | 21:49.13–23:42.52 | 22:16.00–24:31.00 | -48.48s | 3.04 | 99% |
| **17** | — | **NOT DELIVERED** | 24:31.00–26:11.00 | — | — | — |
| **18** | — | **NOT DELIVERED** | 26:11.00–28:05.00 | — | — | — |
| **19** | — | **NOT DELIVERED** | 28:05.00–29:52.00 | — | — | — |
| 20 | 81.79s | 29:52.00–31:13.79 | 29:52.00–31:21.00 | -7.21s | 2.99 | 98% |
| 21 | 84.04s | 31:13.79–32:37.83 | 31:21.00–32:52.00 | -14.17s | 3.00 | 97% |
| 22 | 90.04s | 32:37.83–34:07.87 | 32:52.00–34:22.00 | -14.13s | 2.80 | 98% |
| 23 | 87.25s | 34:07.87–35:35.12 | 34:22.00–35:54.00 | -18.88s | 2.67 | 96% |
| 24 | 82.36s | 35:35.12–36:57.48 | 35:54.00–37:38.00 | -40.52s | 2.94 | 99% |
| 25 | 61.73s | 36:57.48–37:59.21 | 37:38.00–38:41.00 | -41.79s | 2.82 | 98% |
| 26 | 101.64s | 37:59.21–39:40.85 | 38:41.00–40:20.00 | -39.15s | 2.83 | 98% |
| 27 | 100.36s | 39:40.85–41:21.21 | 40:20.00–41:58.00 | -36.79s | 2.86 | 96% |
| 28 | 74.92s | 41:21.21–42:36.13 | 41:58.00–43:18.00 | -41.87s | 2.75 | 99% |

**Voice consistency.** Articulation median 2.80 w/s, range 2.41–3.13, across 25 batches (pauses excluded, so this measures delivery speed, not phrasing). The session trend is +0.12 w/s from b01 to b28 — essentially flat, which is the drift the script pack warns about and it is not present. Outliers sit either side of the median rather than at the end of the session: faster [14] and slower [7].

**Runtime.** 25 delivered batches total 36:26.66 of speech. The recording runs consistently shorter than the script's ~150wpm estimates, so the finished master will land under the 43:18 target.

**Audio tags spoken aloud:** none.

**Script divergence.** Scores below ~95% are usually the transcriber's spelling of transliterated Arabic (mushaf/musaf, Iqra/Ikra, Nöldeke/Noldikas) rather than a fault in the recording — read the diff lines from `audit.py` before treating a score as a defect.

- **b11 at 80% carries real rewording**, not transcription noise.
- **b15 at 77% carries real rewording**, not transcription noise.
