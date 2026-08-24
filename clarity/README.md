# Clarity in the Quran — VO alignment

Working area for aligning the ElevenLabs v3 voiceover batches against
`script/clarity-voiceover-script-v3-tagged.txt` (28 batches, 43:18 target).

    vo/               accepted takes, one file per batch, in sequence
    master/           assembled master track + edl.json (built last)
    vo/rejected/      takes not used, kept for reference
    transcripts/      word-timestamped ASR of each take
    tools/            transcribe.py · audit.py · ledger.py
    ALIGNMENT.md      generated ledger — regenerate with tools/ledger.py

Workflow per batch drop:

    python3 clarity/tools/transcribe.py clarity/vo/batch-NN.mp3
    python3 clarity/tools/audit.py NN
    python3 clarity/tools/ledger.py

`audit.py` folds number-words to digits (including year forms -- "nineteen
twenty-four" is 1924, not 43) before diffing, so a match score
below 100% is usually ASR spelling of transliterated Arabic (mushaf/musaf,
Iqra/Ikra), not a fault in the recording. Read the printed diff lines before
treating a score as a defect.

Status is in `ALIGNMENT.md`; the two batches that diverge from the script are
written up in `DIVERGENCES.md`.
